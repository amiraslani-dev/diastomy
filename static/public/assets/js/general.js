        document.addEventListener('DOMContentLoaded', function () {
            const slider = document.getElementById('actor-list');
            let isDown = false;
            let startX;
            let scrollLeft;

            if (!slider) return;

            // وقتی کاربر کلیک میکنه (شروع درگ)
            slider.addEventListener('mousedown', (e) => {
                isDown = true;
                startX = e.pageX - slider.offsetLeft;
                scrollLeft = slider.scrollLeft;

                // جادوی کار اینجاست: غیرفعال کردن موقت اسنپ و اسکرول نرم
                slider.style.scrollBehavior = 'auto';
                slider.style.scrollSnapType = 'none';
            });

            // وقتی موس از محدوده خارج میشه
            slider.addEventListener('mouseleave', () => {
                isDown = false;
                // برگردوندن تنظیمات به حالت اولیه (تیلویند)
                slider.style.scrollBehavior = '';
                slider.style.scrollSnapType = '';
            });

            // وقتی کاربر کلیک رو ول میکنه (پایان درگ)
            slider.addEventListener('mouseup', () => {
                isDown = false;
                // برگردوندن تنظیمات به حالت اولیه
                slider.style.scrollBehavior = '';
                slider.style.scrollSnapType = '';
            });

            // موقع حرکت موس
            slider.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - slider.offsetLeft;

                // محاسبه میزان کشش
                // نکته مهم: چون سایتت راست‌چین (RTL) هست، ممکنه مرورگرهای مختلف رفتار متفاوتی داشته باشن.
                // اگر دیدی برعکس کشیده میشه، جای x و startX رو عوض کن: (startX - x)
                const walk = (x - startX) * 2;

                slider.scrollLeft = scrollLeft - walk;
            });
        });
