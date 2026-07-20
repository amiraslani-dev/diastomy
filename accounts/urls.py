from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/check-phone/', views.check_phone_view, name='api_check_phone'),
    path('api/send-otp/', views.send_otp_view, name='api_send_otp'),
    path('api/verify-otp/', views.verify_otp_view, name='api_verify_otp'),
    path('api/complete-registration/', views.complete_registration_view, name='api_complete_registration'),
    path('api/login-password/', views.login_password_view, name='api_login_password'),
    path('api/google-login/', views.google_login_view, name='api_google_login'),
    path('api/google-request-otp/', views.google_request_otp_view, name='api_google_request_otp'),
    path('api/google-verify-otp/', views.google_verify_otp_view, name='api_google_verify_otp'),
    
    path('user-info/', views.user_info_view, name='user_info'),
    path('forgot-password/', views.forgot_password_page_view, name='forgot_password'),
    path('api/forgot-password-request/', views.api_forgot_password_request, name='api_forgot_password_request'),
    path('api/forgot-password-verify/', views.api_forgot_password_verify, name='api_forgot_password_verify'),
    path('api/forgot-password-reset/', views.api_forgot_password_reset, name='api_forgot_password_reset'),
]
