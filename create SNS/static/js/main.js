document.addEventListener('DOMContentLoaded', function() {
    const createPostLink = document.getElementById('createPostLink');
    const postForm = document.getElementById('postForm');
    const imageUpload = document.getElementById('imageUpload');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const createForm = document.getElementById('createForm');

    // '만들기' 링크 클릭 시 게시물 작성 폼 토글
    createPostLink.addEventListener('click', function(event) {
        event.preventDefault();
        if (postForm.style.display === 'none' || postForm.style.display === '') {
            postForm.style.display = 'block';
        } else {
            postForm.style.display = 'none';
        }
    });

// 이미지 업로드 시 미리보기
imageUpload.addEventListener('change', function(event) {
    imagePreviewContainer.innerHTML = ''; // 기존 미리보기 초기화
    const files = event.target.files;
    if (files.length > 10) {
        alert('최대 10개의 이미지만 업로드할 수 있습니다.');
        imageUpload.value = ''; // 선택된 파일 초기화
        return;
    }

    Array.from(files).forEach(file => {
        if (file.type !== 'image/png') {
            alert('PNG 파일만 업로드할 수 있습니다.');
            imageUpload.value = ''; // 선택된 파일 초기화
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.alt = file.name;
            img.style.width = '100%'; // 미리보기 이미지 크기 조절
            img.style.height = 'auto'; // 이미지 비율 유지
            img.style.margin = '5px';
            imagePreviewContainer.appendChild(img);
        };
        reader.readAsDataURL(file);
    });
});


    // 폼 제출 시 처리
    createForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const title = document.getElementById('postTitle').value.trim();
        const content = document.getElementById('postContent').value.trim();

        if (!title || !content) {
            alert('제목과 내용을 모두 입력하세요.');
            return;
        }

        // 게시물 목록에 새 게시물 추가
        const postList = document.getElementById('postList');
        const newPost = document.createElement('div');
        
        let postContent = `
            <h3>${title}</h3>
            <p>${content}</p>
        `;

        const images = imagePreviewContainer.getElementsByTagName('img');
        if (images.length > 0) {
            const sliderContainer = document.createElement('div');
            sliderContainer.className = 'slider-container';
            const leftArrow = document.createElement('div');
            leftArrow.className = 'left-arrow';
            leftArrow.innerHTML = '&#10094;';
            const rightArrow = document.createElement('div');
            rightArrow.className = 'right-arrow';
            rightArrow.innerHTML = '&#10095;';

            const slidesWrapper = document.createElement('div');
            slidesWrapper.className = 'slides-wrapper';

            Array.from(images).forEach(img => {
                const slide = document.createElement('div');
                slide.className = 'slide';
                slide.appendChild(img.cloneNode(true));
                slidesWrapper.appendChild(slide);
            });

            sliderContainer.appendChild(leftArrow);
            sliderContainer.appendChild(slidesWrapper);
            sliderContainer.appendChild(rightArrow);
            postContent += sliderContainer.outerHTML;
        }

        postContent += '<hr>';
        newPost.innerHTML = postContent;
        postList.prepend(newPost);

        // 슬라이더 초기화
        const newSlidesWrapper = newPost.querySelector('.slides-wrapper');
        const newSlides = newSlidesWrapper.getElementsByClassName('slide');
        if (newSlides.length > 0) {
            newSlides[0].style.display = 'block';
            for (let i = 1; i < newSlides.length; i++) {
                newSlides[i].style.display = 'none';
            }
        }

        // 폼 초기화
        createForm.reset();
        imagePreviewContainer.innerHTML = '';
        postForm.style.display = 'none';
    });

    // 슬라이드 기능 추가
    document.addEventListener('click', function(event) {
        if (event.target.matches('.right-arrow')) {
            const slidesWrapper = event.target.previousElementSibling;
            const slides = slidesWrapper.getElementsByClassName('slide');
            const currentSlideIndex = Array.from(slides).findIndex(slide => slide.style.display === 'block');
            slides[currentSlideIndex].style.display = 'none';
            const nextSlideIndex = (currentSlideIndex + 1) % slides.length;
            slides[nextSlideIndex].style.display = 'block';
        } else if (event.target.matches('.left-arrow')) {
            const slidesWrapper = event.target.nextElementSibling;
            const slides = slidesWrapper.getElementsByClassName('slide');
            const currentSlideIndex = Array.from(slides).findIndex(slide => slide.style.display === 'block');
            slides[currentSlideIndex].style.display = 'none';
            const prevSlideIndex = (currentSlideIndex - 1 + slides.length) % slides.length;
            slides[prevSlideIndex].style.display = 'block';
        }
    });
});
