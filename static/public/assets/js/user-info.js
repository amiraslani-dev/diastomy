
// Fallback if main.js is cached or delayed
if (typeof window.showToast !== 'function') {
    window.showToast = function(type, title, message, duration = 3000) {
        window.dispatchEvent(new CustomEvent('show-toast', {
            detail: { id: Date.now() + Math.random(), type, title, message, duration }
        }));
    };
}

document.addEventListener("alpine:init", () => {

    Alpine.data("profileSettings", () => {
        const initData = window.DASHBOARD_DATA || {};
        
        return {
            showMobileMenu: false,
            isAvatarModalOpen: false,
            currentAvatar: initData.avatar || "", 
            predefinedAvatars: initData.default_avatars || [],
            fields: {
                // Name, Phone, Email are disabled from template, but we keep them here for display if needed
                fullName: { val: initData.full_name || "", edit: false },
                phone: { val: initData.phone || "", edit: false },
                email: { val: initData.email || "", edit: false },
                username: { val: initData.username || "", edit: false },
            },
            isSaving: false,

            toggleEdit(fieldKey, isMobile = false) {
                // Only username and email are allowed to be edited based on new rules
                if (fieldKey !== 'username' && fieldKey !== 'email') return;
                
                this.fields[fieldKey].edit = !this.fields[fieldKey].edit;

                if (this.fields[fieldKey].edit) {
                    let refName = fieldKey + (isMobile ? "M" : "D");
                    this.$nextTick(() => {
                        if (this.$refs[refName]) {
                            this.$refs[refName].focus();
                        }
                    });
                }
            },

            async selectAvatar(avatarObj) {
                this.currentAvatar = avatarObj.url;
                
                try {
                    let formData = new FormData();
                    formData.append('default_avatar_id', avatarObj.id);
                    // Add CSRF
                    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                    
                    let res = await fetch(initData.update_url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        },
                        body: formData
                    });
                    
                    if (res.ok) {
                        setTimeout(() => {
                            this.isAvatarModalOpen = false;
                        }, 300);
                    } else {
                        window.showModal('error', 'خطا', 'خطا در تغییر عکس پروفایل');
                    }
                } catch (e) {
                    window.showModal('error', 'خطا', 'خطای شبکه');
                }
            },

            async handleAvatarUpload(event) {
                const file = event.target.files[0];
                if (file) {
                    const imageUrl = URL.createObjectURL(file);
                    this.currentAvatar = imageUrl;
                    
                    try {
                        let formData = new FormData();
                        formData.append('avatar', file);
                        let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                        
                        let res = await fetch(initData.update_url, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': csrfToken,
                            },
                            body: formData
                        });
                        
                        if (res.ok) {
                            this.isAvatarModalOpen = false;
                        } else {
                            window.showModal('error', 'خطا', 'خطا در آپلود عکس');
                        }
                    } catch (e) {
                        window.showModal('error', 'خطا', 'خطای شبکه');
                    }
                }
            },
            
            async saveProfile() {
                this.isSaving = true;
                try {
                    let formData = new FormData();
                    formData.append('username', this.fields.username.val);
                    formData.append('email', this.fields.email.val);
                    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                    
                    let res = await fetch(initData.update_url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                        },
                        body: formData
                    });
                    
                    if (res.ok) {
                        let data = await res.json();
                        window.showModal('success', 'موفق', data.message || 'اطلاعات با موفقیت ذخیره شد');
                        this.fields.username.edit = false;
                        this.fields.email.edit = false;
                    } else {
                        let data = await res.json();
                        window.showModal('error', 'خطا', data.error || 'خطا در ذخیره اطلاعات');
                    }
                } catch (e) {
                    window.showModal('error', 'خطا', 'خطای شبکه');
                } finally {
                    this.isSaving = false;
                }
            }
        };
    });
});
