from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('subscription/', views.subscription_view, name='subscription'),
    path('payment-info/', views.payment_info_view, name='payment_info'),
    path('api/check-discount/', views.check_discount_api, name='check_discount'),
    path('api/plans/', views.get_plans_api, name='api_get_plans'),
    path('api/payments/', views.get_payments_api, name='api_get_payments'),
    path('api/create-payment/', views.create_payment_view, name='create_payment'),
    path('api/create-crypto-payment/', views.create_crypto_payment_view, name='create_crypto_payment'),
    path('api/verify-zarinpal/', views.api_verify_zarinpal_payment, name='api_verify_zarinpal'),
    path('verify-zarinpal/', views.verify_zarinpal_payment_view, name='verify_zarinpal'),
    path('verify-payment/<int:payment_id>/', views.verify_payment_mock_view, name='verify_payment_mock'),
]