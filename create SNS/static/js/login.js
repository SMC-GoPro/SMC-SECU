// 로그인 폼 표시
function showLogin() {
    window.location.href = '/';
}

// 회원가입 버튼 클릭 시 register.html로 이동
function navigateToRegister() {
    window.location.href = '/register';
}

// 아이디 찾기 폼 표시
function showFindID() {
    window.location.href = '/findid';
}

// 비밀번호 찾기 폼 표시
function showFindPassword() {
    window.location.href = '/findpassword';
}

// 폼 제출 시 AJAX를 사용한 로그인 처리
$(document).ready(function() {
    $('form').submit(function(event) {
        event.preventDefault(); // 기본 제출 동작을 막음

        var username = $('#username').val();
        var password = $('#password').val();

        $.ajax({
            type: 'POST',
            url: '/login',
            data: {
                username: username,
                password: password
            },
            success: function(response) {
                // 로그인 성공 시 메인 페이지로 리다이렉트
                window.location.href = '/main';
            },
            error: function(xhr, status, error) {
                // 로그인 실패 시 에러 처리 (예: 경고 메시지 표시)
                alert('로그인에 실패했습니다. 아이디와 비밀번호를 다시 확인해 주세요.');
            }
        });
    });
});
