document.addEventListener("alpine:init", () => {
    Alpine.data("chatController", () => ({
        showEmoji: false,
        message: "",
        emojiLoaded: false,

        init() {
            this.$watch("showEmoji", (val) => {
                if (val && !this.emojiLoaded) {
                    this.loadEmojiPicker();
                }
            });
        },

        loadEmojiPicker() {
            if (typeof EmojiMart !== "undefined") {
                const pickerOptions = {
                    theme: "dark",
                    locale: "fa",
                    onEmojiSelect: (emoji) => {
                        this.message += emoji.native;
                        this.$nextTick(() => {
                            this.$refs.messageInput.focus();
                            this.resizeTextarea();
                        });
                    },
                };
                const picker = new EmojiMart.Picker(
                    pickerOptions,
                );
                this.$refs.emojiContainer.innerHTML = "";
                this.$refs.emojiContainer.appendChild(
                    picker,
                );
                this.emojiLoaded = true;
            }
        },

        resizeTextarea() {
            let el = this.$refs.messageInput;
            if (el) {
                el.style.height = "auto";
                el.style.height = el.scrollHeight + "px";
            }
        },

        handleFileSelect(event) {
            // منطق آپلود فایل
        },

        sendMessage() {
            // منطق ارسال پیام
        },
    }));
});
