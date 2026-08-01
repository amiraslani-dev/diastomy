from django.contrib import admin
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date import datetime2jalali
from .models import SupportRoom, SupportMessage

class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 1

@admin.register(SupportRoom)
class SupportRoomAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['user', 'is_active', 'unread_by_admin', 'unread_by_user', 'get_updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__phone_number']
    inlines = [SupportMessageInline]

    @admin.display(description='تاریخ بروزرسانی', ordering='updated_at')
    def get_updated_at(self, obj):
        if obj.updated_at:
            return datetime2jalali(obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return "-"

@admin.register(SupportMessage)
class SupportMessageAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['room', 'sender', 'is_operator', 'get_created_at']
    list_filter = ['is_operator', 'created_at']
    search_fields = ['room__user__username', 'content']

    @admin.display(description='تاریخ ارسال', ordering='created_at')
    def get_created_at(self, obj):
        if obj.created_at:
            return datetime2jalali(obj.created_at).strftime('%Y/%m/%d %H:%M')
        return "-"

