// public/assets/js/main.js

// ۱. ساخت یک تابع کلی برای راه‌اندازی اسلایدرها
window.initCustomSplide = function(sectionClass, sliderClass, config) {
    var sliderSections = document.querySelectorAll(sectionClass);

    sliderSections.forEach(function (section) {
        var sliderElement = section.querySelector(sliderClass);
        var prevButton = section.querySelector(".custom-prev-btn");
        var nextButton = section.querySelector(".custom-next-btn");

        if (!sliderElement) return;

        // راه‌اندازی اسپلاید با تنظیمات کاملاً داینامیک
        var splide = new Splide(sliderElement, {
            type: "slide",
            direction: "rtl",
            perPage: config.desktop.perPage,
            perMove: 1,
            gap: config.desktop.gap,
            pagination: false,
            arrows: false,
            breakpoints: {
                1024: { 
                    perPage: config.tablet.perPage, 
                    gap: config.tablet.gap 
                },
                768: {
                    perPage: config.mobile.perPage,
                    gap: config.mobile.gap,
                    padding: { left: "20%" },
                },
            },
        });

        function updateArrows(newIndex) {
            if (prevButton && nextButton) {
                var currentIndex = typeof newIndex === "number" ? newIndex : splide.index;
                var endIndex = splide.Components.Controller.getEnd();

                prevButton.disabled = currentIndex <= 0;
                nextButton.disabled = currentIndex >= endIndex;
            }
        }

        splide.on("mounted move updated resize refresh", updateArrows);
        splide.mount();

        if (prevButton && nextButton) {
            prevButton.addEventListener("click", function () {
                splide.go("<");
            });

            nextButton.addEventListener("click", function () {
                splide.go(">");
            });
        }
    });
};

document.addEventListener("DOMContentLoaded", function () {
    // پیدا کردن تمام المان‌هایی که کلاس drag-scroll دارند
    const dragSliders = document.querySelectorAll(".drag-scroll");

    // اجرای منطق درگ برای تک‌تک آن‌ها
    dragSliders.forEach((slider) => {
        let isDown = false;
        let startX;
        let scrollLeft;

        slider.addEventListener("mousedown", (e) => {
            isDown = true;
            startX = e.pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            slider.style.scrollBehavior = "auto";
            slider.style.scrollSnapType = "none";
        });

        slider.addEventListener("mouseleave", () => {
            isDown = false;
            slider.style.scrollBehavior = "";
            slider.style.scrollSnapType = "";
        });

        slider.addEventListener("mouseup", () => {
            isDown = false;
            slider.style.scrollBehavior = "";
            slider.style.scrollSnapType = "";
        });

        slider.addEventListener("mousemove", (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - slider.offsetLeft;
            const walk = (x - startX) * 2;
            slider.scrollLeft = scrollLeft - walk;
        });
    });
});

// تعریف استور سراسری مودال برای آلپاین
window.showModal = function(type, title, message) {
    window.dispatchEvent(new CustomEvent('show-modal', {
        detail: { type, title, message }
    }));
};

function registerGlobalModal() {

    // Keep store for backward compatibility, but make it use the event
    Alpine.store('globalModal', {
        isOpen: false,
        type: 'success',
        title: '',
        message: '',
        show(type, title, message) {
            window.showModal(type, title, message);
        },
        close() {} // Handled internally by modals.html now
    });
}

// تعریف استور سراسری توست برای آلپاین
window.showToast = function(type, title, message, duration = 3000) {
    window.dispatchEvent(new CustomEvent('show-toast', {
        detail: { id: Date.now() + Math.random(), type, title, message, duration }
    }));
};

function registerGlobalToast() {
    
    // Keep store for backward compatibility if needed, but it won't be used by our new toasts.html
    Alpine.store('globalToast', {
        toasts: [],
        show(type, title, message, duration = 3000) {
            window.showToast(type, title, message, duration);
        }
    });
}

if (window.Alpine) {
    registerGlobalModal();
    registerGlobalToast();
} else {
    document.addEventListener('alpine:init', () => {
        registerGlobalModal();
        registerGlobalToast();
    });
}
