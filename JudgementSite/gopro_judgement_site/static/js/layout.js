// 폰트 및 레이아웃 안정성 관리
(function() {
    // 폰트 일관성 유지 함수
    function fixFontStyles() {
        // Navbar, 버튼 등 주요 요소에 폰트 스타일 강제 적용
        document.querySelectorAll('.navbar, .navbar-menu, .navbar-item, .navbar-link, .auth-buttons, .auth-btn').forEach(el => {
            el.style.fontFamily = 'var(--main-font)';
        });
    }

    // 페이지 전환 스타일 적용
    document.body.classList.add('page-ready');

    // 폰트 로딩 완료 감지
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(() => {
            document.documentElement.classList.remove('fonts-loading');
            document.documentElement.classList.add('fonts-loaded');
            fixFontStyles(); // 폰트 로딩 완료 시 스타일 적용
        }).catch(() => {
            // 폰트 로딩 실패 시 기본 폰트 사용
            document.documentElement.classList.remove('fonts-loading');
            fixFontStyles(); // 폰트 로딩 실패 시에도 스타일 적용
        });
    }

    // 레이아웃 크기 초기화 함수
    function initializeLayoutSizes() {
        const navbar = document.querySelector('.navbar');
        const navbarMenu = document.querySelector('.navbar-menu');
        const authButtons = document.querySelector('.auth-buttons');
        
        // 세션 스토리지에서 크기 불러오기
        const savedNavbarWidth = sessionStorage.getItem('navbarWidth');
        const savedMenuWidth = sessionStorage.getItem('menuWidth');
        const savedAuthWidth = sessionStorage.getItem('authWidth');
        
        // 현재 크기 측정
        const currentNavbarWidth = navbar?.offsetWidth || 0;
        const currentMenuWidth = navbarMenu?.offsetWidth || 0;
        const currentAuthWidth = authButtons?.offsetWidth || 0;
        
        // 저장된 크기가 있으면 적용, 없으면 현재 크기를 저장
        if (navbar) {
            navbar.style.width = '100%';
        }
        
        if (navbarMenu) {
            if (savedMenuWidth && parseInt(savedMenuWidth) > 300) {
                navbarMenu.style.minWidth = `${savedMenuWidth}px`;
            } else if (currentMenuWidth > 300) {
                sessionStorage.setItem('menuWidth', currentMenuWidth);
                navbarMenu.style.minWidth = `${currentMenuWidth}px`;
            } else {
                navbarMenu.style.minWidth = '500px';
                sessionStorage.setItem('menuWidth', 500);
            }
        }
        
        if (authButtons) {
            if (savedAuthWidth && parseInt(savedAuthWidth) > 200) {
                authButtons.style.minWidth = `${savedAuthWidth}px`;
            } else if (currentAuthWidth > 200) {
                sessionStorage.setItem('authWidth', currentAuthWidth);
                authButtons.style.minWidth = `${currentAuthWidth}px`;
            } else {
                authButtons.style.minWidth = '240px';
                sessionStorage.setItem('authWidth', 240);
            }
        }

        // 폰트 스타일 재적용
        fixFontStyles();
    }

    // 모든 폰트 리소스 사전 로드 - 제거 (CDN에서 직접 로드)
    function preloadFonts() {
        // 이제 CDN에서 직접 로드하므로 이 함수는 더 이상 필요하지 않습니다.
        // 단, 호환성을 위해 빈 함수로 유지
    }

    // 페이지 이동 시 레이아웃 안정성 유지
    function setupLayoutStability() {
        // 초기 페이지 로드 시 초기화
        initializeLayoutSizes();
        
        // 창 크기 조정 시 재계산
        window.addEventListener('resize', function() {
            requestAnimationFrame(initializeLayoutSizes);
        });
        
        // 링크 클릭 시 레이아웃 상태 저장 및 페이지 전환 스타일 적용
        document.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function(e) {
                // 현재 페이지 링크나 외부 링크 제외
                if (this.getAttribute('href')?.startsWith('#') || 
                    this.getAttribute('target') === '_blank' ||
                    this.getAttribute('href')?.startsWith('http')) {
                    return;
                }
                
                // 페이지 전환 스타일 적용
                document.body.classList.remove('page-ready');
                document.body.classList.add('page-transition');
                
                // 현재 레이아웃 크기 저장
                const navbar = document.querySelector('.navbar');
                const navbarMenu = document.querySelector('.navbar-menu');
                const authButtons = document.querySelector('.auth-buttons');
                
                if (navbarMenu) {
                    sessionStorage.setItem('menuWidth', navbarMenu.offsetWidth);
                }
                if (authButtons) {
                    sessionStorage.setItem('authWidth', authButtons.offsetWidth);
                }

                // 폰트 설정 저장
                sessionStorage.setItem('fonts-loaded', document.documentElement.classList.contains('fonts-loaded'));
            });
        });

        // 페이지 로드가 완료되면 이전 페이지의 폰트 설정 복원
        if (sessionStorage.getItem('fonts-loaded') === 'true') {
            document.documentElement.classList.add('fonts-loaded');
        }
    }

    // 모바일 메뉴 토글 함수
    window.toggleMenu = function() {
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileOverlay = document.getElementById('mobileOverlay');
        
        mobileMenu.classList.toggle('show');
        mobileOverlay.classList.toggle('show');
        
        // 메뉴가 열려있을 때 스크롤 방지
        if (mobileMenu.classList.contains('show')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    };

    // DOM이 로드되면 실행
    document.addEventListener('DOMContentLoaded', function() {
        // 모든 기능 초기화 실행
        preloadFonts();
        setupLayoutStability();
        fixFontStyles();  // 초기 로드 시 폰트 스타일 적용
        
        // 드롭다운 메뉴 토글 (데스크톱)
        const dropdowns = document.querySelectorAll('.dropdown');
        
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('mouseover', function() {
                this.querySelector('.dropdown-content').classList.add('show');
            });
            
            dropdown.addEventListener('mouseout', function() {
                this.querySelector('.dropdown-content').classList.remove('show');
            });
        });
        
        // 모바일에서 뒤로가기 버튼으로 메뉴 닫기
        window.addEventListener('popstate', function() {
            const mobileMenu = document.getElementById('mobileMenu');
            const mobileOverlay = document.getElementById('mobileOverlay');
            
            if (mobileMenu.classList.contains('show')) {
                mobileMenu.classList.remove('show');
                mobileOverlay.classList.remove('show');
                document.body.style.overflow = '';
            }
        });

        // 0.1초 후 폰트 스타일 재적용 (일부 늦게 로드되는 요소 처리)
        setTimeout(fixFontStyles, 100);
    });
})();
