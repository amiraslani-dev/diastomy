from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import Series, Movie, Quality, Genre, Country

def _record_recent_view(request, item_type, item_id):
    try:
        recent_views = request.session.get('recent_views', [])
        if not isinstance(recent_views, list):
            recent_views = []
        recent_views = [item for item in recent_views if isinstance(item, dict) and not (item.get('type') == item_type and item.get('id') == item_id)]
        recent_views.insert(0, {'type': item_type, 'id': item_id})
        request.session['recent_views'] = recent_views[:12]
        request.session.modified = True
    except Exception:
        pass


def series_detail(request, slug):
    serial = get_object_or_404(Series, slug=slug)
    _record_recent_view(request, 'series', serial.id)
    qualities = Quality.objects.all().order_by('-weight')
    
    is_liked = False
    is_saved = False
    if request.user.is_authenticated:
        is_liked = request.user in serial.likes.all()
        is_saved = request.user in serial.bookmarks.all()
    
    context = {
        'serial': serial,
        'qualities': qualities,
        'is_liked': is_liked,
        'is_saved': is_saved,
    }
    return render(request, 'movie/serial.html', context)

def movie_detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    _record_recent_view(request, 'movie', movie.id)
    qualities = Quality.objects.all().order_by('-weight')
    
    is_liked = False
    is_saved = False
    if request.user.is_authenticated:
        is_liked = request.user in movie.likes.all()
        is_saved = request.user in movie.bookmarks.all()
    
    context = {
        'movie': movie,
        'qualities': qualities,
        'is_liked': is_liked,
        'is_saved': is_saved,
    }
    return render(request, 'movie/cinematic.html', context)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import SeriesComment

@login_required
def add_series_comment(request, slug):
    if request.method == 'POST':
        serial = get_object_or_404(Series, slug=slug)
        text = request.POST.get('text')
        parent_id = request.POST.get('parent_id')
        
        if text:
            parent = None
            print(f"DEBUG add_series_comment: received text='{text}', parent_id='{parent_id}'")
            if parent_id:
                try:
                    parent = SeriesComment.objects.get(id=parent_id, series=serial)
                    print(f"DEBUG add_series_comment: found parent={parent}")
                except SeriesComment.DoesNotExist:
                    print(f"DEBUG add_series_comment: parent with id {parent_id} does not exist for series {serial}")
                    pass
                    
            comment = SeriesComment.objects.create(
                user=request.user,
                series=serial,
                text=text,
                parent=parent
            )
            print(f"DEBUG add_series_comment: created comment={comment} with parent={comment.parent}")
            return JsonResponse({'status': 'success', 'message': 'دیدگاه شما با موفقیت ثبت شد و پس از تایید مدیریت نمایش داده خواهد شد.'})
    return JsonResponse({'status': 'error', 'message': 'خطا در ثبت دیدگاه.'})

@login_required
def like_series_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(SeriesComment, id=comment_id)
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            comment.dislikes.remove(request.user)
            liked = True
        return JsonResponse({'status': 'success', 'likes': comment.likes.count(), 'dislikes': comment.dislikes.count(), 'liked': liked})
    return JsonResponse({'status': 'error'})

@login_required
def dislike_series_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(SeriesComment, id=comment_id)
        if request.user in comment.dislikes.all():
            comment.dislikes.remove(request.user)
            disliked = False
        else:
            comment.dislikes.add(request.user)
            comment.likes.remove(request.user)
            disliked = True
        return JsonResponse({'status': 'success', 'likes': comment.likes.count(), 'dislikes': comment.dislikes.count(), 'disliked': disliked})
    return JsonResponse({'status': 'error'})

from .models import Movie, MovieComment

@login_required
def add_movie_comment(request, slug):
    if request.method == 'POST':
        movie = get_object_or_404(Movie, slug=slug)
        text = request.POST.get('text')
        parent_id = request.POST.get('parent_id')
        
        if text:
            parent = None
            if parent_id:
                try:
                    parent = MovieComment.objects.get(id=parent_id, movie=movie)
                except MovieComment.DoesNotExist:
                    pass
                    
            comment = MovieComment.objects.create(
                user=request.user,
                movie=movie,
                text=text,
                parent=parent
            )
            return JsonResponse({'status': 'success', 'message': 'دیدگاه شما با موفقیت ثبت شد و پس از تایید مدیریت نمایش داده خواهد شد.'})
    return JsonResponse({'status': 'error', 'message': 'خطا در ثبت دیدگاه.'})

@login_required
def like_movie_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(MovieComment, id=comment_id)
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            comment.dislikes.remove(request.user)
            liked = True
        return JsonResponse({'status': 'success', 'likes': comment.likes.count(), 'dislikes': comment.dislikes.count(), 'liked': liked})
    return JsonResponse({'status': 'error'})

@login_required
def dislike_movie_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(MovieComment, id=comment_id)
        if request.user in comment.dislikes.all():
            comment.dislikes.remove(request.user)
            disliked = False
        else:
            comment.dislikes.add(request.user)
            comment.likes.remove(request.user)
            disliked = True
        return JsonResponse({'status': 'success', 'likes': comment.likes.count(), 'dislikes': comment.dislikes.count(), 'disliked': disliked})
    return JsonResponse({'status': 'error'})

@login_required
def like_series(request, slug):
    if request.method == 'POST':
        obj = get_object_or_404(Series, slug=slug)
        if request.user in obj.likes.all():
            obj.likes.remove(request.user)
            liked = False
        else:
            obj.likes.add(request.user)
            liked = True
        return JsonResponse({'status': 'success', 'liked': liked, 'likes_count': obj.likes.count()})
    return JsonResponse({'status': 'error'})

@login_required
def save_series(request, slug):
    if request.method == 'POST':
        obj = get_object_or_404(Series, slug=slug)
        if request.user in obj.bookmarks.all():
            obj.bookmarks.remove(request.user)
            saved = False
        else:
            obj.bookmarks.add(request.user)
            saved = True
        return JsonResponse({'status': 'success', 'saved': saved})
    return JsonResponse({'status': 'error'})

@login_required
def like_movie(request, slug):
    if request.method == 'POST':
        obj = get_object_or_404(Movie, slug=slug)
        if request.user in obj.likes.all():
            obj.likes.remove(request.user)
            liked = False
        else:
            obj.likes.add(request.user)
            liked = True
        return JsonResponse({'status': 'success', 'liked': liked, 'likes_count': obj.likes.count()})
    return JsonResponse({'status': 'error'})

@login_required
def save_movie(request, slug):
    if request.method == 'POST':
        obj = get_object_or_404(Movie, slug=slug)
        if request.user in obj.bookmarks.all():
            obj.bookmarks.remove(request.user)
            saved = False
        else:
            obj.bookmarks.add(request.user)
            saved = True
        return JsonResponse({'status': 'success', 'saved': saved})
    return JsonResponse({'status': 'error'})


from . import services

def actors_list(request):
    """
    Renders the paginated actors list page.
    """
    setting = services.get_actors_page_setting()
    page_number = request.GET.get('page', 1)
    page_obj = services.get_paginated_actors(page_number=page_number, per_page=setting.per_page)
    elided_page_range = page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=1,
        on_ends=1
    )
    
    context = {
        'actors_setting': setting,
        'page_obj': page_obj,
        'actors': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'elided_page_range': elided_page_range,
    }
    return render(request, 'movie/actors.html', context)


def actor_detail(request, slug):
    """
    Renders an actor's profile detail page with paginated filmography.
    """
    actor = services.get_actor_detail(slug)
    setting = services.get_actors_page_setting()
    page_number = request.GET.get('page', 1)
    page_obj = services.get_actor_paginated_filmography(actor, page_number=page_number, per_page=setting.actor_detail_per_page)
    elided_page_range = page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=1,
        on_ends=1
    )
    
    context = {
        'actor': actor,
        'page_obj': page_obj,
        'items': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'elided_page_range': elided_page_range,
    }
    return render(request, 'movie/actor.html', context)


def search_view(request):
    """
    Renders the search page with filter options and slider datasets.
    """
    options = services.get_search_filter_options()
    sliders = services.get_search_page_sliders(request)
    context = {
        'genres': options['genres'],
        'countries': options['countries'],
        'recent': sliders['recent'],
        'hottest': sliders['hottest'],
        'most_viewed': sliders['most_viewed'],
    }
    return render(request, 'movie/search.html', context)


def _build_archive_title(filters, genre_obj=None, country_obj=None):
    if filters.get('q'):
        return _('نتایج جستجو برای: "%(q)s"') % {'q': filters['q']}
    if genre_obj:
        return f"{_('فیلم و سریال‌های')} {genre_obj.name}"
    if country_obj:
        return f"{_('فیلم و سریال‌های ساخت')} {country_obj.name}"
    
    parts = []
    m_type = filters.get('type')
    if m_type == 'movie':
        parts.append(_('فیلم‌های'))
    elif m_type == 'series':
        parts.append(_('سریال‌های'))
    elif m_type == 'animation':
        parts.append(_('انیمیشن‌های'))
    else:
        parts.append(_('آرشیو فیلم و سریال'))
    
    if filters.get('genre'):
        try:
            g = Genre.objects.filter(Q(slug__iexact=filters['genre']) | Q(name__icontains=filters['genre'])).first()
            if g:
                parts.append(g.name)
        except Exception:
            pass

    if filters.get('country'):
        try:
            c = Country.objects.filter(Q(slug__iexact=filters['country']) | Q(name__icontains=filters['country'])).first()
            if c:
                parts.append(f"{_('ساخت')} {c.name}")
        except Exception:
            pass

    if len(parts) > 1:
        return ' '.join(parts)
    return parts[0]


def archive_view(request, forced_type=None, override_title=None, override_meta=None):
    """
    Renders the movie & series archive page with search/filter results.
    """
    raw_tags = request.GET.getlist('tags')
    parsed_tags = []
    for item in raw_tags:
        parsed_tags.extend([t.strip() for t in item.split(',') if t.strip()])

    raw_age = request.GET.getlist('age')
    parsed_age = []
    for item in raw_age:
        parsed_age.extend([a.strip() for a in item.split(',') if a.strip()])

    selected_type = request.GET.get('type', forced_type or 'all')

    filters = {
        'q': request.GET.get('q', '').strip(),
        'type': selected_type,
        'director': request.GET.get('director', '').strip(),
        'actor': request.GET.get('actor', '').strip(),
        'rating': request.GET.get('rating', '').strip(),
        'genre': request.GET.get('genre', '').strip(),
        'country': request.GET.get('country', '').strip(),
        'year_from': request.GET.get('year_from', '').strip(),
        'year_to': request.GET.get('year_to', '').strip(),
        'lang': request.GET.get('lang', '').strip(),
        'duration': request.GET.get('duration', '').strip(),
        'sort': request.GET.get('sort', 'newest').strip(),
        'age': parsed_age,
        'tags': parsed_tags,
    }
    page_number = request.GET.get('page', 1)

    page_obj = services.filter_movies_and_series(filters=filters, page_number=page_number)
    options = services.get_search_filter_options()

    elided_page_range = page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=1,
        on_ends=1
    )

    page_title = override_title or _build_archive_title(filters)

    context = {
        'query': filters['q'],
        'filters': filters,
        'page_title': page_title,
        'meta_description': override_meta,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'elided_page_range': elided_page_range,
        'genres': options['genres'],
        'countries': options['countries'],
    }
    return render(request, 'movie/archive.html', context)


def movies_archive_view(request):
    """
    Dedicated landing page view for Movies Archive (SEO Clean URL /movies/).
    """
    from core.models import ArchivePageSetting
    setting = ArchivePageSetting.get_solo()
    title = setting.movies_title or _('آرشیو فیلم‌ها')
    meta_desc = setting.movies_meta_description or None
    return archive_view(request, forced_type='movie', override_title=title, override_meta=meta_desc)


def series_archive_view(request):
    """
    Dedicated landing page view for Series Archive (SEO Clean URL /series/).
    """
    from core.models import ArchivePageSetting
    setting = ArchivePageSetting.get_solo()
    title = setting.series_title or _('آرشیو سریال‌ها')
    meta_desc = setting.series_meta_description or None
    return archive_view(request, forced_type='series', override_title=title, override_meta=meta_desc)



def genre_archive_view(request, slug):
    """
    Dedicated landing page view for a specific Genre (SEO Friendly).
    URL: /movie/genre/<slug>/
    """
    genre = get_object_or_404(Genre, slug=slug)
    
    raw_tags = request.GET.getlist('tags')
    parsed_tags = []
    for item in raw_tags:
        parsed_tags.extend([t.strip() for t in item.split(',') if t.strip()])

    raw_age = request.GET.getlist('age')
    parsed_age = []
    for item in raw_age:
        parsed_age.extend([a.strip() for a in item.split(',') if a.strip()])

    filters = {
        'q': request.GET.get('q', '').strip(),
        'type': request.GET.get('type', 'all'),
        'director': request.GET.get('director', '').strip(),
        'actor': request.GET.get('actor', '').strip(),
        'rating': request.GET.get('rating', '').strip(),
        'genre': genre.slug,
        'country': request.GET.get('country', '').strip(),
        'year_from': request.GET.get('year_from', '').strip(),
        'year_to': request.GET.get('year_to', '').strip(),
        'lang': request.GET.get('lang', '').strip(),
        'duration': request.GET.get('duration', '').strip(),
        'age': parsed_age,
        'tags': parsed_tags,
    }
    page_number = request.GET.get('page', 1)

    page_obj = services.filter_movies_and_series(filters=filters, page_number=page_number)
    options = services.get_search_filter_options()

    elided_page_range = page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=1,
        on_ends=1
    )

    page_title = _build_archive_title(filters, genre_obj=genre)

    context = {
        'active_genre': genre,
        'query': filters['q'],
        'filters': filters,
        'page_title': page_title,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'elided_page_range': elided_page_range,
        'genres': options['genres'],
        'countries': options['countries'],
    }
    return render(request, 'movie/archive.html', context)


def country_archive_view(request, slug):
    """
    Dedicated landing page view for a specific Country (SEO Friendly).
    URL: /movie/country/<slug>/
    """
    country = get_object_or_404(Country, slug=slug)
    
    raw_tags = request.GET.getlist('tags')
    parsed_tags = []
    for item in raw_tags:
        parsed_tags.extend([t.strip() for t in item.split(',') if t.strip()])

    raw_age = request.GET.getlist('age')
    parsed_age = []
    for item in raw_age:
        parsed_age.extend([a.strip() for a in item.split(',') if a.strip()])

    filters = {
        'q': request.GET.get('q', '').strip(),
        'type': request.GET.get('type', 'all'),
        'director': request.GET.get('director', '').strip(),
        'actor': request.GET.get('actor', '').strip(),
        'rating': request.GET.get('rating', '').strip(),
        'genre': request.GET.get('genre', '').strip(),
        'country': country.slug,
        'year_from': request.GET.get('year_from', '').strip(),
        'year_to': request.GET.get('year_to', '').strip(),
        'lang': request.GET.get('lang', '').strip(),
        'duration': request.GET.get('duration', '').strip(),
        'age': parsed_age,
        'tags': parsed_tags,
    }
    page_number = request.GET.get('page', 1)

    page_obj = services.filter_movies_and_series(filters=filters, page_number=page_number)
    options = services.get_search_filter_options()

    elided_page_range = page_obj.paginator.get_elided_page_range(
        page_obj.number,
        on_each_side=1,
        on_ends=1
    )

    page_title = _build_archive_title(filters, country_obj=country)

    context = {
        'active_country': country,
        'query': filters['q'],
        'filters': filters,
        'page_title': page_title,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'elided_page_range': elided_page_range,
        'genres': options['genres'],
        'countries': options['countries'],
    }
    return render(request, 'movie/archive.html', context)


# Re-export API views for backwards compatibility and clean separation
from .api_views import (
    api_actors_list,
    api_actor_detail,
    api_live_search,
    api_filter_movies,
)





