document.addEventListener("alpine:init", () => {
    Alpine.data("profileSettings", () => ({
        isAvatarModalOpen: false,
        currentAvatar: "https://i.pravatar.cc/200?img=32", // عکس پروفایل فعلی کاربر
        predefinedAvatars: [
            "https://i.pravatar.cc/200?img=47",
            "https://i.pravatar.cc/200?img=12",
            "https://i.pravatar.cc/200?img=68",
            "https://i.pravatar.cc/200?img=5",
        ], // 4 آواتار آماده
        fields: {
            firstName: { val: "یلدا", edit: false },
            lastName: { val: "حضرتی", edit: false },
            phone: { val: "09373050735", edit: false },
            email: { val: "yaldaaa2777@gmail.com", edit: false },
            username: { val: "yalda-27", edit: false },
        },

        toggleEdit(fieldKey, isMobile = false) {
            // معکوس کردن وضعیت ویرایش فیلد مورد نظر
            this.fields[fieldKey].edit =
                !this.fields[fieldKey].edit;

            // اگر فیلد فعال شد، فوکوس رو بفرست داخلش
            if (this.fields[fieldKey].edit) {
                let refName = fieldKey + (isMobile ? "M" : "D");
                this.$nextTick(() => {
                    if (this.$refs[refName]) {
                        this.$refs[refName].focus();
                    }
                });
            }
        },

        // انتخاب آواتار از لیست
        selectAvatar(url) {
            this.currentAvatar = url;
            // بعد از انتخاب شدن میتونی با خط زیر کاری کنی که مودال بسته بشه
            setTimeout(() => {
                this.isAvatarModalOpen = false;
            }, 300);
        },

        // تابع برای باز کردن فایل (آپلود عکس شخصی)
        handleAvatarUpload(event) {
            const file = event.target.files[0];
            if (file) {
                // ساختن یک لینک موقت و جایگذاری به عنوان تصویر پروفایل
                const imageUrl = URL.createObjectURL(file);
                this.currentAvatar = imageUrl;
                console.log("تصویر انتخاب شد:", file.name);
            }
        },
    }));
});
