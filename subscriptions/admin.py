from django.contrib import admin
from .models import Plan, Subscription, Payment

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'old_price', 'new_price', 'duration_days']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'end_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'tracking_code', 'status', 'created_at']
    list_filter = ['status', 'created_at']
