import re
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import translation

from movie.models import Person, Movie, Series, Genre, Country
from core.models import ActorsPageSetting

def get_actors_page_setting():
    """
    Returns single ActorsPageSetting instance.
    """
    return ActorsPageSetting.get_solo()

def get_actors_queryset():
    """
    Returns QuerySet of all active actors ordered by name.
    """
    return Person.objects.filter(is_actor=True).order_by('name')

def get_paginated_actors(page_number=1, per_page=None):
    """
    Returns paginated actors page object.
    """
    if per_page is None:
        setting = get_actors_page_setting()
        per_page = setting.per_page or 27

    actors_qs = get_actors_queryset()
    paginator = Paginator(actors_qs, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj

def get_actor_detail(slug):
    """
    Returns actor instance by slug or raises 404.
    """
    return get_object_or_404(Person, slug=slug)

def get_actor_filmography(actor):
    """
    Returns movies and series associated with an actor.
    """
    movies = Movie.objects.filter(actors=actor).distinct()
    series = Series.objects.filter(actors=actor).distinct()
    return {
        'movies': movies,
        'series': series,
    }


def get_actor_paginated_filmography(actor, page_number=1, per_page=10):
    """
    Returns paginated combined movies & series for an actor.
    """
    movies = list(Movie.objects.filter(actors=actor).distinct().prefetch_related('genres'))
    series = list(Series.objects.filter(actors=actor).distinct().prefetch_related('genres'))

    combined = sorted(movies + series, key=lambda x: getattr(x, 'created_at', None), reverse=True)
    paginator = Paginator(combined, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj


def live_quick_search(query_text, limit=8):
    """
    Performs fast live search across Movies, Series, and Persons (Actors/Directors).
    Uses smart script detection (Persian vs English/Latin) & current active language.
    """
    if not query_text or not query_text.strip():
        return []

    q = query_text.strip()
    is_persian_script = bool(re.search(r'[\u0600-\u06FF]', q))

    # Build Q filters for Movie/Series
    movie_q = Q()
    if is_persian_script:
        movie_q |= Q(title_fa__icontains=q) | Q(title__icontains=q) | Q(description_fa__icontains=q)
    else:
        movie_q |= (
            Q(english_title_primary__icontains=q) |
            Q(english_title_secondary__icontains=q) |
            Q(title_en__icontains=q) |
            Q(title__icontains=q)
        )
    # Search by genre or actor/director name
    movie_q |= Q(genres__name__icontains=q) | Q(actors__name__icontains=q) | Q(director__name__icontains=q)

    movies = list(Movie.objects.filter(movie_q).distinct().prefetch_related('genres')[:limit])
    series = list(Series.objects.filter(movie_q).distinct().prefetch_related('genres')[:limit])

    results = []
    combined = movies + series

    for item in combined:
        genres_str = "، ".join([g.name for g in item.genres.all()[:3]])
        cover_url = item.cover.url if item.cover else ""
        results.append({
            'id': item.id,
            'title': str(item.title),
            'genre': genres_str,
            'rating': str(item.imdb_rating or '0.0'),
            'image': cover_url,
            'url': item.get_absolute_url(),
            'type': 'movie' if isinstance(item, Movie) else 'series',
        })

    return results[:limit]


def get_search_filter_options():
    """
    Returns QuerySets of all active Genres and Countries for search filter dropdowns.
    """
    genres = Genre.objects.all().order_by('name')
    countries = Country.objects.all().order_by('name')
    return {
        'genres': genres,
        'countries': countries,
    }


def get_user_recent_views(request=None):
    """
    Returns list of recently viewed Movie and Series objects based on user's session IDs.
    Fallback to latest added items if session is empty.
    """
    recent_views_session = request.session.get('recent_views', []) if request else []
    
    if recent_views_session:
        movie_ids = [item['id'] for item in recent_views_session if isinstance(item, dict) and item.get('type') == 'movie']
        series_ids = [item['id'] for item in recent_views_session if isinstance(item, dict) and item.get('type') == 'series']

        movie_dict = {m.id: m for m in Movie.objects.filter(id__in=movie_ids).prefetch_related('genres')}
        series_dict = {s.id: s for s in Series.objects.filter(id__in=series_ids).prefetch_related('genres')}

        ordered_items = []
        for item in recent_views_session:
            if not isinstance(item, dict):
                continue
            item_type = item.get('type')
            item_id = item.get('id')
            if item_type == 'movie' and item_id in movie_dict:
                ordered_items.append(movie_dict[item_id])
            elif item_type == 'series' and item_id in series_dict:
                ordered_items.append(series_dict[item_id])

        if ordered_items:
            return ordered_items[:8]

    recent_movies = list(Movie.objects.order_by('-created_at').prefetch_related('genres')[:6])
    recent_series = list(Series.objects.order_by('-created_at').prefetch_related('genres')[:6])
    return sorted(recent_movies + recent_series, key=lambda x: getattr(x, 'created_at', None), reverse=True)[:8]


def get_search_page_sliders(request=None):
    """
    Returns datasets for the 3 search page carousels:
    - recent: User's recently viewed Movies & Series (or latest added fallback)
    - hottest: Highest rated Movies & Series
    - most_viewed: Highest view count Movies & Series
    """
    recent = get_user_recent_views(request)

    hottest_movies = list(Movie.objects.order_by('-imdb_rating').prefetch_related('genres')[:6])
    hottest_series = list(Series.objects.order_by('-imdb_rating').prefetch_related('genres')[:6])
    hottest = sorted(hottest_movies + hottest_series, key=lambda x: (getattr(x, 'imdb_rating', 0) or 0), reverse=True)[:8]

    most_viewed_movies = list(Movie.objects.order_by('-views_count').prefetch_related('genres')[:6])
    most_viewed_series = list(Series.objects.order_by('-views_count').prefetch_related('genres')[:6])
    most_viewed = sorted(most_viewed_movies + most_viewed_series, key=lambda x: getattr(x, 'views_count', 0) or 0, reverse=True)[:8]

    return {
        'recent': recent,
        'hottest': hottest,
        'most_viewed': most_viewed,
    }


def search_archive(query_text='', page_number=1, per_page=20):
    """
    Returns paginated combined Movies & Series matching query_text.
    """
    filters = {'q': query_text}
    return filter_movies_and_series(filters, page_number=page_number, per_page=per_page)


def filter_movies_and_series(filters, page_number=1, per_page=20):
    """
    Advanced filter for Movies and Series based on:
    - type: 'all', 'movie', 'series' (or 'همه', 'فیلم', 'سریال')
    - director: director name string
    - actor: actor name string
    - min_rating: minimum float rating
    - genre: genre name or id
    - country: country name or id
    - year_from: int production year from
    - year_to: int production year to
    - tags: list of tags ('دوبله فارسی', 'فقط زیرنویس', 'سانسور شده', 'بدون سانسور')
    - q: search query string
    """
    media_type = filters.get('type', 'all')
    director_name = filters.get('director', '').strip() if isinstance(filters.get('director'), str) else ''
    actor_name = filters.get('actor', '').strip() if isinstance(filters.get('actor'), str) else ''
    min_rating = filters.get('min_rating') or filters.get('rating')
    genre_val = filters.get('genre', '').strip() if isinstance(filters.get('genre'), str) else ''
    country_val = filters.get('country', '').strip() if isinstance(filters.get('country'), str) else ''
    year_from = filters.get('year_from')
    year_to = filters.get('year_to')
    raw_tags = filters.get('tags', [])
    tags = []
    if isinstance(raw_tags, str):
        tags = [t.strip() for t in raw_tags.split(',') if t.strip()]
    elif isinstance(raw_tags, (list, tuple)):
        for item in raw_tags:
            if isinstance(item, str):
                tags.extend([t.strip() for t in item.split(',') if t.strip()])

    query_text = filters.get('q', '').strip() if isinstance(filters.get('q'), str) else ''

    def build_q(is_series=False):
        q = Q()
        if query_text:
            search_q = Q()
            is_persian_script = bool(re.search(r'[\u0600-\u06FF]', query_text))
            if is_persian_script:
                search_q |= (Q(title_fa__icontains=query_text) | Q(title__icontains=query_text) | Q(description_fa__icontains=query_text))
            else:
                search_q |= (Q(english_title_primary__icontains=query_text) | Q(english_title_secondary__icontains=query_text) | Q(title_en__icontains=query_text) | Q(title__icontains=query_text))
            search_q |= Q(genres__name__icontains=query_text) | Q(actors__name__icontains=query_text) | Q(director__name__icontains=query_text)
            q &= search_q

        if director_name:
            q &= Q(director__name__icontains=director_name)
        if actor_name:
            q &= Q(actors__name__icontains=actor_name)
        if min_rating:
            try:
                q &= Q(imdb_rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass
        if genre_val and str(genre_val).lower() not in ['همه', 'all', '']:
            if str(genre_val).isdigit():
                q &= Q(genres__id=int(genre_val))
            else:
                q &= (Q(genres__slug__iexact=genre_val) | Q(genres__name__icontains=genre_val))
        if country_val and str(country_val).lower() not in ['همه', 'all', '']:
            if str(country_val).isdigit():
                q &= Q(country__id=int(country_val))
            else:
                q &= (Q(country__slug__iexact=country_val) | Q(country__name__icontains=country_val))
        if year_from:
            try:
                q &= Q(production_year__gte=int(year_from))
            except (ValueError, TypeError):
                pass
        if year_to:
            try:
                q &= Q(production_year__lte=int(year_to))
            except (ValueError, TypeError):
                pass

        lang_val = filters.get('lang', '').strip() if isinstance(filters.get('lang'), str) else ''
        if 'دوبله فارسی' in tags or 'dubbed' in tags or lang_val in ['dubbed', 'دوبله فارسی']:
            q &= Q(is_dubbed=True)
        if 'فقط زیرنویس' in tags or 'زیرنویس چسبیده' in tags or 'subtitled' in tags or lang_val in ['subtitled', 'زیرنویس چسبیده', 'فقط زیرنویس']:
            q &= Q(has_subtitle=True)
        if 'سانسور شده' in tags or 'censored' in tags:
            q &= Q(is_censored=True)
        if 'بدون سانسور' in tags or 'uncensored' in tags:
            q &= Q(is_censored=False)

        # Age Rating Filter
        age_list = filters.get('age', [])
        if isinstance(age_list, str):
            age_list = [a.strip() for a in age_list.split(',') if a.strip()]

        if age_list:
            age_q = Q()
            for age_val in age_list:
                age_str = str(age_val).lower().strip()
                if '16' in age_str or age_str in ['under_16', '16']:
                    age_q |= Q(age_limit__lte=16)
                elif 'زیر 18' in age_str or age_str in ['under_18']:
                    age_q |= Q(age_limit__lt=18)
                elif 'بالای 18' in age_str or '18+' in age_str or age_str in ['above_18', '18_plus']:
                    age_q |= Q(age_limit__gte=18)
            if age_q:
                q &= age_q

        # Duration Filter
        duration_val = filters.get('duration', '').strip() if isinstance(filters.get('duration'), str) else ''
        if duration_val and duration_val.lower() not in ['all', 'همه', '']:
            d_str = duration_val.lower()
            if d_str in ['under_90', 'زیر 90 دقیقه'] or ('90' in d_str and 'زیر' in d_str):
                q &= Q(duration__lt=90)
            elif d_str in ['90_120', '90 تا 120 دقیقه'] or ('90' in d_str and '120' in d_str):
                q &= Q(duration__gte=90, duration__lte=120)
            elif d_str in ['above_120', 'بالای 120 دقیقه'] or ('120' in d_str and 'بالای' in d_str):
                q &= Q(duration__gt=120)

        return q

    movies = []
    series = []

    media_type_lower = str(media_type).lower().strip()
    if media_type_lower in ['all', 'همه', '']:
        movies = list(Movie.objects.filter(build_q(False)).distinct().prefetch_related('genres'))
        series = list(Series.objects.filter(build_q(True)).distinct().prefetch_related('genres'))
    elif media_type_lower in ['movie', 'فیلم']:
        movies = list(Movie.objects.filter(build_q(False)).distinct().prefetch_related('genres'))
    elif media_type_lower in ['series', 'سریال']:
        series = list(Series.objects.filter(build_q(True)).distinct().prefetch_related('genres'))
    elif media_type_lower in ['animation', 'انیمیشن']:
        anim_q = Q(is_animation=True)
        movies = list(Movie.objects.filter(build_q(False) & anim_q).distinct().prefetch_related('genres'))
        series = list(Series.objects.filter(build_q(True) & anim_q).distinct().prefetch_related('genres'))

    sort_option = str(filters.get('sort', 'newest')).lower().strip()

    if sort_option in ['oldest', 'قدیمی‌ترین', 'قدیمی ترین']:
        combined = sorted(movies + series, key=lambda x: getattr(x, 'created_at', None) or getattr(x, 'id', 0), reverse=False)
    elif sort_option in ['most_viewed', 'views', 'پربازدیدترین', 'پربازدید ترین']:
        combined = sorted(movies + series, key=lambda x: getattr(x, 'views_count', 0) or 0, reverse=True)
    elif sort_option in ['highest_rating', 'rating', 'imdb', 'بالاترین امتیاز', 'امتیاز']:
        combined = sorted(movies + series, key=lambda x: float(getattr(x, 'imdb_rating', 0) or 0), reverse=True)
    else:
        combined = sorted(movies + series, key=lambda x: getattr(x, 'created_at', None) or getattr(x, 'id', 0), reverse=True)

    paginator = Paginator(combined, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj
