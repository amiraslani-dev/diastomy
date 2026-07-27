from .models import HeaderSetting, FooterSetting, SiteLanguage

def header_settings(request):
    fallback_menu = [
        {'title': 'خانه', 'link': '/'},
        {'title': 'فیلم', 'link': '/movies/'},
        {'title': 'سریال', 'link': '/series/'},
        {'title': 'خارجی', 'link': '/foreign/'},
        {'title': 'تازه‌ها', 'link': '/new/'},
        {'title': 'کودک', 'link': '/kids/'},
    ]
    
    admin_notifications = None
    admin_unread_count = 0
    total_saved_count = 0
    
    if request.user.is_authenticated:
        total_saved_count = request.user.movie_bookmarks.count() + request.user.series_bookmarks.count()
        
        if request.user.is_staff:
            from core.models import AdminNotification
            admin_notifications = AdminNotification.objects.filter(is_read=False)[:10]
            admin_unread_count = AdminNotification.objects.filter(is_read=False).count()

    active_langs = list(SiteLanguage.objects.filter(is_active=True).order_by('order', 'id').values('code', 'name'))
    if not active_langs:
        active_langs = [
            {'code': 'fa', 'name': 'فارسی'},
            {'code': 'en', 'name': 'English'},
            {'code': 'ar', 'name': 'العربیه'},
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'tr', 'name': 'Türkçe'},
        ]
        
    return {
        'header_settings': HeaderSetting.objects.first(),
        'footer_settings': FooterSetting.objects.first(),
        'fallback_menu': fallback_menu,
        'admin_notifications': admin_notifications,
        'admin_unread_count': admin_unread_count,
        'total_saved_count': total_saved_count,
        'site_languages': active_langs,
    }

