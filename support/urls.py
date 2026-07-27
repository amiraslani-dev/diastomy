from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('support/', views.support_view, name='support'),
    path('support/operator/', views.operator_chat_view, name='operator_chat'),
    path('support/upload/', views.upload_attachment_view, name='upload_attachment'),
]