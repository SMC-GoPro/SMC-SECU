/**
 * Common JavaScript functions for the entire site
 */

// Helper function to initialize UI components
function initializeUI() {
    // Initialize comment reply functionality
    const replyButtons = document.querySelectorAll('.comment-reply-btn');
    if (replyButtons.length > 0) {
        replyButtons.forEach(function(button) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const commentId = button.getAttribute('data-parent-id');
                const form = document.getElementById('reply-form-' + commentId);
                
                // Close all other open forms
                document.querySelectorAll('.reply-form-container').forEach(function(openForm) {
                    if (openForm.id !== 'reply-form-' + commentId) {
                        openForm.style.display = 'none';
                    }
                });
                
                // Toggle current form
                if (form.style.display === 'none') {
                    form.style.display = 'block';
                    const textarea = form.querySelector('textarea');
                    if (textarea) textarea.focus();
                } else {
                    form.style.display = 'none';
                }
            });
        });
    }

    // Initialize cancel reply buttons
    const cancelButtons = document.querySelectorAll('.cancel-reply');
    if (cancelButtons.length > 0) {
        cancelButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                const container = this.closest('.reply-form-container');
                container.style.display = 'none';
            });
        });
    }

    // Initialize delete confirmation dialogs
    const deleteForms = document.querySelectorAll('.delete-form');
    if (deleteForms.length > 0 && typeof Swal !== 'undefined') {
        deleteForms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                Swal.fire({
                    title: '정말 삭제하시겠습니까?',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonText: '삭제',
                    cancelButtonText: '취소'
                }).then((result) => {
                    if (result.isConfirmed) {
                        form.submit();
                    }
                });
            });
        });
    }

    // Initialize problem difficulty filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length > 0) {
        filterButtons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                window.location.href = btn.getAttribute('data-url');
            });
        });
    }
    
    // Setup CSRF protection for all AJAX requests
    setupCSRFProtection();
}

// Function to setup CSRF protection for all AJAX requests
function setupCSRFProtection() {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (!csrfToken) return;

    // Override fetch API
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Only add for non-GET requests
        if (options.method && options.method.toLowerCase() !== 'get') {
            if (!options.headers) {
                options.headers = {};
            }
            options.headers['X-CSRFToken'] = csrfToken;
        }
        return originalFetch(url, options);
    };
    
    // For XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        const result = originalOpen.apply(this, arguments);
        if (method.toLowerCase() !== 'get') {
            this.setRequestHeader('X-CSRFToken', csrfToken);
        }
        return result;
    };
    
    // jQuery AJAX if available
    if (window.jQuery) {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });
    }
}

// Run initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeUI();
}); 