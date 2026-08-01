from django.shortcuts import redirect
from django.utils import translation
from core.models import SiteLanguage


def get_localized_url(path, lang, default_lang='fa'):
    for code in ['en', 'ar', 'ru', 'tr', 'fa']:
        if path == f'/{code}/' or path.startswith(f'/{code}/'):
            path = path[len(code) + 1:]
            if not path.startswith('/'):
                path = '/' + path
            break

    if lang == default_lang:
        return path
    else:
        return f'/{lang}{path}' if path.startswith('/') else f'/{lang}/{path}'


class SmartLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        active_codes = list(SiteLanguage.objects.filter(is_active=True).values_list('code', flat=True))
        if not active_codes:
            active_codes = ['fa', 'en', 'ar', 'ru', 'tr']

        path = request.path
        lang = None

        # 0. Check explicit URL path prefix first (e.g. /en/..., /ar/..., /ru/..., /tr/...)
        for code in active_codes:
            if code != 'fa' and (path == f'/{code}/' or path.startswith(f'/{code}/')):
                lang = code
                break

        # 1. If user is authenticated and no explicit URL prefix override
        if not lang and request.user.is_authenticated and hasattr(request.user, 'preferred_language'):
            user_lang = request.user.preferred_language
            if user_lang and user_lang in active_codes:
                lang = user_lang

        # 2. Check session
        if not lang or lang not in active_codes:
            session_lang = request.session.get('django_language')
            if session_lang in active_codes:
                lang = session_lang

        # 3. First time visitor detection (IP Country check)
        if not lang or lang not in active_codes:
            country = (
                request.META.get('HTTP_CF_IPCOUNTRY') or
                request.META.get('GEOIP_COUNTRY_CODE') or
                request.META.get('HTTP_X_GEOIP_COUNTRY') or
                ''
            ).upper()

            if not country:
                try:
                    from django.contrib.gis.geoip2 import GeoIP2
                    g = GeoIP2()
                    raw_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
                    client_ip = raw_ip.split(',')[0].strip() if raw_ip else ''
                    if client_ip:
                        country = g.country_code(client_ip).upper()
                except Exception:
                    pass

            if country:
                if country == 'IR' and 'fa' in active_codes:
                    lang = 'fa'
                elif country in ['SA', 'AE', 'KW', 'QA', 'BH', 'OM', 'IQ', 'EG'] and 'ar' in active_codes:
                    lang = 'ar'
                elif country in ['RU', 'BY', 'KZ'] and 'ru' in active_codes:
                    lang = 'ru'
                elif country == 'TR' and 'tr' in active_codes:
                    lang = 'tr'
                elif country in ['US', 'GB', 'CA', 'AU', 'NZ', 'IE'] and 'en' in active_codes:
                    lang = 'en'

        # 4. Default site fallback (Persian 'fa')
        if not lang or lang not in active_codes:
            lang = 'fa'

        # Update session and user preference if authenticated
        request.session['django_language'] = lang
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        if request.user.is_authenticated and hasattr(request.user, 'preferred_language'):
            if request.user.preferred_language != lang:
                try:
                    request.user.preferred_language = lang
                    request.user.save(update_fields=['preferred_language'])
                except Exception:
                    pass

        # Align URL prefix for GET HTML requests
        exempt_prefixes = ['/admin/', '/static/', '/media/', '/i18n/', '/rosetta/']
        is_exempt = any(path.startswith(ep) or '/api/' in path for ep in exempt_prefixes)

        if request.method == 'GET' and not is_exempt:
            target_url = get_localized_url(path, lang)
            if target_url != path:
                return redirect(target_url)

        response = self.get_response(request)
        return response


class OnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            exempt_paths = [
                '/selection/',
                '/accounts/logout/',
                '/admin/',
                '/static/',
                '/media/',
                '/api/',
            ]

            path = request.path
            is_exempt = any(path.startswith(ep) for ep in exempt_paths)

            if not is_exempt and not getattr(request.user, 'has_completed_onboarding', True):
                import urllib.parse
                full_path = request.get_full_path()
                return redirect(f'/selection/?next={urllib.parse.quote(full_path)}')

        response = self.get_response(request)
        return response


def parse_device_name(user_agent):
    if not user_agent:
        return "Windows Chrome"
    ua = user_agent.lower()
    
    os_name = "Windows"
    if "iphone" in ua:
        os_name = "iPhone"
    elif "ipad" in ua:
        os_name = "iPad"
    elif "android" in ua:
        os_name = "Android"
    elif "macintosh" in ua or "mac os" in ua:
        os_name = "Mac"
    elif "linux" in ua:
        os_name = "Linux"
    elif "windows" in ua:
        os_name = "Windows"

    browser_name = "Chrome"
    if "edg" in ua:
        browser_name = "Edge"
    elif "chrome" in ua:
        browser_name = "Chrome"
    elif "safari" in ua and "chrome" not in ua:
        browser_name = "Safari"
    elif "firefox" in ua:
        browser_name = "Firefox"
    elif "opera" in ua or "opr" in ua:
        browser_name = "Opera"

    return f"{os_name} {browser_name}"


class DeviceTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.session.session_key:
            import time
            now = time.time()
            last_track = request.session.get('_last_device_track_ts', 0)

            # Skip DB completely if checked within the last 5 minutes (300 seconds)
            if now - last_track < 300:
                return response

            try:
                from .models import UserDevice
                from django.utils import timezone

                session_key = request.session.session_key
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                device_name = parse_device_name(user_agent)

                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0].strip()
                else:
                    ip = request.META.get('REMOTE_ADDR')

                device = UserDevice.objects.filter(user=request.user, session_key=session_key).first()
                if not device:
                    device = UserDevice.objects.filter(user=request.user, device_name=device_name, ip_address=ip).order_by('-last_activity').first()

                if device:
                    device.session_key = session_key
                    device.device_name = device_name
                    device.ip_address = ip
                    device.last_activity = timezone.now()
                    device.save()
                else:
                    UserDevice.objects.create(
                        user=request.user,
                        session_key=session_key,
                        device_name=device_name,
                        ip_address=ip,
                        last_activity=timezone.now()
                    )

                request.session['_last_device_track_ts'] = now
            except Exception:
                pass

        return response

