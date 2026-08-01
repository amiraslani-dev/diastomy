import json
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from . import services


@login_required
def subscription_view(request):
    plans_data = services.get_plans_data()
    return render(request, 'subscriptions/subscription.html', {
        'active_tab': 'subscription',
        'plans_data': plans_data,
    })


@login_required
def payment_info_view(request):
    payments = services.get_user_payments(request.user)
    return render(request, 'subscriptions/payment-info.html', {
        'active_tab': 'payment-info',
        'payments': payments,
    })


@login_required
def check_discount_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            plan_id = data.get('plan_id')
            success, message, discount_amount = services.check_discount_code(request.user, code, plan_id)
            return JsonResponse({'success': success, 'message': message, 'discount': discount_amount})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'متد غیرمجاز'})


@login_required
def create_payment_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_id = data.get('plan_id')
            discount_code_str = data.get('discount_code')

            success, message, payment_url = services.create_zarinpal_payment(
                user=request.user,
                plan_id=plan_id,
                discount_code_str=discount_code_str,
                request=request
            )
            if success and payment_url:
                return JsonResponse({'success': True, 'redirect_url': payment_url})
            else:
                return JsonResponse({'success': False, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'متد غیرمجاز'})


@login_required
def verify_zarinpal_payment_view(request):
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    success, message, payment = services.verify_zarinpal_payment(
        user=request.user,
        authority=authority,
        status_str=status
    )
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('accounts:subscriptions:payment_info')


@login_required
def api_verify_zarinpal_payment(request):
    authority = request.GET.get('Authority') or request.POST.get('Authority')
    status = request.GET.get('Status') or request.POST.get('Status')

    success, message, payment = services.verify_zarinpal_payment(
        user=request.user,
        authority=authority,
        status_str=status
    )
    return JsonResponse({
        'success': success,
        'message': message,
        'payment_id': payment.id if payment else None,
        'status': payment.status if payment else 'FAILED',
    })


@login_required
def create_crypto_payment_view(request):
    if request.method == 'POST':
        try:
            plan_id = request.POST.get('plan_id')
            discount_code_str = request.POST.get('discount_code')
            crypto_tx_hash = request.POST.get('crypto_tx_hash')
            crypto_receipt_image = request.FILES.get('crypto_receipt')

            if not crypto_tx_hash and not crypto_receipt_image:
                return JsonResponse({'success': False, 'message': 'لطفاً حداقل کد/لینک پیگیری یا تصویر رسید را وارد نمایید.'})

            success, message, payment = services.create_crypto_payment(
                user=request.user,
                plan_id=plan_id,
                discount_code_str=discount_code_str,
                crypto_tx_hash=crypto_tx_hash,
                crypto_receipt_image=crypto_receipt_image
            )
            if success:
                redirect_url = reverse('accounts:subscriptions:payment_info')
                return JsonResponse({'success': True, 'message': message, 'redirect_url': redirect_url})
            else:
                return JsonResponse({'success': False, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'متد غیرمجاز'})


@login_required
def verify_payment_mock_view(request, payment_id):
    services.process_payment_verification(request.user, payment_id)
    return redirect('accounts:subscriptions:payment_info')


@login_required
def get_plans_api(request):
    plans_data = services.get_plans_data()
    return JsonResponse({'success': True, 'plans': plans_data})


@login_required
def get_payments_api(request):
    payments = services.get_user_payments(request.user)
    data = []
    for p in payments:
        data.append({
            'id': p.id,
            'plan_name': p.subscription.plan.name if p.subscription and p.subscription.plan else "-",
            'amount': p.formatted_amount,
            'tracking_code': p.tracking_code,
            'status': p.status,
            'status_display': p.get_status_display(),
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'success': True, 'payments': data})

