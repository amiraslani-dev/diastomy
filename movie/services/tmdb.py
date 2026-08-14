import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor


from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from bs4 import BeautifulSoup
from django.db.models import Q

from movie.models import Movie, Series, Person, Genre, Country, ContentIngestion




class TMDBServiceError(Exception):
    """Custom exception for TMDB Service errors."""
    pass


class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t5/p/original"
    BANNER_BASE_URL = "https://image.tmdb.org/t5/p/original"


    OVERRIDE_LOCALES = {
        'fa': 'fa-IR',
        'en': 'en-US',
        'ar': 'ar-SA',
        'ru': 'ru-RU',
        'tr': 'tr-TR',
        'zh': 'zh-CN',
        'ja': 'ja-JP',
        'ko': 'ko-KR',
        'pt': 'pt-BR',
        'de': 'de-DE',
        'fr': 'fr-FR',
        'es': 'es-ES',
        'it': 'it-IT',
    }

    def get_languages_map(self):
        """Dynamically fetch supported languages from Django settings (MODELTRANSLATION_LANGUAGES or LANGUAGES)"""
        model_langs = getattr(settings, 'MODELTRANSLATION_LANGUAGES', None)
        if not model_langs and hasattr(settings, 'LANGUAGES'):
            model_langs = [code for code, _ in settings.LANGUAGES]
        if not model_langs:
            model_langs = ['fa', 'en']

        lang_map = {}
        for lang in model_langs:
            code = str(lang).lower().strip()
            tmdb_locale = self.OVERRIDE_LOCALES.get(code, f"{code}-{code.upper()}")
            lang_map[code] = tmdb_locale

        return lang_map


    COUNTRY_MAP = {
        'US': {'fa': 'آمریکا', 'en': 'United States', 'ar': 'الولايات المتحدة', 'ru': 'США', 'tr': 'Amerika Birleşik Devletleri'},
        'GB': {'fa': 'بریتانیا', 'en': 'United Kingdom', 'ar': 'المملكة المتحدة', 'ru': 'Великобритания', 'tr': 'Birleşik Krallık'},
        'FR': {'fa': 'فرانسه', 'en': 'France', 'ar': 'فرنسا', 'ru': 'Франция', 'tr': 'Fransa'},
        'DE': {'fa': 'آلمان', 'en': 'Germany', 'ar': 'ألمانيا', 'ru': 'Германия', 'tr': 'Almanya'},
        'IR': {'fa': 'ایران', 'en': 'Iran', 'ar': 'إيران', 'ru': 'Иран', 'tr': 'İran'},
        'CA': {'fa': 'کانادا', 'en': 'Canada', 'ar': 'كندا', 'ru': 'Канада', 'tr': 'Kanada'},
        'IT': {'fa': 'ایتالیا', 'en': 'Italy', 'ar': 'إيطاليا', 'ru': 'Италия', 'tr': 'İtalya'},
        'ES': {'fa': 'اسپانیا', 'en': 'Spain', 'ar': 'إسبانيا', 'ru': 'Испания', 'tr': 'İspanya'},
        'JP': {'fa': 'ژاپن', 'en': 'Japan', 'ar': 'اليابان', 'ru': 'Япония', 'tr': 'Japonya'},
        'KR': {'fa': 'کره جنوبی', 'en': 'South Korea', 'ar': 'كوريا الجنوبية', 'ru': 'Южная Корея', 'tr': 'Güney Kore'},
        'IN': {'fa': 'هند', 'en': 'India', 'ar': 'الهند', 'ru': 'Индия', 'tr': 'Hindistan'},
        'AU': {'fa': 'استرالیا', 'en': 'Australia', 'ar': 'أستراليا', 'ru': 'Австралия', 'tr': 'Avustralya'},
        'CN': {'fa': 'چین', 'en': 'China', 'ar': 'الصين', 'ru': 'Китай', 'tr': 'Çin'},
        'RU': {'fa': 'روسیه', 'en': 'Russia', 'ar': 'روسيا', 'ru': 'Россия', 'tr': 'Rusya'},
        'TR': {'fa': 'ترکیه', 'en': 'Turkey', 'ar': 'تركيا', 'ru': 'Турция', 'tr': 'Türkiye'},
        'SE': {'fa': 'سوئد', 'en': 'Sweden', 'ar': 'السويد', 'ru': 'Швеция', 'tr': 'İsveç'},
        'NO': {'fa': 'نروژ', 'en': 'Norway', 'ar': 'النرويج', 'ru': 'Норвегия', 'tr': 'Norveç'},
        'DK': {'fa': 'دانمارک', 'en': 'Denmark', 'ar': 'الدنمارك', 'ru': 'Дания', 'tr': 'Danimarka'},
        'BR': {'fa': 'برزیل', 'en': 'Brazil', 'ar': 'البرازيل', 'ru': 'Бразилия', 'tr': 'Brezilya'},
        'MX': {'fa': 'مکزیک', 'en': 'Mexico', 'ar': 'المكسيك', 'ru': 'Мексика', 'tr': 'Meksika'},
        'NL': {'fa': 'هلند', 'en': 'Netherlands', 'ar': 'هولندا', 'ru': 'Нидерланды', 'tr': 'Hollanda'},
        'PL': {'fa': 'لهستان', 'en': 'Poland', 'ar': 'بولندا', 'ru': 'Польша', 'tr': 'Polonya'},
        'NZ': {'fa': 'نیوزیلند', 'en': 'New Zealand', 'ar': 'نيوزيلندا', 'ru': 'Новая Зеландия', 'tr': 'Yeni Zelanda'},
        'ZA': {'fa': 'آفریقای جنوبی', 'en': 'South Africa', 'ar': 'جنوب أفريقيا', 'ru': 'ЮАР', 'tr': 'Güney Afrika'},
    }

    GENRE_MAP = {
        'action': {'fa': 'اکشن', 'en': 'Action', 'ar': 'أكشن', 'ru': 'Боевик', 'tr': 'Aksiyon'},
        'adventure': {'fa': 'ماجراجویی', 'en': 'Adventure', 'ar': 'مغامرة', 'ru': 'Приключения', 'tr': 'Macera'},
        'animation': {'fa': 'انیمیشن', 'en': 'Animation', 'ar': 'رسوم متحركة', 'ru': 'Мультфильм', 'tr': 'Animasyon'},
        'comedy': {'fa': 'کمدی', 'en': 'Comedy', 'ar': 'كوميديا', 'ru': 'Комедия', 'tr': 'Komedi'},
        'crime': {'fa': 'جنایی', 'en': 'Crime', 'ar': 'جريمة', 'ru': 'Криминал', 'tr': 'Suç'},
        'documentary': {'fa': 'مستند', 'en': 'Documentary', 'ar': 'وثائقي', 'ru': 'Документальный', 'tr': 'Belgesel'},
        'drama': {'fa': 'درام', 'en': 'Drama', 'ar': 'دراما', 'ru': 'Драма', 'tr': 'Dram'},
        'family': {'fa': 'خانوادگی', 'en': 'Family', 'ar': 'عائلي', 'ru': 'Семейный', 'tr': 'Aile'},
        'fantasy': {'fa': 'فانتزی', 'en': 'Fantasy', 'ar': 'فانتازيا', 'ru': 'Фэнтези', 'tr': 'Fantastik'},
        'history': {'fa': 'تاریخی', 'en': 'History', 'ar': 'تاريخي', 'ru': 'История', 'tr': 'Tarih'},
        'horror': {'fa': 'ترسناک', 'en': 'Horror', 'ar': 'رعب', 'ru': 'Ужасы', 'tr': 'Korku'},
        'music': {'fa': 'موزیکال', 'en': 'Music', 'ar': 'موسيقى', 'ru': 'Музыка', 'tr': 'Müzik'},
        'mystery': {'fa': 'معمایی', 'en': 'Mystery', 'ar': 'غموض', 'ru': 'Детектив', 'tr': 'Gizem'},
        'romance': {'fa': 'عاشقانه', 'en': 'Romance', 'ar': 'رومانسي', 'ru': 'Мелодрама', 'tr': 'Romantik'},
        'science fiction': {'fa': 'علمی تخیلی', 'en': 'Science Fiction', 'ar': 'خيال علمي', 'ru': 'Фантастика', 'tr': 'Bilim Kurgu'},
        'sci-fi': {'fa': 'علمی تخیلی', 'en': 'Sci-Fi', 'ar': 'خيال علمي', 'ru': 'Фантастика', 'tr': 'Bilim Kurgu'},
        'tv movie': {'fa': 'فیلم تلویزیونی', 'en': 'TV Movie', 'ar': 'فيلم تلفزيوني', 'ru': 'ТВ фильм', 'tr': 'TV Filmi'},
        'thriller': {'fa': 'هیجان انگیز', 'en': 'Thriller', 'ar': 'إثارة', 'ru': 'Триллер', 'tr': 'Gerilim'},
        'war': {'fa': 'جنگی', 'en': 'War', 'ar': 'حرب', 'ru': 'Военный', 'tr': 'Savaş'},
        'western': {'fa': 'وسترن', 'en': 'Western', 'ar': 'غرب أمريكي', 'ru': 'Вестерн', 'tr': 'Batı'},
    }



    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'TMDB_API_KEY', '') or os.getenv('TMDB_API_KEY', '')
        self.session = requests.Session()

        # Optional Proxy Support (checks .env or settings.py)
        http_proxy = getattr(settings, 'HTTP_PROXY', '') or os.getenv('HTTP_PROXY', '')
        https_proxy = getattr(settings, 'HTTPS_PROXY', '') or os.getenv('HTTPS_PROXY', '')
        if http_proxy or https_proxy:
            self.session.proxies = {
                'http': http_proxy,
                'https': https_proxy or http_proxy,
            }

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.languages_map = self.get_languages_map()


    def _get(self, endpoint, params=None):
        if not self.api_key:
            raise TMDBServiceError("کلید API مربوط به TMDB تنظیم نشده است. لطفاً فایل .env را بررسی کنید.")
        
        url = f"{self.BASE_URL}/{endpoint}"
        default_params = {'api_key': self.api_key}
        if params:
            default_params.update(params)

        try:
            response = self.session.get(url, params=default_params, timeout=8)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise TMDBServiceError(f"خطا در ارتباط با TMDB API: {str(e)}")

    def download_image(self, relative_path, is_banner=False, imdb_id=None):
        """
        Download poster or banner image.
        Priority logic: TMDB CDN -> GoldPoster.com Scraper -> Secondary IMDb/Amazon CDN Fallback -> None
        """
        # 1. Try TMDB CDN
        if relative_path:
            base_url = self.BANNER_BASE_URL if is_banner else self.IMAGE_BASE_URL
            clean_path = relative_path if relative_path.startswith('/') else f"/{relative_path}"
            url = f"{base_url}{clean_path}"
            try:
                res = self.session.get(url, timeout=8)
                if res.status_code == 200 and len(res.content) > 3000:
                    filename = os.path.basename(clean_path)
                    return filename, ContentFile(res.content)
            except Exception:
                pass

        # 2. Fallback: Secondary Poster Scraper (GoldPoster.com)
        if imdb_id and not is_banner:
            try:
                search_url = f"https://www.goldposter.com/search-goldposter/?search={imdb_id}"
                gp_res = self.session.get(search_url, timeout=10, allow_redirects=True)
                if gp_res.status_code == 200 and "/movie/" in gp_res.url:
                    soup = BeautifulSoup(gp_res.text, "html.parser")
                    
                    # 0) IMDb ID Verification on page
                    page_text = soup.get_text(" ", strip=True)
                    imdb_match = re.search(r"IMDB:\s*(tt\d{7,9})", page_text)
                    if imdb_match and imdb_match.group(1) != imdb_id:
                        raise ValueError("IMDb ID mismatch on GoldPoster page")

                    # 1) Try og:image
                    og_image = soup.find("meta", property="og:image")
                    raw_poster_url = og_image["content"] if og_image and og_image.get("content") else None

                    # 2) Fallback to mediaviewer img
                    if not raw_poster_url:
                        img_tag = soup.select_one('a[href*="mediaviewer"] img')
                        if img_tag and img_tag.get("src"):
                            raw_poster_url = img_tag["src"]


                    if raw_poster_url:
                        clean_poster_url = raw_poster_url.split("?")[0]
                        if clean_poster_url.startswith('//'):
                            clean_poster_url = f"https:{clean_poster_url}"
                        elif clean_poster_url.startswith('/'):
                            clean_poster_url = f"https://www.goldposter.com{clean_poster_url}"

                        img_res = self.session.get(clean_poster_url, timeout=10)
                        if img_res.status_code == 200 and len(img_res.content) > 3000:
                            filename = f"{imdb_id}_goldposter.jpg"
                            return filename, ContentFile(img_res.content)
            except Exception:
                pass

            # 3. Backup Fallback: Amazon/IMDb CDN
            try:
                omdb_url = f"http://www.omdbapi.com/?i={imdb_id}&apikey=trilogy"
                res = self.session.get(omdb_url, timeout=6)
                if res.status_code == 200:
                    poster_url = res.json().get('Poster')
                    if poster_url and poster_url.startswith('http'):
                        hd_poster_url = poster_url.split('._V1_')[0] + '._V1_FMjpg_UX1000_.jpg'
                        img_res = self.session.get(hd_poster_url, timeout=8)
                        if img_res.status_code != 200:
                            img_res = self.session.get(poster_url, timeout=8)

                        if img_res.status_code == 200 and len(img_res.content) > 3000:
                            filename = f"{imdb_id}_poster.jpg"
                            return filename, ContentFile(img_res.content)
            except Exception:
                pass

        return None




    def find_by_imdb_id(self, external_id, content_type='movie'):
        """find movie or series TMDB data using IMDb ID (e.g. tt1375666) or TMDB numeric ID"""
        external_id = str(external_id).strip()
        
        if external_id.startswith('tt'):
            res = self._get(f"find/{external_id}", {'external_source': 'imdb_id'})
            if not res:
                raise TMDBServiceError(f"محتوایی با شناسه {external_id} در TMDB یافت نشد.")
            
            if content_type == 'movie' and res.get('movie_results'):
                tmdb_id = res['movie_results'][0]['id']
            elif content_type == 'series' and res.get('tv_results'):
                tmdb_id = res['tv_results'][0]['id']
            elif res.get('movie_results'):
                tmdb_id = res['movie_results'][0]['id']
                content_type = 'movie'
            elif res.get('tv_results'):
                tmdb_id = res['tv_results'][0]['id']
                content_type = 'series'
            else:
                raise TMDBServiceError(f"هیچ فیلم یا سریالی با شناسه {external_id} در TMDB پیدا نشد.")
        else:
            try:
                tmdb_id = int(external_id)
            except ValueError:
                raise TMDBServiceError(f"شناسه نامعتبر: {external_id}")

        return tmdb_id, content_type

    def fetch_multilingual_metadata(self, tmdb_id, content_type='movie'):
        """Fetch metadata in all dynamically supported languages with auto-translate fallback"""
        endpoint = f"movie/{tmdb_id}" if content_type == 'movie' else f"tv/{tmdb_id}"
        
        metadata_by_lang = {}
        for lang_code, tmdb_lang in self.languages_map.items():
            data = self._get(endpoint, {'language': tmdb_lang})
            if data:
                metadata_by_lang[lang_code] = data

        english_data = metadata_by_lang.get('en') or self._get(endpoint, {'language': 'en-US'})
        if not english_data:
            raise TMDBServiceError(f"اطلاعات محتوا با آیدی {tmdb_id} از TMDB دریافت نشد.")

        raw_vote = english_data.get('vote_average')
        try:
            imdb_rating_val = round(float(raw_vote), 1) if raw_vote is not None else None
        except (ValueError, TypeError):
            imdb_rating_val = None

        # Staging object to store extracted fields
        staged_data = {
            'tmdb_id': tmdb_id,
            'content_type': content_type,
            'titles': {},
            'descriptions': {},
            'release_year': None,
            'imdb_rating': imdb_rating_val,
            'duration': None,
            'poster_path': english_data.get('poster_path'),
            'backdrop_path': english_data.get('backdrop_path'),
            'genres_raw': english_data.get('genres', []),
            'age_limit': self.fetch_age_limit(tmdb_id, content_type, english_data.get('adult', False)),
            'country_code': None,
            'country_name': None,
        }


        # Extract Country Code & Name
        prod_countries = english_data.get('production_countries', [])
        origin_countries = english_data.get('origin_country', [])
        if prod_countries:
            staged_data['country_code'] = prod_countries[0].get('iso_3166_1')
            staged_data['country_name'] = prod_countries[0].get('name')
        elif origin_countries:
            staged_data['country_code'] = origin_countries[0]
            staged_data['country_name'] = origin_countries[0]



        # Release year & duration
        if content_type == 'movie':
            release_date = english_data.get('release_date', '')
            if release_date and len(release_date) >= 4:
                staged_data['release_year'] = int(release_date[:4])
            staged_data['duration'] = english_data.get('runtime')
        else:
            first_air_date = english_data.get('first_air_date', '')
            if first_air_date and len(first_air_date) >= 4:
                staged_data['release_year'] = int(first_air_date[:4])
            episode_runtimes = english_data.get('episode_run_time', [])
            if episode_runtimes:
                staged_data['duration'] = episode_runtimes[0]

        # Process title and overview per language
        en_title = english_data.get('title') if content_type == 'movie' else english_data.get('name')
        en_overview = english_data.get('overview', '')

        staged_data['titles']['en'] = en_title
        staged_data['descriptions']['en'] = en_overview

        for lang_code in self.languages_map.keys():
            lang_data = metadata_by_lang.get(lang_code, {})
            title = lang_data.get('title') if content_type == 'movie' else lang_data.get('name')
            overview = lang_data.get('overview')


            # Hybrid logic: If blank, fallback to deep-translator from English
            if not title:
                title = en_title
            if not overview or not overview.strip():
                if en_overview and lang_code != 'en' and GoogleTranslator is not None:
                    try:
                        overview = GoogleTranslator(source='en', target=lang_code).translate(en_overview[:1200])
                    except Exception as trans_err:
                        print(f"[TMDB Translation] Translation warning ({lang_code}): {trans_err}")
                        overview = en_overview
                else:
                    overview = en_overview



            staged_data['titles'][lang_code] = title
            staged_data['descriptions'][lang_code] = overview

        return staged_data

    def fetch_age_limit(self, tmdb_id, content_type='movie', is_adult=False):
        """Fetch content certification/age rating from TMDB and map to integer (18, 16, 12, 7)"""
        if is_adult:
            return 18

        raw_cert = ""
        results = []
        try:
            if content_type == 'movie':
                data = self._get(f"movie/{tmdb_id}/release_dates") or {}
                results = data.get('results', [])
                for preferred_country in ['US', 'GB', 'DE', 'FR']:
                    for item in results:
                        if item.get('iso_3166_1') == preferred_country:
                            for rd in item.get('release_dates', []):
                                c = rd.get('certification', '').strip()
                                if c:
                                    raw_cert = c
                                    break
                        if raw_cert:
                            break
                    if raw_cert:
                        break

        except Exception:
            pass

        if not raw_cert and results:
            for item in results:
                if content_type == 'movie':
                    for rd in item.get('release_dates', []):
                        if rd.get('certification'):
                            raw_cert = rd['certification']
                            break
                else:
                    if item.get('rating'):
                        raw_cert = item['rating']
                if raw_cert:
                    break

        raw_cert_upper = raw_cert.upper()

        if any(k in raw_cert_upper for k in ['R', 'NC-17', 'TV-MA', '18']):
            return 18
        elif any(k in raw_cert_upper for k in ['PG-13', 'TV-14', '16', '15']):
            return 16
        elif any(k in raw_cert_upper for k in ['PG', 'TV-PG', '12', '13']):
            return 12
        elif any(k in raw_cert_upper for k in ['G', 'TV-G', 'TV-Y7', '7', '6']):
            return 7

        return 13 if content_type == 'movie' else 12

    def fetch_credits(self, tmdb_id, content_type='movie'):
        """Fetch actors and director with IDs and profile paths"""
        endpoint = f"movie/{tmdb_id}/credits" if content_type == 'movie' else f"tv/{tmdb_id}/credits"
        credits_data = self._get(endpoint) or {}

        cast = credits_data.get('cast', [])[:10]  # Top 10 actors
        crew = credits_data.get('crew', [])

        directors = [
            {'name': m['name'], 'id': m.get('id'), 'profile_path': m.get('profile_path')}
            for m in crew if m.get('job') == 'Director' and m.get('name')
        ]

        actors = [
            {'name': a['name'], 'id': a.get('id'), 'profile_path': a.get('profile_path')}
            for a in cast if a.get('name')
        ]

        return {
            'actors': actors,
            'directors': directors,
        }


    def _generate_seo_metadata(self, title, lang_code, content_type, year, overview=''):
        year_str = f" ({year})" if year else ""
        c_type_fa = "فیلم" if content_type == 'movie' else "سریال"
        c_type_en = "Movie" if content_type == 'movie' else "Series"

        if lang_code == 'fa':
            seo_title = f"دانلود و تماشای آنلاین {c_type_fa} {title}{year_str} با زیرنویس و دوبله فارسی | دیاستومی"
            meta_desc = f"دانلود و تماشای آنلاین {c_type_fa} {title}{year_str} به همراه خلاصه داستان، لیست بازیگران و کیفیت‌های مختلف در دیاستومی."
        elif lang_code == 'en':
            seo_title = f"Watch {title}{year_str} Full {c_type_en} Online | Diastomy"
            overview_snippet = (overview[:130] + '...') if overview and len(overview) > 130 else overview
            meta_desc = f"Watch {title}{year_str} online in full HD quality. {overview_snippet}"
        elif lang_code == 'ar':
            seo_title = f"مشاهدة وتحميل {title}{year_str} مترجم اون لاين | دیاستومی"
            meta_desc = f"مشاهدة وتنزيل {title}{year_str} اون لاين بجودة عالية HD مع الترجمة والقصة الكاملة علی دیاستومی."
        elif lang_code == 'ru':
            seo_title = f"Смотреть {title}{year_str} онлайн бесплатно | دیاستومی"
            meta_desc = f"Смотрите {title}{year_str} онлайн в хорошем качестве HD с русской озвучкой на دیاستومی."
        elif lang_code == 'tr':
            seo_title = f"{title}{year_str} Türkçe Dublaj ve Altyazılı İzle | دیاستومی"
            meta_desc = f"{title}{year_str} konusunu, oyuncularını و fragmanını izleyin. Full HD Türkçe Altyazılı دیاستومی."
        else:
            seo_title = f"Watch {title}{year_str} Online | Diastomy"
            meta_desc = (overview[:150] + '...') if overview else f"Watch {title}{year_str} online."

        return seo_title[:250], meta_desc

    def _get_or_create_genre(self, g_name):
        g_name_clean = g_name.strip()
        g_slug = slugify(g_name_clean) or g_name_clean.lower().replace(' ', '-')
        
        genre = Genre.objects.filter(slug=g_slug).first()
        if genre:
            return genre

        g_key = g_name_clean.lower()
        map_entry = self.GENRE_MAP.get(g_key, {})

        defaults = {'name': map_entry.get('fa', g_name_clean)}
        for lang_code in self.languages_map.keys():
            val = map_entry.get(lang_code)

            if not val:
                if GoogleTranslator is not None and lang_code != 'en':
                    try:
                        val = GoogleTranslator(source='auto', target=lang_code).translate(g_name_clean)
                    except Exception:
                        val = g_name_clean
                else:
                    val = g_name_clean
            defaults[f'name_{lang_code}'] = val

        genre, _ = Genre.objects.get_or_create(slug=g_slug, defaults=defaults)
        return genre

    def _get_or_create_country(self, c_code, c_name_raw):
        c_code_clean = (c_code or '').strip().upper()
        c_name_clean = (c_name_raw or '').strip()
        if not c_code_clean and not c_name_clean:
            return None

        map_entry = self.COUNTRY_MAP.get(c_code_clean, {})
        en_name = map_entry.get('en') or c_name_clean or c_code_clean
        fa_name = map_entry.get('fa') or c_name_clean or c_code_clean
        c_slug = slugify(en_name) or c_code_clean.lower()

        country = Country.objects.filter(slug=c_slug).first()
        if country:
            return country

        defaults = {'name': fa_name}
        for lang_code in self.languages_map.keys():
            val = map_entry.get(lang_code)

            if not val:
                if GoogleTranslator is not None and lang_code != 'en':
                    try:
                        val = GoogleTranslator(source='auto', target=lang_code).translate(en_name)
                    except Exception:
                        val = en_name
                else:
                    val = en_name
            defaults[f'name_{lang_code}'] = val

        country, _ = Country.objects.get_or_create(slug=c_slug, defaults=defaults)
        return country

    def _get_or_create_person(self, name, is_actor=True, is_director=False, profile_path=None, person_id=None):
        name_clean = name.strip()
        p_slug = slugify(name_clean) or name_clean.lower().replace(' ', '-')
        
        person = Person.objects.filter(slug=p_slug).first()
        if person:
            updated = False
            if is_actor and not person.is_actor:
                person.is_actor = True
                updated = True
            if is_director and not person.is_director:
                person.is_director = True
                updated = True
            if profile_path and not person.photo:
                photo_file = self.download_image(profile_path)
                if photo_file:
                    person.photo.save(photo_file[0], photo_file[1], save=False)
                    updated = True
            if updated:
                person.save()
            return person

        defaults = {
            'name': name_clean,
            'is_actor': is_actor,
            'is_director': is_director,
            'bio': f"بیوگرافی {name_clean}",
            'meta_description': f"بیوگرافی و آثار {name_clean} در دیاستومی",
        }

        # Fast fetch of English biography & parallel translation across ALL 5 active languages
        if person_id:
            try:
                p_data = self._get(f"person/{person_id}", {'language': 'en-US'})
                if p_data and p_data.get('biography'):
                    bio_en = p_data.get('biography', '').strip()
                    if bio_en:

                        defaults['bio_en'] = bio_en
                        defaults['bio'] = bio_en

                        def _translate_person_lang(lang_code):
                            if lang_code == 'en':
                                return 'en', bio_en
                            time.sleep(0.1)  # Micro-delay to emulate human browser behavior & prevent rate limits
                            if GoogleTranslator is not None:
                                try:
                                    res = GoogleTranslator(source='auto', target=lang_code).translate(bio_en)
                                    return lang_code, res
                                except Exception:
                                    pass
                            return lang_code, bio_en

                        with ThreadPoolExecutor(max_workers=2) as executor:
                            translated_map = dict(executor.map(_translate_person_lang, list(self.languages_map.keys())))


                        for lang_code, trans_bio in translated_map.items():
                            defaults[f'bio_{lang_code}'] = trans_bio
                            defaults[f'meta_description_{lang_code}'] = f"بیوگرافی و آثار {name_clean} در دیاستومی"

                        if 'bio_fa' in defaults:
                            defaults['bio'] = defaults['bio_fa']
            except Exception:
                pass



        person, created = Person.objects.get_or_create(slug=p_slug, defaults=defaults)

        if profile_path and not person.photo:
            photo_file = self.download_image(profile_path)
            if photo_file:
                person.photo.save(photo_file[0], photo_file[1], save=True)

        return person



    def ingest(self, ingestion_record):
        """Main entry point: Ingest metadata from TMDB and commit to PostgreSQL database"""
        start_time = time.time()
        print(f"\n[TMDB Ingest] Starting ingestion for IMDb ID: {ingestion_record.imdb_id}")
        ingestion_record.status = 'processing'
        ingestion_record.save(update_fields=['status'])

        try:
            print(f"[TMDB Ingest] [1/4] Finding TMDB ID for {ingestion_record.imdb_id}...")
            tmdb_id, content_type = self.find_by_imdb_id(
                ingestion_record.imdb_id,
                ingestion_record.content_type
            )
            ingestion_record.content_type = content_type

            print(f"[TMDB Ingest] [2/4] Fetching 5-language metadata & credits (TMDB ID: {tmdb_id})...")
            staged_data = self.fetch_multilingual_metadata(tmdb_id, content_type)
            credits_data = self.fetch_credits(tmdb_id, content_type)

            print(f"[TMDB Ingest] [3/4] Resolving genres, director, and actors...")
            genre_objs = []
            for g_item in staged_data['genres_raw']:
                g_name = g_item.get('name')
                if g_name:
                    genre = self._get_or_create_genre(g_name)
                    genre_objs.append(genre)

            director_obj = None
            if credits_data['directors']:
                dir_item = credits_data['directors'][0]
                director_obj = self._get_or_create_person(
                    dir_item['name'],
                    is_actor=False,
                    is_director=True,
                    profile_path=dir_item.get('profile_path'),
                    person_id=dir_item.get('id')
                )

            actor_objs = []
            for act_item in credits_data['actors']:
                actor = self._get_or_create_person(
                    act_item['name'],
                    is_actor=True,
                    is_director=False,
                    profile_path=act_item.get('profile_path'),
                    person_id=act_item.get('id')
                )
                actor_objs.append(actor)

            country_obj = self._get_or_create_country(
                staged_data.get('country_code'),
                staged_data.get('country_name')
            )

            primary_title = staged_data['titles'].get('fa') or staged_data['titles'].get('en')
            en_title = staged_data['titles'].get('en') or primary_title

            ModelClass = Movie if content_type == 'movie' else Series

            existing_instance = ModelClass.objects.filter(
                Q(tmdb_id=tmdb_id) |
                Q(imdb_id=ingestion_record.imdb_id) |
                Q(english_title_primary__iexact=en_title) |
                Q(title__iexact=primary_title)
            ).first()

            if existing_instance:
                if content_type == 'movie':
                    ingestion_record.created_movie = existing_instance
                else:
                    ingestion_record.created_series = existing_instance

                err_msg = f"فیلم/سریال «{existing_instance.title}» قبلاً در دیتابیس ثبت شده است و امکان ثبت تکراری وجود ندارد."
                ingestion_record.status = 'failed'
                ingestion_record.error_log = err_msg
                ingestion_record.save()
                print(f"[TMDB Ingest] Duplicate movie detected: '{en_title}'")
                raise TMDBServiceError(err_msg)

            slug_base = slugify(en_title) or f"content-{tmdb_id}"
            unique_slug = slug_base
            counter = 1
            while ModelClass.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{slug_base}-{counter}"
                counter += 1

            instance = ModelClass(
                tmdb_id=tmdb_id,
                imdb_id=ingestion_record.imdb_id,
                title=primary_title,
                english_title_primary=en_title,
                slug=unique_slug,
                description=staged_data['descriptions'].get('fa', ''),
                production_year=staged_data['release_year'],
                imdb_rating=staged_data['imdb_rating'],
                age_limit=staged_data.get('age_limit', 0),
                duration=staged_data['duration'],
                director=director_obj,
                country=country_obj,
            )


            year = staged_data['release_year']
            for lang_code in self.languages_map.keys():
                title_val = staged_data['titles'].get(lang_code) or primary_title
                desc_val = staged_data['descriptions'].get(lang_code) or ''

                if hasattr(instance, f'title_{lang_code}') and title_val:
                    setattr(instance, f'title_{lang_code}', title_val)
                if hasattr(instance, f'description_{lang_code}') and desc_val:
                    setattr(instance, f'description_{lang_code}', desc_val)

                seo_title_val, meta_desc_val = self._generate_seo_metadata(
                    title=title_val,
                    lang_code=lang_code,
                    content_type=content_type,
                    year=year,
                    overview=desc_val
                )

                if hasattr(instance, f'seo_title_{lang_code}'):
                    setattr(instance, f'seo_title_{lang_code}', seo_title_val)
                if hasattr(instance, f'meta_description_{lang_code}'):
                    setattr(instance, f'meta_description_{lang_code}', meta_desc_val)

            print(f"[TMDB Ingest] [4/4] Downloading posters (TMDB -> GoldPoster Scraper Fallback)...")
            cover_img = self.download_image(staged_data['poster_path'], is_banner=False, imdb_id=ingestion_record.imdb_id)
            if cover_img:
                instance.cover.save(cover_img[0], cover_img[1], save=False)

            banner_img = self.download_image(staged_data['backdrop_path'], is_banner=True, imdb_id=ingestion_record.imdb_id)
            if banner_img:
                instance.banner.save(banner_img[0], banner_img[1], save=False)

            instance.save()

            if genre_objs:
                instance.genres.set(genre_objs)
            if actor_objs:
                instance.actors.set(actor_objs)

            if content_type == 'movie':
                ingestion_record.created_movie = instance
            else:
                ingestion_record.created_series = instance

            ingestion_record.status = 'completed'
            ingestion_record.error_log = f"محتوای «{primary_title}» با موفقیت دریافت و ذخیره گردید."
            ingestion_record.save()

            elapsed = round(time.time() - start_time, 2)
            print(f"[TMDB Ingest] SUCCESS: Ingested '{en_title}' in {elapsed}s!\n")
            return instance


        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            safe_err = str(e).encode('ascii', errors='ignore').decode('ascii')
            print(f"[TMDB Ingest] FAILED after {elapsed}s: {safe_err or type(e).__name__}\n")
            ingestion_record.status = 'failed'
            ingestion_record.error_log = str(e)
            ingestion_record.save()
            raise e




    def sync_existing_instance(self, instance, imdb_id=None):
        """Re-sync an existing Movie or Series instance from TMDB using its English title or slug or TMDB search"""
        content_type = 'movie' if getattr(instance, 'is_movie', True) else 'series'
        search_query = instance.english_title_primary or instance.title
        tmdb_id = getattr(instance, 'tmdb_id', None)

        if not tmdb_id:
            if not imdb_id:
                imdb_id = getattr(instance, 'imdb_id', None)

            if not imdb_id:
                ing_filter = {'created_movie': instance} if content_type == 'movie' else {'created_series': instance}
                ing_rec = ContentIngestion.objects.filter(**ing_filter).first()
                if ing_rec:
                    imdb_id = ing_rec.imdb_id

            if imdb_id:
                tmdb_id, content_type = self.find_by_imdb_id(imdb_id, content_type)

        if not tmdb_id:
            endpoint = "search/movie" if content_type == 'movie' else "search/tv"
            res = self._get(endpoint, {'query': search_query}) or {}
            results = res.get('results', [])
            if not results:
                raise TMDBServiceError(f"اطلاعاتی برای «{search_query}» در TMDB یافت نشد.")
            tmdb_id = results[0]['id']

        instance.tmdb_id = tmdb_id
        if imdb_id and not getattr(instance, 'imdb_id', None):
            instance.imdb_id = imdb_id


        staged_data = self.fetch_multilingual_metadata(tmdb_id, content_type)
        credits_data = self.fetch_credits(tmdb_id, content_type)

        if staged_data['release_year']:
            instance.production_year = staged_data['release_year']
        if staged_data['imdb_rating']:
            instance.imdb_rating = staged_data['imdb_rating']
        if staged_data['duration']:
            instance.duration = staged_data['duration']
        if staged_data.get('age_limit'):
            instance.age_limit = staged_data['age_limit']

        if credits_data['directors']:
            d_item = credits_data['directors'][0]
            instance.director = self._get_or_create_person(
                d_item['name'], is_actor=False, is_director=True,
                profile_path=d_item.get('profile_path'), person_id=d_item.get('id')
            )

        c_obj = self._get_or_create_country(staged_data.get('country_code'), staged_data.get('country_name'))
        if c_obj:
            instance.country = c_obj

        genre_objs = [self._get_or_create_genre(g['name']) for g in staged_data['genres_raw'] if g.get('name')]
        actor_objs = [
            self._get_or_create_person(
                act['name'], is_actor=True, is_director=False,
                profile_path=act.get('profile_path'), person_id=act.get('id')
            )
            for act in credits_data['actors']
        ]


        for lang_code in self.languages_map.keys():
            title_val = staged_data['titles'].get(lang_code)
            desc_val = staged_data['descriptions'].get(lang_code)
            if hasattr(instance, f'title_{lang_code}') and title_val:
                setattr(instance, f'title_{lang_code}', title_val)
            if hasattr(instance, f'description_{lang_code}') and desc_val:
                setattr(instance, f'description_{lang_code}', desc_val)

            seo_title_val, meta_desc_val = self._generate_seo_metadata(
                title=title_val or instance.title,
                lang_code=lang_code,
                content_type=content_type,
                year=instance.production_year,
                overview=desc_val or ''
            )
            if hasattr(instance, f'seo_title_{lang_code}'):
                setattr(instance, f'seo_title_{lang_code}', seo_title_val)
            if hasattr(instance, f'meta_description_{lang_code}'):
                setattr(instance, f'meta_description_{lang_code}', meta_desc_val)

        # Download poster & banner with Fallback
        cover_img = self.download_image(staged_data['poster_path'], is_banner=False, imdb_id=imdb_id)
        if cover_img:
            instance.cover.save(cover_img[0], cover_img[1], save=False)

        banner_img = self.download_image(staged_data['backdrop_path'], is_banner=True, imdb_id=imdb_id)
        if banner_img:
            instance.banner.save(banner_img[0], banner_img[1], save=False)

        instance.save()



        if genre_objs:
            instance.genres.set(genre_objs)
        if actor_objs:
            instance.actors.set(actor_objs)

        return instance

