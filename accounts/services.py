from django.utils.translation import gettext as _
from django.utils import translation
import random
import logging
import re
from django.core.cache import cache
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import User, Notification
from django.utils import timezone
from subscriptions.models import Subscription
from core.models import DashboardSetting, ProfileImage, FooterSetting

logger = logging.getLogger(__name__)

def normalize_phone(phone):
    if not phone:
        return None
    phone = str(phone).strip()
    if re.match(r'^9\d{9}$', phone):
        return '0' + phone
    if re.match(r'^09\d{9}$', phone):
        return phone
    return None

def check_user_status(phone):
    """
    Checks if a user exists with the given phone number,
    and whether they have a usable password set.
    """
    try:
        user = User.objects.get(phone=phone)
        return {
            "exists": True,
            "has_password": user.has_usable_password()
        }
    except User.DoesNotExist:
        return {
            "exists": False,
            "has_password": False
        }

def generate_and_send_otp(phone):
    """
    Generates a 6-digit OTP, stores it in the cache for 2 minutes,
    and sends an SMS via MeliPayamak pattern service.
    Prevents sending multiple SMS within the 2-minute window.
    """
    cache_key = f"otp_{phone}"
    
    # Check if an active OTP already exists
    if cache.get(cache_key):
        return False, _("کد تایید قبلاً برای شما ارسال شده است. لطفاً ۲ دقیقه صبر کنید.")
        
    otp_code = f"{random.randint(100000, 999999)}"
    
    # Send SMS via MeliPayamak pattern
    from core.sms import send_sms_pattern
    sms_success, sms_result = send_sms_pattern(to=phone, text=otp_code)
    
    if not sms_success:
        logger.error(f"Failed to send OTP SMS to {phone}: {sms_result}")
        return False, _("خطا در ارسال پیامک کد تایید. لطفاً دوباره تلاش کنید.")
    
    # Store OTP in cache for 120 seconds (2 minutes)
    cache.set(cache_key, otp_code, timeout=120)
    
    logger.info(f"Generated and sent OTP {otp_code} for phone {phone}")
    
    return True, _("کد تایید با موفقیت ارسال شد")

def verify_otp_code(phone, code):
    """
    Verifies the provided OTP code. If valid, checks if user exists.
    Returns (user, needs_registration).
    """
    cache_key = f"otp_{phone}"
    cached_code = cache.get(cache_key)
    
    if cached_code and str(cached_code) == str(code):
        # Code is valid, remove it from cache
        cache.delete(cache_key)
        
        try:
            user = User.objects.get(phone=phone)
            return user, False
        except User.DoesNotExist:
            # Valid code, but user doesn't exist
            return None, True
            
    return None, False

def authenticate_user(phone, password):
    """
    Authenticates a user via phone and password.
    AbstractUser typically logs in with username, but since we set username=phone
    during OTP registration (or if they changed it, we might need a custom backend).
    Wait, let's look up user by phone and then check password.
    """
    try:
        user = User.objects.get(phone=phone)
        if user.check_password(password):
            return user
    except User.DoesNotExist:
        pass
    
    return None

import requests

def verify_google_token(token):
    """
    Verifies Google Access Token and gets/creates a user with the provided email.
    """
    try:
        response = requests.get(f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={token}")
        if response.status_code != 200:
            logger.error(f"Google UserInfo failed: {response.text}")
            return None, _("توکن گوگل نامعتبر است.")
            
        user_info = response.json()
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        if not email:
            return None, _("ایمیل در اطلاعات حساب گوگل یافت نشد.")
            
        # Try to find user by email
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.username = email
            user.full_name = name
            user.set_unusable_password()
            user.save()
            
        return user, None
        
    except Exception as e:
        logger.error(f"Google Login error: {e}")
        return None, _("خطا در ارتباط با سرورهای گوگل.")

def get_user_dashboard_info(user):
    active_sub = Subscription.objects.filter(user=user, is_active=True, end_date__gte=timezone.now()).first()
    
    return {
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "user_number": user.user_number,
        "date_joined": user.date_joined,
        "avatar": user.avatar.url if user.avatar else None,
        "has_active_subscription": bool(active_sub),
        "subscription_name": active_sub.plan.name if active_sub and active_sub.plan else None,
        "subscription_end_date": active_sub.end_date if active_sub else None,
    }

def get_default_avatars():
    setting = DashboardSetting.objects.first()
    if setting:
        return setting.default_avatars.all()
    return []

def update_user_username_and_avatar(user, username=None, email=None, avatar_file=None, default_avatar_id=None):
    updated = False
    if username and username != user.username:
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            return False, _("این نام کاربری قبلاً استفاده شده است.")
        user.username = username
        updated = True
        
    if email and email != user.email:
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            return False, _("این ایمیل قبلاً استفاده شده است.")
        user.email = email
        updated = True
        
    if avatar_file:
        user.avatar = avatar_file
        updated = True
    elif default_avatar_id:
        try:
            profile_img = ProfileImage.objects.get(id=default_avatar_id)
            user.avatar = profile_img.image.name
            updated = True
        except ProfileImage.DoesNotExist:
            pass

    if updated:
        user.save()
        return True, _("پروفایل با موفقیت بروزرسانی شد.")
    return False, _("تغییری اعمال نشد.")

def get_social_medias():
    setting = FooterSetting.objects.first()
    if setting:
        return setting.social_medias.all()
    return []


def change_user_password(user, old_password, new_password, confirm_password):
    """
    Validates and changes the user's password.
    """
    if user.has_usable_password():
        if not old_password:
            return False, _("لطفاً رمز عبور فعلی را وارد کنید.")
        if not user.check_password(old_password):
            return False, _("رمز عبور فعلی نادرست است.")

    if not new_password:
        return False, _("لطفاً رمز عبور جدید را وارد کنید.")

    if len(new_password) < 6:
        return False, _("رمز عبور جدید باید حداقل ۶ کاراکتر باشد.")

    if new_password != confirm_password:
        return False, _("رمز عبور جدید و تکرار آن یکسان نیستند.")

    user.set_password(new_password)
    user.save()
    return True, _("رمز عبور با موفقیت تغییر یافت.")


def get_user_notifications(user):
    """
    Returns queryset of active notifications excluding those dismissed by the given user.
    """
    return Notification.objects.filter(
        is_active=True
    ).exclude(
        dismissed_users=user
    ).order_by('-created_at')


def get_unread_notifications_count(user):
    """
    Returns count of active, non-dismissed notifications that the user has not read yet.
    """
    if not user or not user.is_authenticated:
        return 0
    return Notification.objects.filter(
        is_active=True
    ).exclude(
        dismissed_users=user
    ).exclude(
        read_users=user
    ).count()


def mark_all_notifications_as_read(user):
    """
    Marks all active, non-dismissed notifications as read for the given user.
    """
    if not user or not user.is_authenticated:
        return
    unread_notifications = Notification.objects.filter(
        is_active=True
    ).exclude(
        dismissed_users=user
    ).exclude(
        read_users=user
    )
    for n in unread_notifications:
        n.read_users.add(user)


def dismiss_user_notification(user, notification_id):
    """
    Dismisses a notification for a user by adding them to dismissed_users.
    """
    try:
        notification = Notification.objects.get(pk=notification_id, is_active=True)
        notification.dismissed_users.add(user)
        return True, _("اعلان بسته‌شد.")
    except Notification.DoesNotExist:
        return False, _("اعلان یافت نشد.")


def update_player_quality(user, quality):
    """
    Updates the user's preferred player quality.
    """
    valid_qualities = ['AUTO', 'VeryHigh', 'High', 'Medium', 'Low']
    if quality not in valid_qualities:
        return False, _("کیفیت انتخاب شده نامعتبر است.")
    user.preferred_quality = quality
    user.save()
    return True, _("کیفیت پخش‌کننده با موفقیت بروزرسانی شد.")


def update_user_language(user, lang_code, session=None):
    """
    Updates the user's preferred language and session/translation.
    """
    from core.models import SiteLanguage
    valid_languages = list(SiteLanguage.objects.filter(is_active=True).values_list('code', flat=True))
    if not valid_languages:
        valid_languages = ['fa', 'en', 'ar', 'ru', 'tr']

    if lang_code not in valid_languages:
        return False, _("زبان انتخاب شده نامعتبر است.")

    user.preferred_language = lang_code
    user.save()

    if session is not None:
        session['django_language'] = lang_code

    translation.activate(lang_code)
    return True, _("زبان با موفقیت بروزرسانی شد.")


def sync_user_language_from_session(user, session):
    """
    Called upon user registration or login to save the session language to the user's profile.
    """
    from core.models import SiteLanguage
    valid_languages = list(SiteLanguage.objects.filter(is_active=True).values_list('code', flat=True))
    if not valid_languages:
        valid_languages = ['fa', 'en', 'ar', 'ru', 'tr']

    if session and 'django_language' in session:
        session_lang = session.get('django_language')
        if session_lang in valid_languages and user.preferred_language != session_lang:
            user.preferred_language = session_lang
            user.save()





