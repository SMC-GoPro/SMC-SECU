let slideIndex = 1;
showSlides(slideIndex);

// Auto slide functionality
let slideInterval = setInterval(() => {
    moveSlide(1);
}, 5000);

function moveSlide(n) {
    showSlides(slideIndex += n);
    resetInterval();
}

function currentSlide(n) {
    showSlides(slideIndex = n);
    resetInterval();
}

function resetInterval() {
    clearInterval(slideInterval);
    slideInterval = setInterval(() => {
        moveSlide(1);
    }, 5000);
}

function showSlides(n) {
    let i;
    let slides = document.getElementsByClassName("slide");
    let dots = document.getElementsByClassName("dot");
    
    if (n > slides.length) {slideIndex = 1}
    if (n < 1) {slideIndex = slides.length}
    
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }
    
    slides[slideIndex-1].style.display = "block";
    dots[slideIndex-1].className += " active";
}

// Make slider responsive
window.addEventListener('resize', () => {
    adjustSliderHeight();
});

function adjustSliderHeight() {
    const slider = document.querySelector('.slider');
    const activeSlide = document.querySelector('.slide[style*="display: block"] img');
    if (activeSlide && slider) {
        const aspectRatio = activeSlide.naturalWidth / activeSlide.naturalHeight;
        const width = slider.clientWidth;
        slider.style.height = (width / aspectRatio) + 'px';
    }
}

// Initial adjustment
window.addEventListener('load', adjustSliderHeight);
