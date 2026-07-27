from django.contrib import admin
from .models import SupportRoom, SupportMessage

class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 1

@admin.register(SupportRoom)
class SupportRoomAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'unread_by_admin', 'unread_by_user', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__phone_number']
    inlines = [SupportMessageInline]

@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'sender', 'is_operator', 'created_at']
    list_filter = ['is_operator', 'created_at']
    search_fields = ['room__user__username', 'content']
