// 캐릭터 요소 가져오기
const character = document.getElementById('character');

// 초기 위치
let posX = window.innerWidth / 2; // 가로 중앙
let posY = window.innerHeight / 2; // 세로 중앙

// 이동 거리 상수
const moveAmount = 5;

// 방향키 입력 상태를 추적할 객체
const keys = {
    ArrowLeft: false,
    ArrowRight: false,
    ArrowUp: false,
    ArrowDown: false
};

// 게임 종료 상태 변수
let isGameOver = false;
let isInvincible = false; // 무적 상태 변수

// 점수 변수
let score = 0;

// 점수 표시 요소 생성
const scoreElement = document.createElement('div');
scoreElement.style.position = 'fixed';
scoreElement.style.top = '10px';
scoreElement.style.left = '10px';
scoreElement.style.fontSize = '24px';
scoreElement.style.color = 'white';
scoreElement.style.zIndex = '1000';
document.body.appendChild(scoreElement);
updateScoreDisplay();

// 이벤트 리스너 추가: 키보드 이벤트 감지
document.addEventListener('keydown', function(event) {
    keys[event.key] = true;
});

document.addEventListener('keyup', function(event) {
    keys[event.key] = false;
});

// 캐릭터 위치 업데이트 및 이미지 회전 함수
function updateCharacterPosition() {
    if (keys.ArrowLeft && keys.ArrowUp) {
        moveLeft();
        moveUp();
        character.style.transform = 'rotate(45deg)';
    } else if (keys.ArrowLeft && keys.ArrowDown) {
        moveLeft();
        moveDown();
        character.style.transform = 'rotate(-45deg)';
    } else if (keys.ArrowRight && keys.ArrowUp) {
        moveRight();
        moveUp();
        character.style.transform = 'rotate(135deg)';
    } else if (keys.ArrowRight && keys.ArrowDown) {
        moveRight();
        moveDown();
        character.style.transform = 'rotate(-135deg)';
    } else if (keys.ArrowLeft) {
        moveLeft();
        character.style.transform = 'rotate(0deg)';
    } else if (keys.ArrowRight) {
        moveRight();
        character.style.transform = 'rotate(180deg)';
    } else if (keys.ArrowUp) {
        moveUp();
        character.style.transform = 'rotate(90deg)';
    } else if (keys.ArrowDown) {
        moveDown();
        character.style.transform = 'rotate(-90deg)';
    }
}

// 왼쪽으로 이동 함수
function moveLeft() {
    posX -= moveAmount;
}

// 오른쪽으로 이동 함수
function moveRight() {
    posX += moveAmount;
}

// 위로 이동 함수
function moveUp() {
    posY -= moveAmount;
}

// 아래로 이동 함수
function moveDown() {
    posY += moveAmount;
}

// 반복적으로 위치 업데이트
function animate() {
    if (!isGameOver) {
        updateCharacterPosition();
        character.style.left = posX + 'px';
        character.style.top = posY + 'px';
        requestAnimationFrame(animate);
    }
}

// 애니메이션 시작
animate();

// 충돌 감지 함수
function isColliding(rect1, rect2) {
    return !(rect1.right < rect2.left || 
             rect1.left > rect2.right || 
             rect1.bottom < rect2.top || 
             rect1.top > rect2.bottom);
}

// 이미지 떨어뜨리는 함수
function dropImage() {
    if (isGameOver) return; // 게임 종료 상태에서는 함수 실행 중지

    const fallingImage = document.createElement('div');
    fallingImage.style.width = '150px';
    fallingImage.style.height = '150px';
    const isDo = Math.random() < 0.1;
    fallingImage.style.backgroundImage = isDo ? 'url("do.png")' : 'url("ledo1.png")'; // 10% 확률로 보너스 이미지
    fallingImage.style.backgroundSize = 'cover';
    fallingImage.style.position = 'absolute';
    fallingImage.style.top = '0';
    fallingImage.style.left = Math.random() * window.innerWidth + 'px';
    document.body.appendChild(fallingImage);

    if (isDo) {
        const doText = document.createElement('div');
        doText.textContent = '보너스!';
        doText.classList.add('do-text'); // do-text 클래스 추가
        fallingImage.appendChild(doText); // 보너스 텍스트를 fallingImage 안에 넣습니다.
    }
    

    let fallingPosY = 0;
    const fallingSpeed = 5;

    function fall() {
        if (isGameOver) return; // 게임 종료 상태에서는 함수 실행 중지

        fallingPosY += fallingSpeed;
        fallingImage.style.top = fallingPosY + 'px';

        const characterRect = character.getBoundingClientRect();
        const fallingImageRect = fallingImage.getBoundingClientRect();

        if (isColliding(characterRect, fallingImageRect)) {
            if (isDo) {
                isInvincible = true;
                setTimeout(() => {
                    isInvincible = false;
                }, 3000); // 3초 후 무적 상태 해제
                document.body.removeChild(fallingImage);
            } else if (!isInvincible) {
                // 일반 이미지와 충돌 시
                gameOverMessage.style.display = 'block';
                isGameOver = true; // 게임 종료 상태로 설정
                clearInterval(imageDropInterval); // 이미지 떨어뜨리는 인터벌 중지
                document.getElementById('back').style.display = 'block'; // 돌아가기 버튼 표시
                
                // 말풍선 생성 및 표시
                const speechBubble = document.createElement('div');
                speechBubble.textContent = '이걸 죽냐 ㅋ';
                speechBubble.style.position = 'absolute';
                speechBubble.style.top = fallingImageRect.top - 30 + 'px'; // 이미지 위쪽에 위치
                speechBubble.style.left = fallingImageRect.left + 16 + 'px'; // 이미지 왼쪽에 맞춤
                speechBubble.style.padding = '5px 10px';
                speechBubble.style.background = 'rgba(0, 0, 0, 0.7)';
                speechBubble.style.color = 'white';
                speechBubble.style.borderRadius = '5px';
                speechBubble.style.zIndex = '1000';
                document.body.appendChild(speechBubble);

                return;
            }
        }

        if (fallingPosY < window.innerHeight) {
            requestAnimationFrame(fall);
        } else {
            // 이미지가 화면 아래로 지나가면 점수 증가
            score += 10;
            updateScoreDisplay();
            document.body.removeChild(fallingImage);
        }
    }

    fall();
}

// 점수 표시 업데이트 함수
function updateScoreDisplay() {
    scoreElement.textContent = '점수: ' + score;
}

// 게임 시작 버튼 클릭 시 이벤트 처리
const startGameButton = document.getElementById('startGame');
const gameOverMessage = document.getElementById('gameOverMessage');
const goBackButton = document.getElementById('goBack');

let imageDropInterval;
let imageDropIntervalTime = 1000; // 초기 이미지 떨어지는 간격 (1초)

// 이미지 떨어지는 간격 점진적으로 줄이기 위한 함수
function increaseImageDropRate() {
    if (isGameOver) return; // 게임 종료 상태에서는 함수 실행 중지
    if (imageDropIntervalTime > 200) { // 최소 간격을 0.2초로 설정
        imageDropIntervalTime -= 200; // 간격을 0.2초씩 줄임
        clearInterval(imageDropInterval);
        imageDropInterval = setInterval(dropImage, imageDropIntervalTime);
    }
}

startGameButton.addEventListener('click', function() {
    if (isGameOver) return; // 게임 종료 상태라면 동작하지 않음

    // 이미지가 계속 떨어지도록 인터벌 설정
    imageDropInterval = setInterval(dropImage, imageDropIntervalTime);

    // 20초마다 이미지 떨어지는 간격 줄이기
    setInterval(increaseImageDropRate, 20000);
});

// 돌아가기 버튼 클릭 시 페이지 새로고침
goBackButton.addEventListener('click', function() {
    location.reload();
});
