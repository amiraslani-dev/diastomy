document.addEventListener("DOMContentLoaded", function () {
    if (window.initCustomSplide) {
        initCustomSplide(".slider-section", ".movie-slider", {
            desktop: { perPage: 5, gap: "0.8rem" },
            tablet:  { perPage: 3, gap: "2rem" },
            mobile:  { perPage: 2, gap: "1rem" }
        });
    }
});
