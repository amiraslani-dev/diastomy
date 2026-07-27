from django.db import models
from django.conf import settings

class SupportRoom(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_room',
        verbose_name="کاربر"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    unread_by_admin = models.IntegerField(default=0, verbose_name="پیام‌های خوانده‌نشده ادمین")
    unread_by_user = models.IntegerField(default=0, verbose_name="پیام‌های خوانده‌نشده کاربر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "اتاق پشتیبانی"
        verbose_name_plural = "اتاق‌های پشتیبانی"
        ordering = ['-updated_at']

    def __str__(self):
        return f"اتاق پشتیبانی {self.user.get_full_name() or self.user.username}"


class SupportMessage(models.Model):
    room = models.ForeignKey(
        SupportRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="اتاق پشتیبانی"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_support_messages',
        verbose_name="فرستنده"
    )
    content = models.TextField(blank=True, verbose_name="متن پیام")
    attachment = models.FileField(upload_to='support_attachments/', blank=True, null=True, verbose_name="فایل پیوست")
    is_operator = models.BooleanField(default=False, verbose_name="پاسخ پشتیبان")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")

    class Meta:
        verbose_name = "پیام پشتیبانی"
        verbose_name_plural = "پیام‌های پشتیبانی"
        ordering = ['created_at']

    @property
    def attachment_name(self):
        if self.attachment:
            import os
            return os.path.basename(self.attachment.name)
        return ""

    @property
    def attachment_type(self):
        if self.attachment:
            name = self.attachment.name.lower()
            if name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp')):
                return 'image'
            elif name.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
                return 'audio'
            elif name.endswith(('.mp4', '.mkv', '.webm', '.avi')):
                return 'video'
            else:
                return 'document'
        return "text"

    def __str__(self):
        role = "پشتیبان" if self.is_operator else "کاربر"
        return f"پیام از {role} در {self.room.user.username}"

# Aliases for backward compatibility if any
Ticket = SupportRoom
Message = SupportMessage
