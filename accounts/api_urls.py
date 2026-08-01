from django.urls import path
from . import views

urlpatterns = [
    path('check-phone/', views.check_phone_view, name='raw_api_check_phone'),
    path('send-otp/', views.send_otp_view, name='raw_api_send_otp'),
    path('verify-otp/', views.verify_otp_view, name='raw_api_verify_otp'),
    path('complete-registration/', views.complete_registration_view, name='raw_api_complete_registration'),
    path('login-password/', views.login_password_view, name='raw_api_login_password'),
    path('google-login/', views.google_login_view, name='raw_api_google_login'),
    path('google-request-otp/', views.google_request_otp_view, name='raw_api_google_request_otp'),
    path('google-verify-otp/', views.google_verify_otp_view, name='raw_api_google_verify_otp'),
    path('update-profile/', views.api_update_profile_view, name='raw_api_update_profile'),
    path('forgot-password-request/', views.api_forgot_password_request, name='raw_api_forgot_password_request'),
    path('forgot-password-verify/', views.api_forgot_password_verify, name='raw_api_forgot_password_verify'),
    path('forgot-password-reset/', views.api_forgot_password_reset, name='raw_api_forgot_password_reset'),
    path('notifications/', views.api_notifications_list_view, name='raw_api_notifications'),
    path('notifications/mark-read/', views.api_mark_notifications_read_view, name='raw_api_notifications_mark_read'),
    path('change-password/', views.api_change_password_view, name='raw_api_change_password'),
    path('update-player-quality/', views.api_update_player_quality_view, name='raw_api_update_player_quality'),
    path('set-language/', views.api_set_language_view, name='raw_api_set_language'),
    path('devices/<int:pk>/terminate/', views.api_terminate_device_view, name='raw_api_terminate_device'),
    path('devices/terminate-others/', views.api_terminate_other_devices_view, name='raw_api_terminate_other_devices'),
]
