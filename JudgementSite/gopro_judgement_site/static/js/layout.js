let dropdownTimer;
const dropdown = document.querySelector('.dropdown-content');

function toggleMenu() {
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileOverlay');
    menu.classList.toggle('show');
    overlay.classList.toggle('show');
}

function showDropdown() {
    clearTimeout(dropdownTimer);
    dropdown.classList.add('show');
}

function hideDropdown() {
    dropdownTimer = setTimeout(() => {
        dropdown.classList.remove('show');
    }, 300); // 0.3초 대기
}

// 마우스 오버 시 드롭다운 표시
document.querySelector('.navbar-item.dropdown').addEventListener('mouseover', showDropdown);

// 마우스 아웃 시 드롭다운 숨기기
document.querySelector('.navbar-item.dropdown').addEventListener('mouseout', hideDropdown);
