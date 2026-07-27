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

@admin.register(Payment)
class PaymentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['user', 'amount', 'tracking_code', 'status', 'get_created_at']
    list_filter = ['status', 'created_at']

    @admin.display(description='تاریخ ثبت تراکنش', ordering='created_at')
    def get_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return "-"


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

