import random
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

def generate_user_number():
    while True:
        num = "".join([str(random.randint(0, 9)) for _ in range(10)])
        # Avoid starting with 0 if you want a clean number look, or allow it
        if num[0] != '0' and not User.objects.filter(user_number=num).exists():
            return num

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="شماره موبایل")
    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="نام و نام خانوادگی")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="تصویر آواتار")
    user_number = models.CharField(max_length=10, unique=True, editable=False, verbose_name="شماره کاربری")
    
    QUALITY_CHOICES = (
        ('AUTO', 'خودکار'),
        ('VeryHigh', 'خیلی بالا (1080p)'),
        ('High', 'بالا (720p)'),
        ('Medium', 'متوسط (480p)'),
        ('Low', 'پایین (360p)'),
    )
    preferred_quality = models.CharField(
        max_length=20,
        choices=QUALITY_CHOICES,
        default='AUTO',
        verbose_name="کیفیت پیش‌فرض پخش‌کننده"
    )

    LANGUAGE_CHOICES = (
        ('fa', 'فارسی'),
        ('en', 'English'),
        ('ar', 'العربیه'),
        ('ru', 'Русский'),
        ('tr', 'Türkçe'),
    )
    preferred_language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='fa',
        verbose_name="زبان پیش‌فرض"
    )

    # Onboarding fields
    has_completed_onboarding = models.BooleanField(default=False, verbose_name="تکمیل سلیقه‌سنجی")
    favorite_movies = models.ManyToManyField('movie.Movie', blank=True, verbose_name="فیلم‌های مورد علاقه")
    favorite_series = models.ManyToManyField('movie.Series', blank=True, verbose_name="سریال‌های مورد علاقه")
    def save(self, *args, **kwargs):
        if not self.user_number:
            self.user_number = generate_user_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def has_active_subscription(self):
        from django.utils import timezone
        return self.subscriptions.filter(is_active=True, end_date__gt=timezone.now()).exists()


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('SUCCESS', 'موفق (سبز)'),
        ('DANGER', 'خطا/مهم (قرمز)'),
        ('WARNING', 'هشدار (نارنجی)'),
        ('INFO', 'اطلاعیه (آبی)'),
    )

    title = models.CharField(max_length=255, verbose_name="عنوان")
    message = models.TextField(verbose_name="متن اعلان")
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='INFO', 
        verbose_name="نوع اعلان"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ انتشار")
    dismissed_users = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='dismissed_notifications',
        verbose_name="کاربرانی که این اعلان را بسته‌اند"
    )

    class Meta:
        verbose_name = "اعلان عمومی"
        verbose_name_plural = "اعلان‌های عمومی"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"


class UserDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices', verbose_name="کاربر")
    session_key = models.CharField(max_length=40, db_index=True, verbose_name="کلید نشست")
    device_name = models.CharField(max_length=255, verbose_name="نام دستگاه و مرورگر")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="آدرس IP")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="آخرین فعالیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ لاگین")

    class Meta:
        verbose_name = "دستگاه فعال"
        verbose_name_plural = "دستگاه‌های فعال"
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"

