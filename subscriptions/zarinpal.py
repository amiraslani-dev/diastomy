from django.conf import settings
from zarinpal import ZarinPal


class Config:
    def __init__(self, sandbox=True, merchant_id=None, access_token=None):
        self.sandbox = getattr(settings, 'ZARINPAL_SANDBOX', sandbox)
        self.merchant_id = merchant_id or getattr(settings, 'ZARINPAL_MERCHANT_ID', 'Your merchant code')
        self.access_token = access_token or getattr(settings, 'ZARINPAL_ACCESS_TOKEN', 'your-access-token')


def create_payment_request(amount, description, callback_url, mobile=None, email=None):
    """
    Sends payment request using ZarinPal SDK and returns (success, message, authority, payment_url).
    """
    try:
        config = Config()
        zarinpal = ZarinPal(config)

        data = {
            "amount": int(amount),
            "description": description,
            "callback_url": callback_url,
        }
        if mobile:
            data["mobile"] = str(mobile)
        if email:
            data["email"] = str(email)

        response = zarinpal.payments.create(data)

        if isinstance(response, dict) and "data" in response and "authority" in response["data"]:
            authority = response["data"]["authority"]
            payment_url = zarinpal.payments.generate_payment_url(authority)
            return True, "درخواست پرداخت با موفقیت ایجاد شد", authority, payment_url
        else:
            errors = response.get("errors", "خطا در پاسخ زرین‌پال") if isinstance(response, dict) else str(response)
            return False, f"خطا در ایجاد درگاه: {errors}", None, None
    except Exception as e:
        return False, f"خطا هنگام ایجاد درخواست پرداخت: {str(e)}", None, None


def verify_payment_request(authority, amount):
    """
    Verifies payment with ZarinPal SDK using authority & amount.
    Returns (success, message, ref_id, card_pan).
    """
    try:
        config = Config()
        zarinpal = ZarinPal(config)

        data = {
            "authority": str(authority),
            "amount": int(amount),
        }
        response = zarinpal.verifications.verify(data)

        if isinstance(response, dict) and "data" in response:
            code = response["data"].get("code")
            ref_id = response["data"].get("ref_id")
            card_pan = response["data"].get("card_pan")

            if code == 100:
                return True, "تراکنش با موفقیت تایید شد", ref_id, card_pan
            elif code == 101:
                return True, "تراکنش قبلاً تایید شده است", ref_id, card_pan
            else:
                return False, f"تراکنش ناموفق بود (کد: {code})", None, None
        else:
            errors = response.get("errors", "خطا در پاسخ زرین‌پال") if isinstance(response, dict) else str(response)
            return False, f"خطا در تایید تراکنش: {errors}", None, None
    except Exception as e:
        return False, f"خطا هنگام تایید تراکنش: {str(e)}", None, None
