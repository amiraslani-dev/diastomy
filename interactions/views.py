from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from . import services


@login_required
def my_list_view(request):
    """
    Renders My List page with tabs for Continue Watching, Series, and Movies.
    """
    saved_movies = services.get_user_saved_movies(request.user)
    saved_series = services.get_user_saved_series(request.user)
    watch_history = services.get_user_watch_history(request.user)

    # Process watch history items with progress calculation
    history_data = []
    for item in watch_history:
        progress_pct = 0
        if item.total_duration > 0:
            progress_pct = min(100, int((item.watched_duration / item.total_duration) * 100))
        remaining_seconds = max(0, item.total_duration - item.watched_duration)
        rem_min = remaining_seconds // 60
        rem_sec = remaining_seconds % 60
        remaining_str = f"{rem_min:02d}:{rem_sec:02d}"

        history_data.append({
            'item': item,
            'progress_pct': progress_pct,
            'remaining_str': remaining_str,
        })

    initial_tab = request.GET.get('tab', 'continue')
    if initial_tab not in ['continue', 'movies', 'series']:
        initial_tab = 'continue'

    context = {
        'active_tab': 'my-list',
        'initial_tab': initial_tab,
        'saved_movies': saved_movies,
        'saved_series': saved_series,
        'watch_history': history_data,
        'total_movies_count': saved_movies.count(),
        'total_series_count': saved_series.count(),
        'total_history_count': len(history_data),
    }
    return render(request, 'interactions/my-list.html', context)


@login_required
def api_my_list_view(request):
    """
    API endpoint returning user's saved movies, saved series, and continue watching list.
    """
    saved_movies = services.get_user_saved_movies(request.user)
    saved_series = services.get_user_saved_series(request.user)
    watch_history = services.get_user_watch_history(request.user)

    movies_data = [{
        'id': m.id,
        'title': m.title,
        'slug': m.slug,
        'poster': m.poster.url if m.poster else None,
        'year': m.release_year,
        'imdb': str(m.imdb_rating) if m.imdb_rating else '',
    } for m in saved_movies]

    series_data = [{
        'id': s.id,
        'title': s.title,
        'slug': s.slug,
        'poster': s.poster.url if s.poster else None,
        'year': s.release_year,
        'imdb': str(s.imdb_rating) if s.imdb_rating else '',
    } for s in saved_series]

    history_data = []
    for h in watch_history:
        progress_pct = 0
        if h.total_duration > 0:
            progress_pct = min(100, int((h.watched_duration / h.total_duration) * 100))
        
        target_title = h.movie.title if h.movie else (h.episode.season.series.title if h.episode and h.episode.season and h.episode.season.series else '')
        subtitle = _("فصل %(season)s - قسمت %(episode)s") % {'season': h.episode.season.season_number, 'episode': h.episode.episode_number} if h.episode and h.episode.season else ""
        poster = h.movie.poster.url if h.movie and h.movie.poster else (h.episode.season.series.poster.url if h.episode and h.episode.season and h.episode.season.series and h.episode.season.series.poster else None)

        history_data.append({
            'id': h.id,
            'title': target_title,
            'subtitle': subtitle,
            'poster': poster,
            'watched_duration': h.watched_duration,
            'total_duration': h.total_duration,
            'progress_pct': progress_pct,
        })

    return JsonResponse({
        'success': True,
        'movies': movies_data,
        'series': series_data,
        'watch_history': history_data,
    })


@login_required
@require_POST
def api_toggle_bookmark_view(request):
    """
    API endpoint to toggle bookmark for a movie or series.
    Expects json or POST params: item_type ('movie' or 'series'), item_id
    """
    item_type = request.POST.get('item_type') or request.GET.get('item_type')
    item_id = request.POST.get('item_id') or request.GET.get('item_id')

    if not item_type or not item_id:
        return JsonResponse({'success': False, 'message': _('اطلاعات ناقص است.')}, status=400)

    if item_type == 'movie':
        success, message, is_bookmarked = services.toggle_movie_bookmark(request.user, item_id)
    elif item_type == 'series':
        success, message, is_bookmarked = services.toggle_series_bookmark(request.user, item_id)
    else:
        return JsonResponse({'success': False, 'message': _('نوع آیتم معتبر نیست.')}, status=400)

    if success:
        return JsonResponse({
            'success': True,
            'message': message,
            'is_bookmarked': is_bookmarked
        })
    return JsonResponse({'success': False, 'message': message}, status=404)


@login_required
@require_POST
def api_remove_watch_history_view(request, pk):
    """
    API endpoint to remove an item from watch history.
    """
    success, message = services.remove_watch_history_item(request.user, pk)
    if success:
        return JsonResponse({'success': True, 'message': message})
    return JsonResponse({'success': False, 'message': message}, status=404)
