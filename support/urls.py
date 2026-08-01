from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('support/', views.support_view, name='support'),
    path('support/operator/', views.operator_chat_view, name='operator_chat'),
    path('support/upload/', views.upload_attachment_view, name='upload_attachment'),

    # REST API Endpoints for Mobile App & External Integration
    path('support/api/messages/', views.api_get_messages_view, name='api_get_messages'),
    path('support/api/send/', views.api_send_message_view, name='api_send_message'),
    path('support/api/rooms/', views.api_list_rooms_view, name='api_list_rooms'),
]