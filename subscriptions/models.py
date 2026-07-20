from django.db import models
from django.conf import settings

class Plan(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام بسته")
    description = models.TextField(blank=True, verbose_name="توضیحات بسته")
    old_price = models.DecimalField(max_length=12, decimal_places=0, max_digits=12, null=True, blank=True, verbose_name="قیمت قدیمی (تومان)")
    new_price = models.DecimalField(max_length=12, decimal_places=0, max_digits=12, verbose_name="قیمت جدید (تومان)")
    duration_days = models.PositiveIntegerField(verbose_name="مدت زمان به روز")

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
