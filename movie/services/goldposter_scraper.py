"""
goldposter_scraper.py
----------------------
دریافت پوستر فیلم/سریال از goldposter.com بر اساس IMDb ID (مثل tt1375666).

⚠️ نکته‌ی مهم قبل از استفاده:
هنگام تست این روش (GET ساده به /search-goldposter/?search=...) با چند IMDb ID
مختلف، همه‌شون به یک صفحه‌ی ثابت (Inception) ریدایرکت شدن. این نشون می‌ده که
پردازش واقعی سرچ احتمالاً سمت کلاینت (جاوااسکریپت/AJAX) انجام می‌شه، نه سرور.

به همین دلیل این اسکریپت یک لایه‌ی "تأیید" اضافه داره: بعد از رسیدن به صفحه‌ی
فیلم، چک می‌کنه که IMDb ID توی خود صفحه با ورودی مطابقت داره یا نه. اگه مطابقت
نداشت، یعنی این روش برای اون ID کار نکرده و باید endpoint واقعی سرچ (که با
DevTools مرورگر، تب Network، پیدا می‌شه) جایگزینش بشه.

نصب پیش‌نیاز:
    pip install requests beautifulsoup4
"""

import re
import sys
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.goldposter.com"
SEARCH_URL = f"{BASE_URL}/search-goldposter/"

HEADERS = {
    # بعضی سایت‌ها درخواست‌های بدون User-Agent مرورگر رو بلاک یا متفاوت هندل می‌کنن
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

IMDB_ID_RE = re.compile(r"tt\d{7,9}")


@dataclass
class PosterResult:
    imdb_id: str
    found: bool
    title: str | None = None
    poster_url: str | None = None
    movie_page_url: str | None = None
    verified: bool = False  # True یعنی IMDb ID روی صفحه با ورودی مطابقت داره
    note: str = ""


def _clean_image_url(raw_url: str) -> str:
    """حذف کوئری‌استرینگ ریسایز/فرمت (?x-oss-process=...) از URL تصویر."""
    return raw_url.split("?")[0]


def get_poster_by_imdb_id(imdb_id: str, session: requests.Session | None = None) -> PosterResult:
    if not IMDB_ID_RE.fullmatch(imdb_id):
        return PosterResult(imdb_id, found=False, note="فرمت IMDb ID نامعتبره (باید مثل tt1375666 باشه)")

    sess = session or requests.Session()

    try:
        resp = sess.get(
            SEARCH_URL,
            params={"search": imdb_id},
            headers=HEADERS,
            allow_redirects=True,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return PosterResult(imdb_id, found=False, note=f"خطای شبکه: {e}")

    final_url = resp.url

    # اگه ریدایرکت نشده باشه به /movie/<id>/ یعنی احتمالاً چیزی پیدا نشده
    if "/movie/" not in final_url:
        return PosterResult(
            imdb_id, found=False, movie_page_url=final_url,
            note="ریدایرکت به صفحه‌ی فیلم انجام نشد؛ احتمالاً موردی پیدا نشده یا سرچ واقعی سمت جاوااسکریپته."
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    # ۱) تلاش برای گرفتن پوستر از og:image (تمیزترین راه)
    og_image = soup.find("meta", property="og:image")
    poster_url = _clean_image_url(og_image["content"]) if og_image and og_image.get("content") else None

    # ۲) fallback: تگ <img> داخل لینک mediaviewer
    if not poster_url:
        img_tag = soup.select_one('a[href*="mediaviewer"] img')
        if img_tag and img_tag.get("src"):
            poster_url = _clean_image_url(urljoin(BASE_URL, img_tag["src"]))

    # عنوان فیلم/سریال
    title_tag = soup.find("meta", property="og:title")
    title = title_tag["content"].split("|")[0].strip() if title_tag and title_tag.get("content") else None

    # ۳) تأیید صحت: IMDb ID واقعی توی صفحه با ورودی یکی هست؟
    page_text = soup.get_text(" ", strip=True)
    imdb_on_page_match = re.search(r"IMDB:\s*(tt\d{7,9})", page_text)
    imdb_on_page = imdb_on_page_match.group(1) if imdb_on_page_match else None
    verified = (imdb_on_page == imdb_id)

    note = ""
    if not verified:
        note = (
            f"⚠️ IMDb ID روی صفحه ({imdb_on_page}) با ورودی ({imdb_id}) یکی نیست. "
            "یعنی این نتیجه احتمالاً غلطه و سرچ واقعی انجام نشده "
            "(به‌احتمال زیاد باید endpoint واقعی AJAX سایت رو پیدا کنی)."
        )

    return PosterResult(
        imdb_id=imdb_id,
        found=poster_url is not None,
        title=title,
        poster_url=poster_url,
        movie_page_url=final_url,
        verified=verified,
        note=note,
    )


def get_poster_by_imdb_id_playwright(imdb_id: str, headless: bool = True) -> PosterResult:
    """
    نسخه‌ی جایگزین با هدلس براوزر واقعی (Playwright).
    فقط در صورتی لازمه که نسخه‌ی requests بالا همیشه یک نتیجه‌ی ثابت/غلط برگردونه
    (نشونه‌ی اینکه سرچ واقعاً به اجرای جاوااسکریپت یا عبور از آنتی‌بات نیاز داره).

    نصب پیش‌نیاز:
        pip install playwright
        playwright install chromium
    """
    from playwright.sync_api import sync_playwright

    if not IMDB_ID_RE.fullmatch(imdb_id):
        return PosterResult(imdb_id, found=False, note="فرمت IMDb ID نامعتبره")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        try:
            page.goto(f"{SEARCH_URL}?search={imdb_id}", wait_until="networkidle", timeout=20000)
            # اگه سایت واقعاً کلاینت‌ساید ریدایرکت می‌کنه، چند ثانیه صبر می‌کنیم تا URL عوض بشه
            page.wait_for_timeout(2000)

            final_url = page.url
            html = page.content()
        finally:
            browser.close()

    if "/movie/" not in final_url:
        return PosterResult(imdb_id, found=False, movie_page_url=final_url, note="ریدایرکت به صفحه‌ی فیلم انجام نشد.")

    soup = BeautifulSoup(html, "html.parser")
    og_image = soup.find("meta", property="og:image")
    poster_url = _clean_image_url(og_image["content"]) if og_image and og_image.get("content") else None

    title_tag = soup.find("meta", property="og:title")
    title = title_tag["content"].split("|")[0].strip() if title_tag and title_tag.get("content") else None

    page_text = soup.get_text(" ", strip=True)
    imdb_on_page_match = re.search(r"IMDB:\s*(tt\d{7,9})", page_text)
    imdb_on_page = imdb_on_page_match.group(1) if imdb_on_page_match else None
    verified = (imdb_on_page == imdb_id)

    return PosterResult(
        imdb_id=imdb_id,
        found=poster_url is not None,
        title=title,
        poster_url=poster_url,
        movie_page_url=final_url,
        verified=verified,
        note="" if verified else f"⚠️ IMDb ID صفحه ({imdb_on_page}) با ورودی یکی نیست.",
    )


if __name__ == "__main__":
    test_ids = sys.argv[1:] or ["tt1375666", "tt0111161", "tt0944947"]

    print("### تست با requests ###")
    with requests.Session() as s:
        for imdb_id in test_ids:
            result = get_poster_by_imdb_id(imdb_id, session=s)
            print(f"\n=== {imdb_id} ===")
            print(f"پیدا شد: {result.found} | تأیید شده: {result.verified}")
            if result.title:
                print(f"عنوان: {result.title}")
            if result.poster_url:
                print(f"پوستر: {result.poster_url}")
            if result.movie_page_url:
                print(f"صفحه: {result.movie_page_url}")
            if result.note:
                print(result.note)

    # اگه بالا برای همه‌ی IDها یک نتیجه‌ی ثابت/verified=False گرفتی، این بخش رو با
    # کامنت‌برداری فعال کن (نیاز به نصب playwright داره):
    #
    # print("\n### تست با Playwright ###")
    # for imdb_id in test_ids:
    #     result = get_poster_by_imdb_id_playwright(imdb_id)
    #     print(f"\n=== {imdb_id} ===")
    #     print(f"پیدا شد: {result.found} | تأیید شده: {result.verified}")
    #     if result.poster_url:
    #         print(f"پوستر: {result.poster_url}")
    #     if result.note:
    #         print(result.note)
