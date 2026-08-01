from django.db import models

class SiteLanguage(models.Model):
    code = models.CharField(max_length=10, unique=True, verbose_name="کد زبان")
    name = models.CharField(max_length=50, verbose_name="نام زبان")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "زبان سایت"
        verbose_name_plural = "زبان‌های سایت"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.code})"


class SiteSettings(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان سایت")
    logo = models.ImageField(upload_to='site/', verbose_name="لوگوی سایت", blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', verbose_name="فاوآیکون", blank=True, null=True)
    description = models.TextField(verbose_name="توضیحات سایت (سئو)", blank=True)
    instagram_link = models.CharField(max_length=500, verbose_name="لینک پیج اینستاگرام", blank=True, null=True)
    telegram_link = models.CharField(max_length=500, verbose_name="لینک کانال تلگرام", blank=True, null=True)

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

class DashboardSetting(models.Model):
    vat_notice = models.TextField(
        verbose_name=_("متن اطلاع‌رسانی مالیات"),
        default=_("به تمامی مبالغ 10% مالیات بر ارزش افزوده اضافه خواهد شد."),
        blank=True
    )
    support_phone = models.CharField(
        max_length=50,
        verbose_name=_("شماره پشتیبانی (مثلاً: 90002542)"),
        default="90002542",
        blank=True
    )
    crypto_wallet_address = models.CharField(
        max_length=255,
        verbose_name=_("آدرس کیف پول کریپتو (مثلاً: USDT TRC20: TXXXX...)"),
        default="USDT (TRC20): TYourWalletAddressHere",
        blank=True
    )
    crypto_instructions = models.TextField(
        verbose_name=_("راهنمای پرداخت کریپتو"),
        default=_("لطفاً معادل دلاری مبلغ را به آدرس کیف پول واریز کرده و تصویر رسید یا کد پیگیری تراکنش را ارسال نمایید."),
        blank=True
    )

    class Meta:
        verbose_name = _("تنظیمات داشبورد")
        verbose_name_plural = _("تنظیمات داشبورد")

    def __str__(self):
        return str(_("تنظیمات داشبورد"))

class ProfileImage(models.Model):
    dashboard_setting = models.ForeignKey(DashboardSetting, on_delete=models.CASCADE, related_name='default_avatars', verbose_name=_("تنظیمات داشبورد"))
    image = models.ImageField(upload_to='dashboard/avatars/', verbose_name=_("تصویر پروفایل"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("عکس پروفایل پیش‌فرض")
        verbose_name_plural = _("عکس‌های پروفایل پیش‌فرض")
        ordering = ['order']

    def __str__(self):
        return f"عکس پروفایل {self.id}"

class SupportAvatar(models.Model):
    dashboard_setting = models.ForeignKey(DashboardSetting, on_delete=models.CASCADE, related_name='support_avatars', verbose_name=_("تنظیمات داشبورد"))
    name = models.CharField(max_length=100, blank=True, verbose_name=_("نام پشتیبان"))
    image = models.ImageField(upload_to='dashboard/support_avatars/', verbose_name=_("تصویر آواتار"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("آواتار پشتیبان")
        verbose_name_plural = _("آواتارهای پشتیبانان (صفحه پشتیبانی)")
        ordering = ['order']

    def __str__(self):
        return self.name or f"آواتار پشتیبان {self.id}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True, verbose_name=_("آدرس ایمیل"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ثبت‌نام"))
    is_active = models.BooleanField(default=True, verbose_name=_("فعال"))

    class Meta:
        verbose_name = _("عضو خبرنامه")
        verbose_name_plural = _("اعضای خبرنامه")
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class ActorsPageSetting(models.Model):
    title = models.CharField(max_length=255, default='بازیگران', verbose_name=_('عنوان صفحه بازیگران'))
    meta_description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات متا (SEO)'))
    per_page = models.PositiveIntegerField(default=27, verbose_name=_('تعداد بازیگر در هر صفحه'))
    actor_detail_per_page = models.PositiveIntegerField(default=15, verbose_name=_('تعداد فیلم/سریال در صفحه جزئیات بازیگر'))

    class Meta:
        verbose_name = _('تنظیمات صفحه بازیگران')
        verbose_name_plural = _('تنظیمات صفحه بازیگران')

    def __str__(self):
        return self.title or str(_("تنظیمات صفحه بازیگران"))

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class ArchivePageSetting(models.Model):
    movies_title = models.CharField(max_length=255, default='آرشیو فیلم‌ها', verbose_name=_('عنوان صفحه آرشیو فیلم‌ها'))
    movies_meta_description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات متا آرشیو فیلم‌ها (SEO)'))
    
    series_title = models.CharField(max_length=255, default='آرشیو سریال‌ها', verbose_name=_('عنوان صفحه آرشیو سریال‌ها'))
    series_meta_description = models.TextField(blank=True, null=True, verbose_name=_('توضیحات متا آرشیو سریال‌ها (SEO)'))

    class Meta:
        verbose_name = _('تنظیمات صفحات آرشیو')
        verbose_name_plural = _('تنظیمات صفحات آرشیو')

    def __str__(self):
        return str(_("تنظیمات صفحات آرشیو"))

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class HomePageSetting(models.Model):
    title = models.CharField(max_length=255, default='تنظیمات صفحه اصلی', verbose_name=_('عنوان تنظیمات'))
    
    # 1. Hero Slider
    hero_movies = models.ManyToManyField('movie.Movie', blank=True, related_name='hero_settings', verbose_name=_('فیلم‌های اسلایدر اصلی'))
    hero_series = models.ManyToManyField('movie.Series', blank=True, related_name='hero_settings', verbose_name=_('سریال‌های اسلایدر اصلی'))
    
    # 2. Half-price items
    halfprice_movies = models.ManyToManyField('movie.Movie', blank=True, related_name='halfprice_settings', verbose_name=_('فیلم‌های نیم‌بها'))
    halfprice_series = models.ManyToManyField('movie.Series', blank=True, related_name='halfprice_settings', verbose_name=_('سریال‌های نیم‌بها'))
    
    # 3. Suggested Series
    suggested_series = models.ManyToManyField('movie.Series', blank=True, related_name='suggested_settings', verbose_name=_('سریال‌های پیشنهادی'))
    
    # 4. Top Actors
    featured_actors = models.ManyToManyField('movie.Person', blank=True, related_name='featured_settings', verbose_name=_('بازیگران منتخب'))

    # 5. Community Banner
    banner_title = models.CharField(max_length=255, default='برترینهای این هفته رو ببین!', verbose_name=_('عنوان بنر'))
    banner_description = models.TextField(default='با کامیونیتی وارد دنیای فیلمها شو، نظرتو بگو، فیلمای جدید کشف کن و هیجان سینما رو زندگی کن!', verbose_name=_('توضیحات بنر'))
    banner_button_text = models.CharField(max_length=100, default='ورود و تماشا', verbose_name=_('متن دکمه بنر'))
    banner_button_link = models.CharField(max_length=500, default='#', verbose_name=_('لینک دکمه بنر'))
    banner_image = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name=_('تصویر پس‌زمینه بنر'))

    class Meta:
        verbose_name = _('تنظیمات صفحه اصلی')
        verbose_name_plural = _('تنظیمات صفحه اصلی')

    def __str__(self):
        return self.title or str(_('تنظیمات صفحه اصلی'))

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class HomeTrailer(models.Model):
    setting = models.ForeignKey(HomePageSetting, on_delete=models.CASCADE, related_name='trailers', verbose_name=_('تنظیمات صفحه اصلی'))
    cover = models.ImageField(upload_to='trailers/covers/', verbose_name=_('تصویر تریلر'))
    video = models.FileField(upload_to='trailers/videos/', blank=True, null=True, verbose_name=_('فایل ویدیو تریلر'))
    video_url = models.URLField(blank=True, null=True, verbose_name=_('لینک مستقیم ویدیو تریلر'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('ترتیب'))

    class Meta:
        ordering = ['order', '-id']
        verbose_name = _('تریلر صفحه اصلی')
        verbose_name_plural = _('تریلرهای صفحه اصلی')

    def __str__(self):
        return f"تریلر #{self.id}"



