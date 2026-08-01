import uuid
from decimal import Decimal
from django.utils import timezone
from django.utils.translation import gettext as _
from .models import Plan, Payment, Subscription, DiscountCode
from .utils import add_jalali_months


def get_user_payments(user):
    """
    Returns payments list for a given user ordered by created_at desc.
    """
    return user.payments.all().order_by('-created_at')


def get_plans_data():
    """
    Returns plans formatted data list for subscription page/API.
    """
    plans = Plan.objects.all().order_by('duration_months')
    plans_data = []
    for plan in plans:
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'oldPrice': f"{plan.old_price:,}" if plan.old_price else "",
            'newPrice': f"{plan.new_price:,}" if plan.new_price else "",
            'durationMonths': plan.duration_months,
            'oldPriceRaw': float(plan.old_price) if plan.old_price else 0,
            'newPriceRaw': float(plan.new_price) if plan.new_price else 0
        })
    return plans_data


def check_discount_code(user, code, plan_id):
    """
    Validates discount code and returns calculated discount.
    """
    if not code or not plan_id:
        return False, _("اطلاعات ناقص است"), None

    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return False, _("پلن یافت نشد"), None

    base_price = plan.new_price if plan.new_price else plan.old_price

    try:
        discount = DiscountCode.objects.get(code=code)
        if not discount.is_valid(user):
            return False, _("کد تخفیف نامعتبر یا منقضی شده است"), None

        final_price = discount.calculate_discount(base_price)
        discount_amount = float(base_price - final_price)
        return True, _("کد تخفیف با موفقیت اعمال شد"), discount_amount
    except DiscountCode.DoesNotExist:
        return False, _("کد تخفیف یافت نشد"), None


def create_user_payment(user, plan_id, discount_code_str=None):
    """
    Creates pending subscription & payment record and returns payment object.
    """
    if not plan_id:
        return False, _("پلن نامعتبر است"), None

    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return False, _("پلن یافت نشد"), None

    base_price = plan.new_price if plan.new_price else plan.old_price

    discount = None
    final_price = base_price

    if discount_code_str:
        try:
            discount_obj = DiscountCode.objects.get(code=discount_code_str)
            if discount_obj.is_valid(user):
                discount = discount_obj
                final_price = discount_obj.calculate_discount(base_price)
        except DiscountCode.DoesNotExist:
            pass

    vat = final_price * Decimal('0.10')
    total_amount = final_price + vat

    now = timezone.now()
    active_sub = user.subscriptions.filter(is_active=True, end_date__gt=now).order_by('-end_date').first()
    start_date = active_sub.end_date if active_sub else now

    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        start_date=start_date,
        end_date=add_jalali_months(start_date, plan.duration_months),
        is_active=False
    )

    payment = Payment.objects.create(
        user=user,
        subscription=subscription,
        amount=total_amount,
        tracking_code=str(uuid.uuid4())[:12],
        status='PENDING',
        discount_code=discount.code if discount else ''
    )

    return True, _("پرداخت ایجاد شد"), payment


def create_crypto_payment(user, plan_id, discount_code_str=None, crypto_tx_hash=None, crypto_receipt_image=None):
    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return False, _("پلن یافت نشد"), None

    base_price = plan.new_price if plan.new_price else plan.old_price

    discount = None
    final_price = base_price

    if discount_code_str:
        try:
            discount_obj = DiscountCode.objects.get(code=discount_code_str)
            if discount_obj.is_valid(user):
                discount = discount_obj
                final_price = discount_obj.calculate_discount(base_price)
        except DiscountCode.DoesNotExist:
            pass

    vat = final_price * Decimal('0.10')
    total_amount = final_price + vat

    now = timezone.now()
    active_sub = user.subscriptions.filter(is_active=True, end_date__gt=now).order_by('-end_date').first()
    start_date = active_sub.end_date if active_sub else now

    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        start_date=start_date,
        end_date=add_jalali_months(start_date, plan.duration_months),
        is_active=False
    )

    payment = Payment.objects.create(
        user=user,
        subscription=subscription,
        amount=total_amount,
        payment_method='CRYPTO',
        tracking_code=str(uuid.uuid4())[:12],
        crypto_tx_hash=crypto_tx_hash or '',
        crypto_receipt_image=crypto_receipt_image,
        status='AWAITING_VERIFICATION',
        discount_code=discount.code if discount else ''
    )

    try:
        from core.models import AdminNotification
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Payment)
        AdminNotification.objects.create(
            content_type=ct,
            object_id=payment.id,
            message=f"پرداخت کریپتویی جدید توسط {user.username} ثبت شد."
        )
    except Exception:
        pass

    return True, _("رسید پرداخت کریپتویی با موفقیت ثبت شد و در انتظار تایید ادمین است."), payment


def process_payment_verification(user, payment_id):
    """
    Verifies pending payment, activates subscription, increments discount usage.
    """
    try:
        payment = Payment.objects.get(id=payment_id, user=user)
    except Payment.DoesNotExist:
        return False, _("پرداخت یافت نشد"), None

    if payment.status in ['PENDING', 'AWAITING_VERIFICATION']:
        payment.status = 'SUCCESS'
        payment.save()

        now = timezone.now()
        active_sub = user.subscriptions.filter(is_active=True, end_date__gt=now).exclude(id=payment.subscription.id).order_by('-end_date').first()
        start_date = active_sub.end_date if active_sub else now
        end_date = add_jalali_months(start_date, payment.subscription.plan.duration_months)

        payment.subscription.start_date = start_date
        payment.subscription.end_date = end_date
        payment.subscription.is_active = True
        payment.subscription.save()

        if payment.discount_code:
            try:
                discount = DiscountCode.objects.get(code=payment.discount_code)
                discount.used_count += 1
                discount.save()
            except DiscountCode.DoesNotExist:
                pass

    return True, _("پرداخت تأیید شد"), payment


def create_zarinpal_payment(user, plan_id, discount_code_str=None, request=None):
    """
    Creates payment record and sends payment request to ZarinPal, returning (success, message, payment_url).
    """
    from django.urls import reverse
    from .zarinpal import create_payment_request

    success, message, payment = create_user_payment(user, plan_id, discount_code_str)
    if not success:
        return False, message, None

    callback_url = request.build_absolute_uri(reverse('accounts:subscriptions:verify_zarinpal')) if request else ""

    amount_in_rial = int(payment.amount * 10)

    z_success, z_message, authority, payment_url = create_payment_request(
        amount=amount_in_rial,
        description=f"خرید اشتراک {payment.subscription.plan.name} - {user.username}",
        callback_url=callback_url,
        email=getattr(user, 'email', None),
        mobile=getattr(user, 'phone_number', None),
    )

    if z_success and authority:
        payment.tracking_code = authority
        payment.save()
        return True, _("درخواست پرداخت ایجاد شد"), payment_url
    else:
        payment.status = 'FAILED'
        payment.save()
        return False, z_message, None


def verify_zarinpal_payment(user, authority, status_str):
    """
    Verifies returned ZarinPal payment and updates payment/subscription status.
    """
    from .zarinpal import verify_payment_request

    if not authority:
        return False, _("شناسه پرداخت (Authority) نامعتبر است"), None

    try:
        payment = Payment.objects.get(tracking_code=authority, user=user)
    except Payment.DoesNotExist:
        try:
            payment = Payment.objects.get(tracking_code=authority)
        except Payment.DoesNotExist:
            return False, _("تراکنش مورد نظر یافت نشد"), None

    if status_str != 'OK':
        payment.status = 'FAILED'
        payment.save()
        return False, _("پرداخت توسط کاربر لغو شد یا با خطا مواجه گردید"), payment

    amount_in_rial = int(payment.amount * 10)
    z_success, z_message, ref_id, card_pan = verify_payment_request(authority, amount_in_rial)

    if z_success:
        if ref_id:
            payment.tracking_code = str(ref_id)
        payment.status = 'SUCCESS'
        payment.save()

        process_payment_verification(payment.user, payment.id)
        return True, _("پرداخت شما با موفقیت تایید شد و اشتراک شما فعال گردید."), payment
    else:
        payment.status = 'FAILED'
        payment.save()
        return False, z_message, payment
