from django import template
from django.utils.translation import get_language
from jalali_date import datetime2jalali

register = template.Library()

@register.filter(name='smart_date')
def smart_date(value, format_str="%Y/%m/%d"):
    """
    Returns Jalali (solar) formatted date if current active language is Persian ('fa'),
    otherwise returns Gregorian (Western) formatted date.
    """
    if not value:
        return ""
    
    lang = get_language()
    if lang == 'fa':
        try:
            return datetime2jalali(value).strftime(format_str)
        except Exception:
            return value.strftime(format_str)
    else:
        try:
            clean_format = format_str.replace('،', ',')
            return value.strftime(clean_format)
        except Exception:
            return str(value)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Preserves all existing GET query parameters in URL and updates/adds specified kwargs (e.g. page=num).
    """
    request = context.get('request')
    if not request:
        return ""
    dict_ = request.GET.copy()
    for key, value in kwargs.items():
        dict_[key] = value
    return dict_.urlencode()
