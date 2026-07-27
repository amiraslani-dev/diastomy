from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from modeltranslation.admin import TranslationAdmin
from .models import User, Notification, UserDevice

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'full_name', 'phone', 'preferred_language', 'preferred_quality', 'user_number', 'is_staff']
    list_filter = UserAdmin.list_filter + ('preferred_language', 'preferred_quality')
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات بیشتر', {'fields': ('full_name', 'phone', 'avatar', 'user_number', 'preferred_language', 'preferred_quality')}),
    )
    readonly_fields = ['user_number']

admin.site.register(User, CustomUserAdmin)

@admin.register(Notification)
class NotificationAdmin(TranslationAdmin):
    list_display = ['title', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['title', 'message']
    filter_horizontal = ['dismissed_users']

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'ip_address', 'last_activity', 'created_at']
    list_filter = ['created_at', 'last_activity']
    search_fields = ['user__username', 'device_name', 'ip_address', 'session_key']

