from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import NewsletterSubscriber

def subscribe_newsletter(email: str):
    """
    Subscribes an email address to the newsletter.
    Returns (success: bool, message: str)
    """
    if not email:
        return False, _("لطفاً آدرس ایمیل خود را وارد کنید.")
    
    email = email.strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return False, _("لطفاً یک آدرس ایمیل معتبر وارد کنید.")

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={'is_active': True}
    )

    if not created:
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=['is_active'])
            return True, _("ایمیل شما مجدداً در خبرنامه فعال گردید.")
        return True, _("ایمیل شما قبلاً در خبرنامه ثبت شده است.")

    return True, _("ایمیل شما با موفقیت در خبرنامه ثبت گردید.")
