from django.utils.translation import gettext as _, get_language
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification, UserDevice
from . import services

import urllib.parse

def get_redirect_url(request, user, default_onboarding_url='/selection/', default_user_url='/accounts/user-info/'):
    next_url = request.GET.get('next') or request.POST.get('next')
    if not next_url and request.body:
        try:
            body_data = json.loads(request.body)
            next_url = body_data.get('next')
        except Exception:
            pass
            
    valid_next = next_url if (next_url and next_url.startswith('/') and not next_url.startswith('//')) else None

    if not user.has_completed_onboarding:
        if valid_next:
            return f"/selection/?next={urllib.parse.quote(valid_next)}"
        return default_onboarding_url

    if valid_next:
        return valid_next

    return default_user_url

def login_view(request):
    if request.user.is_authenticated:
        next_url = request.GET.get('next')
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
        return redirect('/accounts/user-info/')
    
    context = {
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID_HERE')
    }
    return render(request, 'accounts/auth/login.html', context)

@login_required
def user_info_view(request):
    dashboard_info = services.get_user_dashboard_info(request.user)
    default_avatars = services.get_default_avatars()
    social_medias = services.get_social_medias()
    
    return render(request, 'accounts/user-info.html', {
        'active_tab': 'user-info',
        'dashboard_info': dashboard_info,
        'default_avatars': default_avatars,
        'social_medias': social_medias,
    })

@login_required
@require_POST
def api_update_profile_view(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            default_avatar_id = data.get('default_avatar_id')
            avatar_file = None
        else:
            username = request.POST.get('username')
            email = request.POST.get('email')
            default_avatar_id = request.POST.get('default_avatar_id')
            avatar_file = request.FILES.get('avatar')

        success, message = services.update_user_username_and_avatar(
            request.user, 
            username=username,
            email=email,
            avatar_file=avatar_file, 
            default_avatar_id=default_avatar_id
        )

        if success:
            return JsonResponse({'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
    except Exception as e:
        return JsonResponse({'error': _("خطای سرور")}, status=500)

def logout_view(request):
    if request.user.is_authenticated:
        current_key = request.session.session_key
        if current_key:
            UserDevice.objects.filter(user=request.user, session_key=current_key).delete()
        logout(request)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'message': _('با موفقیت از حساب کاربری خارج شدید.')})

    return redirect('accounts:login')


def api_logout_view(request):
    """REST API endpoint for logout for mobile apps and API clients."""
    if request.user.is_authenticated:
        current_key = request.session.session_key
        if current_key:
            UserDevice.objects.filter(user=request.user, session_key=current_key).delete()
        logout(request)
    return JsonResponse({'success': True, 'message': _('با موفقیت از حساب کاربری خارج شدید.')})

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


@login_required
def notifications_view(request):
    notifications_list = services.get_user_notifications(request.user)

    # Get list of unread notification IDs before marking as read to highlight new ones in template
    unread_ids = list(notifications_list.exclude(read_users=request.user).values_list('id', flat=True))

    # Mark all unread notifications as read for this user
    services.mark_all_notifications_as_read(request.user)

    total_count = notifications_list.count()

    paginator = Paginator(notifications_list, 20)  # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_tab': 'notifications',
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'unread_ids': unread_ids,
        'total_count': total_count,
    }
    return render(request, 'accounts/notifications.html', context)


@login_required
@require_POST
def dismiss_notification_view(request, pk):
    success, message = services.dismiss_user_notification(request.user, pk)
    if success:
        return JsonResponse({'success': True, 'message': message})
    return JsonResponse({'error': message}, status=404)


@login_required
def api_notifications_list_view(request):
    notifications = services.get_user_notifications(request.user)
    read_ids = set(request.user.read_notifications.values_list('id', flat=True))
    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.id in read_ids,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    unread_count = services.get_unread_notifications_count(request.user)
    return JsonResponse({
        'success': True,
        'count': len(data),
        'unread_count': unread_count,
        'notifications': data
    })


@login_required
@require_POST
def api_mark_notifications_read_view(request):
    services.mark_all_notifications_as_read(request.user)
    return JsonResponse({'success': True, 'message': _('تمام اعلان‌ها با موفقیت به عنوان خوانده‌شده علامت‌گذاری شدند.')})



from jalali_date import datetime2jalali

@login_required
def settings_view(request):
    current_key = request.session.session_key

    # Deduplicate old duplicate device entries for current user
    all_user_devices = UserDevice.objects.filter(user=request.user).order_by('-last_activity')
    seen = set()
    devices = []
    to_delete_ids = []

    for d in all_user_devices:
        combo = (d.device_name, d.ip_address)
        if combo in seen and d.session_key != current_key:
            to_delete_ids.append(d.id)
        else:
            seen.add(combo)
            devices.append(d)

    if to_delete_ids:
        UserDevice.objects.filter(id__in=to_delete_ids).delete()

    active_devices = []
    current_lang = get_language()
    for d in devices:
        if current_lang == 'fa':
            formatted_time = datetime2jalali(d.last_activity).strftime('%Y/%m/%d ، %H:%M:%S') if d.last_activity else ''
        else:
            formatted_time = d.last_activity.strftime('%Y-%m-%d %H:%M:%S') if d.last_activity else ''

        active_devices.append({
            'id': d.id,
            'device_name': d.device_name,
            'ip_address': d.ip_address,
            'last_activity': formatted_time,
            'is_current': (d.session_key == current_key),
        })

    return render(request, 'accounts/settings.html', {
        'active_tab': 'settings',
        'active_devices': active_devices,
    })


@login_required
@require_POST
def api_terminate_device_view(request, pk):
    try:
        device = get_object_or_404(UserDevice, pk=pk, user=request.user)
        from django.contrib.sessions.models import Session
        Session.objects.filter(session_key=device.session_key).delete()
        device.delete()
        return JsonResponse({'success': True, 'message': _('نشست دستگاه با موفقیت خاتمه یافت.')})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_terminate_other_devices_view(request):
    try:
        current_key = request.session.session_key
        other_devices = UserDevice.objects.filter(user=request.user).exclude(session_key=current_key)
        other_keys = list(other_devices.values_list('session_key', flat=True))
        from django.contrib.sessions.models import Session
        Session.objects.filter(session_key__in=other_keys).delete()
        other_devices.delete()
        return JsonResponse({'success': True, 'message': _('تمام نشست‌های غیرفعلی با موفقیت خاتمه یافتند.')})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
@require_POST
def api_change_password_view(request):
    try:
        data = json.loads(request.body)
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')

        success, message = services.change_user_password(
            request.user, old_password, new_password, confirm_password
        )
        if success:
            update_session_auth_hash(request, request.user)
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'error': message}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_update_player_quality_view(request):
    try:
        data = json.loads(request.body)
        quality = data.get('quality', 'AUTO')
        success, message = services.update_player_quality(request.user, quality)
        if success:
            return JsonResponse({'success': True, 'message': message, 'quality': request.user.preferred_quality})
        return JsonResponse({'error': message}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_set_language_view(request):
    try:
        data = json.loads(request.body)
        lang_code = data.get('language', 'fa')
        success, message = services.update_user_language(request.user, lang_code, request.session)
        if success:
            referer = request.META.get('HTTP_REFERER', '/')
            try:
                from accounts.middleware import get_localized_url
                from urllib.parse import urlparse
                path = urlparse(referer).path or '/'
                redirect_url = get_localized_url(path, lang_code)
            except Exception:
                redirect_url = '/'
            return JsonResponse({'success': True, 'message': message, 'language': request.user.preferred_language, 'redirect_url': redirect_url})
        return JsonResponse({'error': message}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': _('داده‌های نامعتبر')}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




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
            redirect_url = get_redirect_url(request, user)
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
        redirect_url = get_redirect_url(request, user)
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
            redirect_url = get_redirect_url(request, user)
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
                redirect_url = get_redirect_url(request, user)
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
                redirect_url = get_redirect_url(request, user)
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
