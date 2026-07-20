from django.utils.translation import gettext as _
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from . import services

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/accounts/user-info/')
    
    context = {
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID_HERE')
    }
    return render(request, 'accounts/auth/login.html', context)

@login_required
def user_info_view(request):
    return render(request, 'accounts/user-info.html', {'active_tab': 'user-info'})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('accounts:login')

@require_POST
def check_phone_view(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        
        if not phone:
            return JsonResponse({'error': _('شماره موبایل وارد شده معتبر نیست')}, status=400)
            
        status = services.check_user_status(phone)
        return JsonResponse(status)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)


@require_POST
def send_otp_view(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        
        if not phone:
            return JsonResponse({'error': _('شماره موبایل وارد شده معتبر نیست')}, status=400)
            
        success, message = services.generate_and_send_otp(phone)
        if success:
            return JsonResponse({'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)


@require_POST
def verify_otp_view(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        code = data.get('code')
        
        if not phone or not code:
            return JsonResponse({'error': _('شماره موبایل معتبر و کد تایید الزامی است')}, status=400)
            
        user, needs_registration = services.verify_otp_code(phone, code)
        
        if user:
            # Explicitly specify backend to avoid Multiple authentication backends error
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            redirect_url = '/accounts/user-info/' if user.has_completed_onboarding else '/selection/'
            return JsonResponse({'message': _('با موفقیت وارد شدید'), 'redirect_url': redirect_url})
        elif needs_registration:
            request.session['verified_phone'] = phone
            return JsonResponse({'needs_registration': True})
        else:
            return JsonResponse({'error': _('کد تایید نامعتبر است یا منقضی شده')}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

@require_POST
def complete_registration_view(request):
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name', '')
        email = data.get('email', '')
        username = data.get('username', '')
        password = data.get('password', '')
        
        phone = request.session.get('verified_phone')
        
        if not phone:
            return JsonResponse({'error': _('نشست شما منقضی شده است. لطفا مجدد تلاش کنید.')}, status=400)
            
        if not all([full_name, email, username, password]):
            return JsonResponse({'error': _('تمامی فیلدها الزامی است')}, status=400)
            
        if services.User.objects.filter(username=username).exists():
            return JsonResponse({'error': _('این نام کاربری قبلا استفاده شده است')}, status=400)
        if services.User.objects.filter(email=email).exists():
            return JsonResponse({'error': _('این ایمیل قبلا استفاده شده است')}, status=400)
            
        user = services.User.objects.create(
            phone=phone,
            username=username,
            email=email,
            full_name=full_name
        )
        user.set_password(password)
        user.save()
        
        del request.session['verified_phone']
        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        redirect_url = '/accounts/user-info/' if user.has_completed_onboarding else '/selection/'
        return JsonResponse({'message': _('ثبت‌نام با موفقیت انجام شد'), 'redirect_url': redirect_url})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)


@require_POST
def login_password_view(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        password = data.get('password')
        
        if not phone or not password:
            return JsonResponse({'error': _('شماره موبایل معتبر و رمز عبور الزامی است')}, status=400)
            
        user = services.authenticate_user(phone, password)
        
        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            redirect_url = '/accounts/user-info/' if user.has_completed_onboarding else '/selection/'
            return JsonResponse({'message': _('با موفقیت وارد شدید'), 'redirect_url': redirect_url})
        else:
            return JsonResponse({'error': _('شماره موبایل یا رمز عبور اشتباه است')}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

@require_POST
def google_login_view(request):
    try:
        data = json.loads(request.body)
        token = data.get('credential')
        
        if not token:
            return JsonResponse({'error': _('توکن گوگل دریافت نشد.')}, status=400)
            
        user, error_msg = services.verify_google_token(token)
        
        if user:
            if not user.phone:
                request.session['pending_google_email'] = user.email
                return JsonResponse({'needs_google_completion': True, 'email': user.email})
            else:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                redirect_url = '/accounts/user-info/' if user.has_completed_onboarding else '/selection/'
                return JsonResponse({'message': _('با موفقیت وارد شدید'), 'redirect_url': redirect_url})
        else:
            return JsonResponse({'error': error_msg}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

@require_POST
def google_request_otp_view(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        username = data.get('username')
        
        email = request.session.get('pending_google_email')
        if not email:
            return JsonResponse({'error': _('نشست شما منقضی شده است. لطفاً مجدداً تلاش کنید.')}, status=400)
            
        if not phone or not username:
            return JsonResponse({'error': _('تمامی فیلدها الزامی است')}, status=400)
            
        if services.User.objects.filter(phone=phone).exists():
            return JsonResponse({'error': _('این شماره موبایل قبلا استفاده شده است')}, status=400)
            
        if services.User.objects.filter(username=username).exclude(email=email).exists():
            return JsonResponse({'error': _('این نام کاربری قبلا استفاده شده است')}, status=400)
            
        success, message = services.generate_and_send_otp(phone)
        if success:
            request.session['pending_google_phone'] = phone
            request.session['pending_google_username'] = username
            return JsonResponse({'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

@require_POST
def google_verify_otp_view(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        code = data.get('code')
        
        email = request.session.get('pending_google_email')
        session_phone = request.session.get('pending_google_phone')
        session_username = request.session.get('pending_google_username')
        
        if not email or not session_phone or not session_username:
            return JsonResponse({'error': _('نشست شما منقضی شده است. لطفاً مجدداً تلاش کنید.')}, status=400)
            
        if phone != session_phone:
            return JsonResponse({'error': _('شماره موبایل با درخواست اولیه مطابقت ندارد')}, status=400)
            
        user, needs_registration = services.verify_otp_code(phone, code)
        
        if needs_registration:
            try:
                user = services.User.objects.get(email=email)
                user.phone = phone
                user.username = session_username
                user.save()
                
                del request.session['pending_google_email']
                del request.session['pending_google_phone']
                del request.session['pending_google_username']
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                redirect_url = '/accounts/user-info/' if user.has_completed_onboarding else '/selection/'
                return JsonResponse({'message': _('ثبت‌نام با موفقیت تکمیل شد'), 'redirect_url': redirect_url})
            except services.User.DoesNotExist:
                return JsonResponse({'error': _('کاربر یافت نشد')}, status=400)
        elif user:
            return JsonResponse({'error': _('این شماره موبایل متعلق به حساب دیگری است.')}, status=400)
        else:
            return JsonResponse({'error': _('کد تایید نامعتبر است یا منقضی شده')}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

def forgot_password_page_view(request):
    return render(request, 'accounts/auth/forgot.html')

@require_POST
def api_forgot_password_request(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        
        if not phone:
            return JsonResponse({'error': _('شماره موبایل الزامی است')}, status=400)
            
        if not services.User.objects.filter(phone=phone).exists():
            return JsonResponse({'error': _('حسابی با این شماره یافت نشد.')}, status=400)
            
        success, message = services.generate_and_send_otp(phone)
        if success:
            request.session['forgot_phone'] = phone
            return JsonResponse({'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

@require_POST
def api_forgot_password_verify(request):
    try:
        data = json.loads(request.body)
        phone = services.normalize_phone(data.get('phone'))
        code = data.get('code')
        
        session_phone = request.session.get('forgot_phone')
        
        if not session_phone or session_phone != phone:
            return JsonResponse({'error': _('نشست نامعتبر است. لطفاً مجدداً تلاش کنید.')}, status=400)
            
        user, needs_registration = services.verify_otp_code(phone, code)
        
        if user:
            # Code is valid and user exists
            request.session['forgot_verified_phone'] = phone
            return JsonResponse({'needs_new_password': True})
        else:
            return JsonResponse({'error': _('کد تایید نامعتبر است یا منقضی شده')}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)

@require_POST
def api_forgot_password_reset(request):
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        verified_phone = request.session.get('forgot_verified_phone')
        if not verified_phone:
            return JsonResponse({'error': _('نشست منقضی شده است. لطفا مجدد تلاش کنید.')}, status=400)
            
        if not password or len(password) < 6:
            return JsonResponse({'error': _('رمز عبور باید حداقل ۶ کاراکتر باشد')}, status=400)
            
        try:
            user = services.User.objects.get(phone=verified_phone)
            user.set_password(password)
            user.save()
            
            # Login user automatically
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Cleanup session
            if 'forgot_phone' in request.session:
                del request.session['forgot_phone']
            if 'forgot_verified_phone' in request.session:
                del request.session['forgot_verified_phone']
                
            return JsonResponse({'message': _('رمز عبور با موفقیت تغییر یافت'), 'redirect_url': '/accounts/user-info/'})
            
        except services.User.DoesNotExist:
            return JsonResponse({'error': _('کاربر یافت نشد')}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)
