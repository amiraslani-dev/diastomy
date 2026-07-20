document.addEventListener("alpine:init", () => {
    Alpine.data("subscriptionController", () => ({
        selectedPlan: 1,
        discountCode: "",

        plans: [
            {
                id: 1,
                name: "اشتراک 1 ماهه",
                oldPrice: "180.000",
                newPrice: "171.000",
            },
            {
                id: 2,
                name: "اشتراک 2 ماهه",
                oldPrice: "180.000",
                newPrice: "171.000",
            },
            {
                id: 3,
                name: "اشتراک 3 ماهه",
                oldPrice: "180.000",
                newPrice: "171.000",
            },
            {
                id: 6,
                name: "اشتراک 6 ماهه",
                oldPrice: "180.000",
                newPrice: "171.000",
            },
            {
                id: 12,
                name: "اشتراک 1 ساله",
                oldPrice: "180.000",
                newPrice: "171.000",
            },
        ],
    }));
});
