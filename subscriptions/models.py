from django.db import models
from django.conf import settings
from django.utils import timezone

class Plan(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام بسته")
    description = models.TextField(blank=True, verbose_name="توضیحات بسته")
    old_price = models.DecimalField(max_length=12, decimal_places=0, max_digits=12, null=True, blank=True, verbose_name="قیمت بدون تخفیف (تومان)")
    new_price = models.DecimalField(max_length=12, decimal_places=0, max_digits=12, null=True, blank=True, verbose_name="قیمت تخفیفی (تومان)")
    duration_months = models.PositiveIntegerField(default=1, verbose_name="مدت زمان (ماه)")

    class Meta:
        verbose_name = "بسته اشتراک"
        verbose_name_plural = "بسته‌های اشتراک"

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="کاربر")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, verbose_name="بسته")
    start_date = models.DateTimeField(verbose_name="تاریخ شروع")
    end_date = models.DateTimeField(verbose_name="تاریخ پایان")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "اشتراک کاربر"
        verbose_name_plural = "اشتراک‌های کاربران"

    def __str__(self):
        return f"اشتراک {self.user.username} - {self.plan.name if self.plan else 'نامشخص'}"

    @property
    def is_valid(self):
        from django.utils import timezone
        if self.is_active and self.end_date and self.end_date > timezone.now():
            return True
        return False


class Payment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار پرداخت'),
        ('SUCCESS', 'پرداخت موفق'),
        ('FAILED', 'پرداخت ناموفق'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments', verbose_name="کاربر")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="اشتراک مربوطه")
    amount = models.DecimalField(max_length=12, decimal_places=0, max_digits=12, verbose_name="مبلغ (تومان)")
    tracking_code = models.CharField(max_length=100, blank=True, verbose_name="کد رهگیری بانکی")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت پرداخت")
    discount_code = models.CharField(max_length=50, blank=True, verbose_name="کد تخفیف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت تراکنش")

    class Meta:
        verbose_name = "تراکنش پرداخت"
        verbose_name_plural = "تراکنش‌های پرداخت"

    def __str__(self):
        return f"تراکنش {self.id} - {self.user.username} - {self.amount} تومان"

    @property
    def formatted_amount(self):
        if self.amount:
            return f"{int(self.amount):,}"
        return "0"
        
    @property
    def expected_end_date(self):
        
        if self.subscription and self.subscription.plan:
            from .utils import add_jalali_months
            return add_jalali_months(self.subscription.start_date, self.subscription.plan.duration_months)
        return None



class DiscountCode(models.Model):
    DISCOUNT_TYPES = (
        ('PERCENT', 'درصدی'),
        ('FIXED', 'مبلغ ثابت'),
    )
    
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="عنوان (فقط برای ادمین)")
    code = models.CharField(max_length=50, unique=True, verbose_name="کد تخفیف")
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='PERCENT', verbose_name="نوع تخفیف")
    value = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مقدار تخفیف (درصد یا تومان)")
    
    expiration_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")
    max_uses = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر تعداد استفاده")
    used_count = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده شده")
    
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='allowed_discounts', verbose_name="کاربران مجاز (در صورت خالی بودن برای همه مجاز است)")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        if self.title:
            return f"{self.title} ({self.code}) - {self.get_discount_type_display()} ({self.value})"
        return f"{self.code} - {self.get_discount_type_display()} ({self.value})"

    def is_valid(self, user=None):
        if not self.is_active:
            return False
        if self.expiration_date and self.expiration_date < timezone.now():
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        if self.allowed_users.exists():
            if not user or not self.allowed_users.filter(id=user.id).exists():
                return False
        return True

    def calculate_discount(self, original_price):
        if self.discount_type == 'PERCENT':
            discount = (original_price * self.value) / 100
            return max(0, original_price - discount)
        elif self.discount_type == 'FIXED':
            return max(0, original_price - self.value)
        return original_price
