from django.db import models

class SiteSettings(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان سایت")
    logo = models.ImageField(upload_to='site/', verbose_name="لوگوی سایت", blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', verbose_name="فاوآیکون", blank=True, null=True)
    description = models.TextField(verbose_name="توضیحات سایت (سئو)", blank=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.title


class HeaderSetting(models.Model):
    logo = models.FileField(upload_to='header/', verbose_name="لوگو", blank=True, null=True)

    class Meta:
        verbose_name = "تنظیمات هدر"
        verbose_name_plural = "تنظیمات هدر"

    def __str__(self):
        return "تنظیمات هدر"


class HeaderMenuItem(models.Model):
    header_setting = models.ForeignKey(HeaderSetting, on_delete=models.CASCADE, related_name='menu_items', verbose_name="تنظیمات هدر")
    title = models.CharField(max_length=255, verbose_name="عنوان")
    link = models.CharField(max_length=500, verbose_name="لینک")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "منوی هدر"
        verbose_name_plural = "منوهای هدر"
        ordering = ['order']

    def __str__(self):
        return self.title


class FooterSetting(models.Model):
    bg_image = models.FileField(upload_to='footer/', verbose_name="تصویر پس زمینه", blank=True, null=True)
    col1_title_mobile = models.CharField(max_length=255, verbose_name="عنوان ستون 1 منو ها در موبایل", blank=True)
    col2_title_mobile = models.CharField(max_length=255, verbose_name="عنوان ستون 2 منو ها در موبایل", blank=True)
    footer_text = models.TextField(verbose_name="متن فوتر", blank=True)
    newsletter_title_desktop = models.CharField(max_length=255, verbose_name="عنوان باکس خبرنامه در دسکتاپ", blank=True)
    newsletter_title_mobile = models.CharField(max_length=255, verbose_name="عنوان باکس خبرنامه در موبایل", blank=True)
    privacy_text = models.TextField(verbose_name="متن حریم خصوصی", blank=True)

    class Meta:
        verbose_name = "تنظیمات فوتر"
        verbose_name_plural = "تنظیمات فوتر"

    def __str__(self):
        return "تنظیمات فوتر"


class FooterMenuColumn1(models.Model):
    footer_setting = models.ForeignKey(FooterSetting, on_delete=models.CASCADE, related_name='col1_menus', verbose_name="تنظیمات فوتر")
    title = models.CharField(max_length=255, verbose_name="عنوان")
    link = models.CharField(max_length=500, verbose_name="لینک")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "منوی ستون ۱ فوتر"
        verbose_name_plural = "منوهای ستون ۱ فوتر"
        ordering = ['order']

    def __str__(self):
        return self.title


class FooterMenuColumn2(models.Model):
    footer_setting = models.ForeignKey(FooterSetting, on_delete=models.CASCADE, related_name='col2_menus', verbose_name="تنظیمات فوتر")
    title = models.CharField(max_length=255, verbose_name="عنوان")
    link = models.CharField(max_length=500, verbose_name="لینک")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "منوی ستون ۲ فوتر"
        verbose_name_plural = "منوهای ستون ۲ فوتر"
        ordering = ['order']

    def __str__(self):
        return self.title


class FooterSocialMedia(models.Model):
    footer_setting = models.ForeignKey(FooterSetting, on_delete=models.CASCADE, related_name='social_medias', verbose_name="تنظیمات فوتر")
    svg = models.TextField(verbose_name="کد SVG")
    link = models.CharField(max_length=500, verbose_name="لینک")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "شبکه اجتماعی فوتر"
        verbose_name_plural = "شبکه‌های اجتماعی فوتر"
        ordering = ['order']

    def __str__(self):
        return self.link


# Centralized Admin Notification System
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class AdminNotification(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    message = models.CharField(max_length=255, verbose_name="پیام")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "اعلان ادمین"
        verbose_name_plural = "اعلان‌های ادمین"
        ordering = ['-created_at']

    def __str__(self):
        return self.message

    def get_admin_url(self):
        from django.urls import reverse
        return reverse(
            f"admin:{self.content_type.app_label}_{self.content_type.model}_change",
            args=[self.object_id]
        )


from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class UserTasteSettings(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("عنوان صفحه"))
    movies = models.ManyToManyField('movie.Movie', blank=True, verbose_name=_("فیلم‌ها"))
    series = models.ManyToManyField('movie.Series', blank=True, verbose_name=_("سریال‌ها"))

    class Meta:
        verbose_name = _("تنظیمات صفحه سلیقه کاربر")
        verbose_name_plural = _("تنظیمات صفحه سلیقه کاربر")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.pk:
            total_count = self.movies.count() + self.series.count()
            if total_count > 10:
                raise ValidationError(_("مجموع تعداد فیلم‌ها و سریال‌های انتخاب شده نمی‌تواند بیشتر از 10 باشد."))
