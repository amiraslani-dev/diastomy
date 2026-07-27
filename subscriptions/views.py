import json
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
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
        'payments': payments
    })


@login_required
def check_discount_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            plan_id = data.get('plan_id')

            success, message, discount_amount = services.check_discount_code(request.user, code, plan_id)
            if success:
                return JsonResponse({'success': True, 'discount_amount': discount_amount, 'message': message})
            else:
                return JsonResponse({'success': False, 'message': message})
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

            success, message, payment = services.create_user_payment(request.user, plan_id, discount_code_str)
            if success:
                verify_url = reverse('accounts:subscriptions:verify_payment_mock', args=[payment.id])
                return JsonResponse({'success': True, 'redirect_url': verify_url})
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

