from django.contrib import admin
from .models import Ticket, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 1

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'sender', 'is_operator', 'created_at']
    list_filter = ['is_operator', 'created_at']
