document.addEventListener("alpine:init", () => {
    Alpine.data("subscriptionController", () => ({
        selectedPlan: window.SUBSCRIPTION_PLANS && window.SUBSCRIPTION_PLANS.length > 0 ? window.SUBSCRIPTION_PLANS[0].id : null,
        discountCode: "",
        discountAmount: 0,
        plans: window.SUBSCRIPTION_PLANS || [],

        get activePlan() {
            return this.plans.find(p => p.id == this.selectedPlan) || null;
        },

        get basePrice() {
            if (!this.activePlan) return 0;
            return this.activePlan.newPriceRaw ? this.activePlan.newPriceRaw : this.activePlan.oldPriceRaw;
        },

        get vatAmount() {
            let taxable = this.basePrice - this.discountAmount;
            if (taxable < 0) taxable = 0;
            return taxable * 0.10;
        },

        get totalAmount() {
            let payable = (this.basePrice - this.discountAmount) + this.vatAmount;
            return payable > 0 ? payable : 0;
        },

        
        discountMessage: "",
        discountSuccess: false,
        isApplyingDiscount: false,

        async applyDiscount() {
            if (!this.discountCode) return;
            this.isApplyingDiscount = true;
            this.discountMessage = "";
            
            try {
                let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                const response = await fetch('/accounts/api/check-discount/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken || ''
                    },
                    body: JSON.stringify({
                        code: this.discountCode,
                        plan_id: this.selectedPlan
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    this.discountAmount = data.discount_amount;
                    this.discountSuccess = true;
                    window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: data.success ? "success" : "error", title: data.success ? "موفقیت" : "خطا", message: data.message } }));
                } else {
                    this.discountAmount = 0;
                    this.discountSuccess = false;
                    window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: data.success ? "success" : "error", title: data.success ? "موفقیت" : "خطا", message: data.message } }));
                }
            } catch (error) {
                console.error(error);
                window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "error", title: "خطا", message: "خطایی رخ داد" } }));
                this.discountSuccess = false;
            } finally {
                this.isApplyingDiscount = false;
            }
        },

        
        isProcessingPayment: false,
        async processPayment() {
            if (!this.selectedPlan) return;
            this.isProcessingPayment = true;
            
            try {
                let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                const response = await fetch('/accounts/api/create-payment/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken || ''
                    },
                    body: JSON.stringify({
                        plan_id: this.selectedPlan,
                        discount_code: this.discountSuccess ? this.discountCode : ''
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "error", title: "خطا در پرداخت", message: data.message || "خطایی رخ داد" } }));
                }
            } catch (error) {
                console.error(error);
                window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "error", title: "خطا", message: "خطای ارتباط با سرور" } }));
            } finally {
                this.isProcessingPayment = false;
            }
        },

        init() {
            this.$watch('selectedPlan', () => {
                if(this.discountAmount > 0) {
                    this.applyDiscount();
                }
            });
        },

        formatPrice(price) {
            return Math.floor(price).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
    }));
});
