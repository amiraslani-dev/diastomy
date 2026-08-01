document.addEventListener("alpine:init", () => {
    Alpine.data("chatController", () => ({
        showEmoji: false,
        message: "",
        messages: [],
        emojiLoaded: false,
        socket: null,
        isOperatorTyping: false,
        typingTimeout: null,

        init() {
            this.connectWebSocket();
        },

        connectWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = wsProtocol + window.location.host + '/ws/support/chat/';
            
            try {
                this.socket = new WebSocket(wsUrl);

                this.socket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'history') {
                        this.messages = data.messages || [];
                    } else if (data.type === 'chat_message' && data.message) {
                        const newMsg = data.message;
                        if (!Array.isArray(this.messages)) this.messages = [];
                        
                        const tempIndex = this.messages.findIndex(m => String(m.id).startsWith('temp_') && m.content === newMsg.content);
                        if (tempIndex !== -1) {
                            this.messages[tempIndex] = newMsg;
                        } else {
                            const exists = this.messages.some(m => m.id === newMsg.id);
                            if (!exists) {
                                this.messages.push(newMsg);
                            }
                        }
                        this.isOperatorTyping = false;
                    } else if (data.type === 'typing_status') {
                        if (data.is_operator) {
                            this.isOperatorTyping = data.is_typing;
                        }
                    }
                    this.scrollToBottom();
                };

                this.socket.onclose = () => {
                    setTimeout(() => {
                        this.connectWebSocket();
                    }, 3000);
                };
            } catch (e) {
                console.error("WebSocket error:", e);
            }
        },

        handleInput() {
            this.resizeTextarea();
            this.sendTypingSignal();
        },

        sendTypingSignal() {
            if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
            
            this.socket.send(JSON.stringify({
                type: 'typing',
                is_typing: true
            }));

            if (this.typingTimeout) clearTimeout(this.typingTimeout);
            this.typingTimeout = setTimeout(() => {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({
                        type: 'typing',
                        is_typing: false
                    }));
                }
            }, 2000);
        },

        activeEmojiTab: 'smileys',

        selectEmoji(char) {
            this.message += char;
            this.$nextTick(() => {
                if (this.$refs.messageInput) {
                    this.$refs.messageInput.focus();
                    this.resizeTextarea();
                }
            });
        },

        resizeTextarea() {
            let el = this.$refs.messageInput;
            if (el) {
                el.style.height = "auto";
                el.style.height = el.scrollHeight + "px";
            }
        },

        selectedFile: null,
        selectedFileName: "",

        triggerFileInput() {
            if (this.$refs.fileInput) {
                this.$refs.fileInput.click();
            }
        },

        handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.selectedFile = file;
            this.selectedFileName = file.name;
        },

        removeSelectedFile() {
            this.selectedFile = null;
            this.selectedFileName = "";
            if (this.$refs.fileInput) {
                this.$refs.fileInput.value = "";
            }
        },

        sendMessage() {
            const text = this.message.trim();

            if (this.selectedFile) {
                const formData = new FormData();
                formData.append('file', this.selectedFile);
                if (text) {
                    formData.append('content', text);
                }

                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

                fetch('/accounts/support/upload/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        this.message = '';
                        this.removeSelectedFile();
                        this.resizeTextarea();
                    } else {
                        alert(data.error || 'خطا در آپلود فایل');
                    }
                })
                .catch(err => {
                    console.error("Upload error:", err);
                    alert('خطایی در شبکه هنگام آپلود فایل رخ داد.');
                });
                return;
            }

            if (!text) return;

            // 1. Instant Optimistic UI Push with real user avatar
            const now = new Date();
            const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
            const userAvatar = window.USER_AVATAR || "https://ui-avatars.com/api/?name=User&background=DD0202&color=fff";
            
            const tempMsg = {
                id: 'temp_' + Date.now(),
                content: text,
                is_operator: false,
                sender_avatar: userAvatar,
                created_at: timeStr
            };

            if (!Array.isArray(this.messages)) this.messages = [];
            this.messages.push(tempMsg);

            // 2. Send over WebSocket
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    type: 'chat_message',
                    message: text
                }));
            }

            // 3. Clear input
            this.message = "";
            this.resizeTextarea();
            this.scrollToBottom();
        },

        scrollToBottom() {
            const doScroll = () => {
                const container = this.$refs.messagesContainer;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            };
            this.$nextTick(() => {
                doScroll();
                setTimeout(doScroll, 50);
                setTimeout(doScroll, 150);
                setTimeout(doScroll, 350);
            });
        }
    }));
});
