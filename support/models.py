from django.db import models
from django.conf import settings

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'باز'),
        ('PENDING_RESPONSE', 'در انتظار پاسخ پشتیبانی'),
        ('CLOSED', 'بسته شده'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets', verbose_name="کاربر")
    subject = models.CharField(max_length=255, verbose_name="موضوع تیکت")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ آخرین بروزرسانی")

    class Meta:
        verbose_name = "تیکت پشتیبانی"
        verbose_name_plural = "تیکت‌های پشتیبانی"

    def __str__(self):
        return f"{self.subject} - {self.user.username}"


class Message(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', verbose_name="تیکت")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_messages', verbose_name="فرستنده")
    content = models.TextField(verbose_name="متن پیام")
    is_operator = models.BooleanField(default=False, verbose_name="پاسخ پشتیبان")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")

    class Meta:
        verbose_name = "پیام تیکت"
        verbose_name_plural = "پیام‌های تیکت‌ها"

    def __str__(self):
        role = "پشتیبان" if self.is_operator else "کاربر"
        return f"پیام از {role} در تیکت {self.ticket.id}"
