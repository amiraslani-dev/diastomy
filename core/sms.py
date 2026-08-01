import logging
import requests
from django.conf import settings
from melipayamak import Api

logger = logging.getLogger(__name__)


def send_sms_pattern(to: str, text, body_id=None) -> tuple[bool, str]:
    """
    Sends a pattern SMS using MeliPayamak Api SDK (SendByBaseNumber / BaseServiceNumber).
    Used for sending SMS to blacklist numbers via shared service lines.
    """
    username = getattr(settings, "MELIPAYAMAK_USERNAME", "")
    password = getattr(settings, "MELIPAYAMAK_PASSWORD", "")
    body_id = body_id or getattr(settings, "MELIPAYAMAK_OTP_BODY_ID", "")

    # Format text variables if list or tuple
    if isinstance(text, (list, tuple)):
        text_str = ";".join(str(v) for v in text)
    else:
        text_str = str(text)

    if not username or not password or not body_id:
        print(f"\n[SMS MOCK] To: {to} | Code: {text_str} | BodyID: {body_id}\n")
        return True, "Simulated SMS send"

    try:
        # Method 1: Using MeliPayamak SDK (BaseServiceNumber)
        api = Api(username, password)
        sms_rest = api.sms()
        response = sms_rest.send_by_base_number(text_str, str(to), str(body_id))

        print(f"\n--- MeliPayamak SDK Response ---")
        print(f"Target: {to} | BodyID: {body_id} | Text: {text_str}")
        print(f"Response: {response}\n-----------------------------------\n")

        logger.info(f"MeliPayamak SMS response for {to}: {response}")

        if isinstance(response, dict):
            val = str(response.get("Value", ""))
            return True, val
        return True, str(response)

    except Exception as e:
        logger.error(
            f"Error using MeliPayamak SDK for {to}: {e}, attempting HTTP ASMX fallback..."
        )

        # Method 2: Direct HTTP ASMX fallback (SendByBaseNumber2)
        try:
            url = "http://api.payamak-panel.com/post/Send.asmx/SendByBaseNumber2"
            payload = {
                "username": username,
                "password": password,
                "text": text_str,
                "to": str(to),
                "bodyId": str(body_id),
            }
            res = requests.post(url, data=payload, timeout=10)
            val = res.text
            if "<string" in val:
                val = val.split(">")[1].split("<")[0]
            val = val.strip()
            print(f"[ASMX Fallback Response]: {val}")
            return True, val
        except Exception as fallback_err:
            logger.error(f"ASMX fallback error for {to}: {fallback_err}")
            return False, str(e)
