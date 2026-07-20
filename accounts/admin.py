from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'full_name', 'phone', 'user_number', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات بیشتر', {'fields': ('full_name', 'phone', 'avatar', 'user_number')}),
    )
    readonly_fields = ['user_number']

admin.site.register(User, CustomUserAdmin)
