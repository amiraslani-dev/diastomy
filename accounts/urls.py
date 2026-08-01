from django.urls import path, include
from django.views.generic import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:user_info', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/logout/', views.api_logout_view, name='api_logout'),
    path('api/check-phone/', views.check_phone_view, name='api_check_phone'),
    path('api/send-otp/', views.send_otp_view, name='api_send_otp'),
    path('api/verify-otp/', views.verify_otp_view, name='api_verify_otp'),
    path('api/complete-registration/', views.complete_registration_view, name='api_complete_registration'),
    path('api/login-password/', views.login_password_view, name='api_login_password'),
    path('api/google-login/', views.google_login_view, name='api_google_login'),
    path('api/google-request-otp/', views.google_request_otp_view, name='api_google_request_otp'),
    path('api/google-verify-otp/', views.google_verify_otp_view, name='api_google_verify_otp'),
    
    path('user-info/', views.user_info_view, name='user_info'),
    path('api/update-profile/', views.api_update_profile_view, name='api_update_profile'),
    path('forgot-password/', views.forgot_password_page_view, name='forgot_password'),
    path('api/forgot-password-request/', views.api_forgot_password_request, name='api_forgot_password_request'),
    path('api/forgot-password-verify/', views.api_forgot_password_verify, name='api_forgot_password_verify'),
    path('api/forgot-password-reset/', views.api_forgot_password_reset, name='api_forgot_password_reset'),

    # Dashboard pages
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/dismiss/', views.dismiss_notification_view, name='dismiss_notification'),
    path('api/notifications/', views.api_notifications_list_view, name='api_notifications'),
    path('api/notifications/mark-read/', views.api_mark_notifications_read_view, name='api_notifications_mark_read'),
    path('settings/', views.settings_view, name='settings'),
    path('api/change-password/', views.api_change_password_view, name='api_change_password'),
    path('api/update-player-quality/', views.api_update_player_quality_view, name='api_update_player_quality'),
    path('api/set-language/', views.api_set_language_view, name='api_set_language'),
    path('api/devices/<int:pk>/terminate/', views.api_terminate_device_view, name='api_terminate_device'),
    path('api/devices/terminate-others/', views.api_terminate_other_devices_view, name='api_terminate_other_devices'),


    # Nested dashboard apps (subscriptions and support are part of accounts dashboard)
    path('', include(('subscriptions.urls', 'subscriptions'), namespace='subscriptions')),
    path('', include(('support.urls', 'support'), namespace='support')),
]