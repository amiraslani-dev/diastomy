from django.utils.translation import gettext as _
import random
import logging
import re
from django.core.cache import cache
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import User

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
    and simulates sending an SMS.
    Prevents sending multiple SMS within the 2-minute window.
    """
    cache_key = f"otp_{phone}"
    
    # Check if an active OTP already exists
    if cache.get(cache_key):
        return False, _("کد تایید قبلاً برای شما ارسال شده است. لطفاً ۲ دقیقه صبر کنید.")
        
    otp_code = f"{random.randint(100000, 999999)}"
    
    # Store OTP in cache for 120 seconds (2 minutes)
    cache.set(cache_key, otp_code, timeout=120)
    
    # TODO: Integrate real SMS provider here (e.g., Kavenegar)
    print(f"\n{'='*40}")
    print(f"SMS Service - To: {phone}")
    print(f"Your login code is: {otp_code}")
    print(f"{'='*40}\n")
    logger.info(f"Generated OTP {otp_code} for phone {phone}")
    
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
