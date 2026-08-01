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

        paymentMethod: 'DIRECT',
        cryptoTxHash: '',
        cryptoReceiptFile: null,
        cryptoReceiptFileName: '',
        copiedWallet: false,
        isSubmittingCrypto: false,

        copyWallet(address) {
            if (!address) return;
            navigator.clipboard.writeText(address).then(() => {
                this.copiedWallet = true;
                setTimeout(() => this.copiedWallet = false, 2000);
            }).catch(() => {});
        },

        handleReceiptSelect(event) {
            const file = event.target.files[0];
            if (file) {
                this.cryptoReceiptFile = file;
                this.cryptoReceiptFileName = file.name;
            }
        },

        removeReceipt() {
            this.cryptoReceiptFile = null;
            this.cryptoReceiptFileName = '';
            if (this.$refs.receiptInput) {
                this.$refs.receiptInput.value = '';
            }
        },

        async submitCryptoPayment() {
            if (!this.selectedPlan) return;
            if (!this.cryptoTxHash && !this.cryptoReceiptFile) {
                window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "error", title: "خطا", message: "لطفاً حداقل کد/لینک پیگیری یا تصویر رسید را وارد نمایید." } }));
                return;
            }

            this.isSubmittingCrypto = true;

            try {
                let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                let formData = new FormData();
                formData.append('plan_id', this.selectedPlan);
                if (this.discountSuccess && this.discountCode) {
                    formData.append('discount_code', this.discountCode);
                }
                if (this.cryptoTxHash) {
                    formData.append('crypto_tx_hash', this.cryptoTxHash);
                }
                if (this.cryptoReceiptFile) {
                    formData.append('crypto_receipt', this.cryptoReceiptFile);
                }

                const response = await fetch('/accounts/api/create-crypto-payment/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken || ''
                    },
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "success", title: "ثبت موفق", message: data.message } }));
                    setTimeout(() => {
                        window.location.href = data.redirect_url || '/accounts/payment-info/';
                    }, 1500);
                } else {
                    window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "error", title: "خطا در ثبت رسید", message: data.message || "خطایی رخ داد" } }));
                }
            } catch (error) {
                console.error(error);
                window.dispatchEvent(new CustomEvent("show-modal", { detail: { type: "error", title: "خطا", message: "خطای ارتباط با سرور" } }));
            } finally {
                this.isSubmittingCrypto = false;
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
