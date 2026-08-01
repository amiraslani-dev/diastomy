from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Plan, Subscription, Payment, DiscountCode
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali

@admin.register(Plan)
class PlanAdmin(ModelAdminJalaliMixin, TranslationAdmin):
    list_display = ['name', 'old_price', 'new_price', 'duration_months']

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['user', 'plan', 'get_start_date', 'get_end_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'end_date']

    @admin.display(description='تاریخ شروع', ordering='start_date')
    def get_start_date(self, obj):
        if obj.start_date:
            return datetime2jalali(obj.start_date).strftime('%Y/%m/%d %H:%M')
        return "-"

    @admin.display(description='تاریخ پایان', ordering='end_date')
    def get_end_date(self, obj):
        if obj.end_date:
            return datetime2jalali(obj.end_date).strftime('%Y/%m/%d %H:%M')
        return "-"

from django.utils.html import format_html
from .services import process_payment_verification

@admin.register(Payment)
class PaymentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_method', 'status', 'tracking_code', 'crypto_tx_hash', 'get_created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['user__username', 'tracking_code', 'crypto_tx_hash', 'discount_code']
    readonly_fields = ['receipt_preview']
    fields = ['user', 'subscription', 'amount', 'payment_method', 'status', 'tracking_code', 'crypto_tx_hash', 'crypto_receipt_image', 'receipt_preview', 'discount_code']
    actions = ['approve_selected_payments']

    @admin.display(description='پیش‌نمایش رسید کریپتو')
    def receipt_preview(self, obj):
        if obj.crypto_receipt_image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 250px; max-width: 100%; border-radius: 8px; border: 1px solid #ccc;" /></a>', obj.crypto_receipt_image.url)
        return "رسیدی بارگذاری نشده است"

    @admin.display(description='تاریخ ثبت تراکنش', ordering='created_at')
    def get_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return "-"

    @admin.action(description='تایید و فعال‌سازی پرداخت‌های انتخاب شده')
    def approve_selected_payments(self, request, queryset):
        count = 0
        for payment in queryset:
            if payment.status != 'SUCCESS':
                success, msg, _ = process_payment_verification(payment.user, payment.id)
                if success:
                    count += 1
        self.message_user(request, f"تعداد {count} پرداخت با موفقیت تایید و اشتراک کاربر فعال گردید.")

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data and obj.status == 'SUCCESS':
            obj.save()
            process_payment_verification(obj.user, obj.id)
        else:
            super().save_model(request, obj, form, change)


@admin.register(DiscountCode)
class DiscountCodeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['title', 'code', 'discount_type', 'value', 'get_expiration_date', 'max_uses', 'used_count', 'is_active']
    list_filter = ['discount_type', 'is_active', 'expiration_date']

    @admin.display(description='تاریخ انقضا', ordering='expiration_date')
    def get_expiration_date(self, obj):
        if obj.expiration_date:
            return datetime2jalali(obj.expiration_date).strftime('%Y/%m/%d %H:%M')
        return "-"
    search_fields = ['code', 'title']
    filter_horizontal = ['allowed_users']
    readonly_fields = ['used_count']
    fields = ['is_active', 'title', 'code', 'used_count', 'discount_type', 'value', 'expiration_date', 'max_uses', 'allowed_users']

