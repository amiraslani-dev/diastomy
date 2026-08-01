from django.http import JsonResponse
from . import services


def api_actors_list(request):
    """
    JSON API Endpoint for actors list.
    """
    setting = services.get_actors_page_setting()
    page_number = request.GET.get('page', 1)
    page_obj = services.get_paginated_actors(page_number=page_number, per_page=setting.per_page)

    actors_data = []
    for actor in page_obj.object_list:
        actors_data.append({
            'id': actor.id,
            'name': actor.name,
            'slug': actor.slug,
            'bio': actor.bio,
            'photo': actor.photo.url if actor.photo else None,
        })

    return JsonResponse({
        'success': True,
        'page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'actors': actors_data,
    })


def api_actor_detail(request, slug):
    """
    JSON API Endpoint for actor detail & filmography.
    """
    actor = services.get_actor_detail(slug)
    setting = services.get_actors_page_setting()
    page_number = request.GET.get('page', 1)
    page_obj = services.get_actor_paginated_filmography(actor, page_number=page_number, per_page=setting.actor_detail_per_page)

    items_data = []
    for item in page_obj.object_list:
        items_data.append({
            'id': item.id,
            'title': item.title,
            'slug': item.slug,
            'cover': item.cover.url if item.cover else None,
            'imdb_rating': item.imdb_rating,
            'type': 'movie' if item.is_movie else 'series',
            'genres': [g.name for g in item.genres.all()],
        })

    return JsonResponse({
        'success': True,
        'actor': {
            'id': actor.id,
            'name': actor.name,
            'slug': actor.slug,
            'bio': actor.bio,
            'photo': actor.photo.url if actor.photo else None,
        },
        'page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'filmography': items_data,
    })


def api_live_search(request):
    """
    JSON API endpoint for live auto-complete search.
    Query param: ?q=...
    """
    query = request.GET.get('q', '')
    results = services.live_quick_search(query)
    return JsonResponse({
        'success': True,
        'results': results,
    })


def api_filter_movies(request):
    """
    API endpoint returning JSON for movie/series filter queries for Mobile App & Web.
    Endpoint: /movie/api/filter/
    """
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

    results = []
    for item in page_obj.object_list:
        cover_url = item.cover.url if getattr(item, 'cover', None) else ''
        genres_list = [{'id': g.id, 'name': g.name, 'slug': g.slug} for g in item.genres.all()]
        is_series = hasattr(item, 'seasons')
        results.append({
            'id': item.id,
            'title': item.title,
            'slug': item.slug,
            'type': 'series' if is_series else 'movie',
            'is_animation': getattr(item, 'is_animation', False),
            'url': item.get_absolute_url(),
            'cover': cover_url,
            'genres': genres_list,
            'imdb_rating': float(item.imdb_rating or 0.0),
            'production_year': item.production_year,
            'duration': item.duration,
            'age_limit': item.age_limit,
            'is_dubbed': getattr(item, 'is_dubbed', False),
            'has_subtitle': getattr(item, 'has_subtitle', False),
            'is_censored': getattr(item, 'is_censored', False),
            'description': item.description[:150] if item.description else '',
        })

    return JsonResponse({
        'success': True,
        'total_pages': page_obj.paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_results': page_obj.paginator.count,
        'results': results,
    })
