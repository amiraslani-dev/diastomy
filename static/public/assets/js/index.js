// public/assets/js/index.js

document.addEventListener("DOMContentLoaded", function () {
    // ------------------------------------------
    // 1. Hero Main Slider
    // ------------------------------------------
    var heroSliderElement = document.querySelector(".hero-main-slider");
    if (heroSliderElement) {
        var heroSplide = new Splide(heroSliderElement, {
            type: "fade",
            rewind: true,
            perPage: 1,
            arrows: false,
            pagination: false,
            autoplay: true,
            interval: 5000,
            pauseOnHover: false,
            pauseOnFocus: false,
        });

        var bar = document.getElementById("hero-progress");

        heroSplide.on("autoplay:playing", function (rate) {
            if (bar) {
                bar.style.width = rate * 100 + "%";
            }
        });

        heroSplide.mount();

        var prevBtn = document.querySelector(".hero-prev");
        var nextBtn = document.querySelector(".hero-next");

        if (prevBtn) {
            prevBtn.addEventListener("click", function () {
                heroSplide.go("<");
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener("click", function () {
                heroSplide.go(">");
            });
        }
    }

    // ------------------------------------------
    // 2. HP Movie Slider (.hp-slider-section)
    // ------------------------------------------
    var hpSliderSections = document.querySelectorAll(".hp-slider-section");
    hpSliderSections.forEach(function (section) {
        var sliderElement = section.querySelector(".hp-movie-slider");
        var prevButton = section.querySelector(".hp-prev-btn");
        var nextButton = section.querySelector(".hp-next-btn");

        if (!sliderElement) return;

        var splide = new Splide(sliderElement, {
            type: "slide",
            direction: "rtl",
            perPage: 1,
            gap: "1rem",
            pagination: false,
            arrows: false,
            breakpoints: {
                767: {
                    destroy: true, // در موبایل اسلایدر کلا غیرفعال میشه
                },
            },
        });

        function updateArrows() {
            if (splide.state.is(Splide.STATES.DESTROYED)) return;
            if (prevButton && nextButton) {
                var currentIndex = splide.index;
                var endIndex = splide.Components.Controller.getEnd();

                prevButton.disabled = currentIndex <= 0;
                nextButton.disabled = currentIndex >= endIndex;
            }
        }

        splide.on("mounted move updated resize refresh", updateArrows);
        splide.mount();

        if (prevButton && nextButton) {
            prevButton.addEventListener("click", function () {
                if (!splide.state.is(Splide.STATES.DESTROYED)) splide.go("<");
            });
            nextButton.addEventListener("click", function () {
                if (!splide.state.is(Splide.STATES.DESTROYED)) splide.go(">");
            });
        }
    });

    // ------------------------------------------
    // 3. Movie Slider 2 (.slider-section-2)
    // ------------------------------------------
    var movieSlider2Element = document.querySelector(".movie-slider-2");
    var prevButton2 = document.querySelector(".slider-section-2 .custom-prev-btn");
    var nextButton2 = document.querySelector(".slider-section-2 .custom-next-btn");

    if (movieSlider2Element) {
        var splide2 = new Splide(movieSlider2Element, {
            type: "loop",
            direction: "rtl",
            perPage: 5,
            perMove: 1,
            gap: "1.5rem",
            pagination: false,
            arrows: false,
            updateOnMove: true,
            flickMaxPages: 1,
            breakpoints: {
                1024: { 
                    perPage: 3, 
                    gap: "0.5rem",
                    focus: 0 
                },
                768: {
                    perPage: 1,
                    gap: "-1.5rem",
                    padding: "22%",
                    focus: "center",
                },
            },
        });

        splide2.mount();

        if (prevButton2 && nextButton2) {
            prevButton2.addEventListener("click", function () {
                splide2.go("<");
            });

            nextButton2.addEventListener("click", function () {
                splide2.go(">");
            });
        }
    }

    // ------------------------------------------
    // 4. Trailer Slider (.trailer-slider-section)
    // ------------------------------------------
    var trailerSections = document.querySelectorAll(".trailer-slider-section");
    trailerSections.forEach(function (section) {
        var sliderElement = section.querySelector(".trailer-slider");
        var prevButton = section.querySelector(".trailer-prev-btn");
        var nextButton = section.querySelector(".trailer-next-btn");

        if (!sliderElement) return;

        var splide = new Splide(sliderElement, {
            type: "slide",
            direction: "rtl",
            perPage: 2,
            perMove: 1,
            gap: "1.5rem",
            pagination: false,
            arrows: false,
            breakpoints: {
                768: {
                    perPage: 1,
                    gap: "1rem",
                },
            },
        });

        function updateArrows() {
            if (prevButton && nextButton) {
                var currentIndex = splide.index;
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

    // ------------------------------------------
    // 5. Custom Splide Instances
    // ------------------------------------------
    if (window.initCustomSplide) {
        initCustomSplide(".slider-section", ".movie-slider", {
            desktop: { perPage: 5, gap: "0.8rem" },
            tablet:  { perPage: 3, gap: "2rem" },
            mobile:  { perPage: 3, gap: "0.3rem" }
        });

        initCustomSplide(".animation-slider", ".animation-slider-box", {
            desktop: { perPage: 4, gap: "1.5rem" }, 
            tablet:  { perPage: 2, gap: "1rem" }, 
            mobile:  { perPage: 1, gap: "0.5rem" } 
        });
    }
});
