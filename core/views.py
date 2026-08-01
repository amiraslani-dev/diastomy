from itertools import chain
from django.shortcuts import render, redirect
from movie.models import Movie, Series, Genre, Country
from .models import HomePageSetting

def home(request):
    genres = Genre.objects.all()
    countries = Country.objects.all()
    home_setting = HomePageSetting.get_solo()

    latest_series = Series.objects.order_by('-created_at')[:10]
    dubbed_series = Series.objects.filter(is_dubbed=True).order_by('-created_at')[:10]

    dubbed_movies = list(Movie.objects.filter(is_dubbed=True).order_by('-created_at')[:10])
    dubbed_series_list = list(Series.objects.filter(is_dubbed=True).order_by('-created_at')[:10])
    dubbed_all = sorted(
        chain(dubbed_movies, dubbed_series_list),
        key=lambda x: x.created_at,
        reverse=True
    )[:10]

    anim_movies = list(Movie.objects.filter(is_animation=True).order_by('-created_at')[:10])
    anim_series = list(Series.objects.filter(is_animation=True).order_by('-created_at')[:10])
    animations = sorted(chain(anim_movies, anim_series), key=lambda x: x.created_at, reverse=True)[:10]

    # Hero items: selected movies + series from home_setting, or fallback to latest items
    hero_movies = list(home_setting.hero_movies.all())
    hero_series = list(home_setting.hero_series.all())
    hero_items = sorted(chain(hero_movies, hero_series), key=lambda x: x.created_at, reverse=True)
    if not hero_items:
        latest_movies = list(Movie.objects.all().order_by('-created_at')[:3])
        latest_series_hero = list(Series.objects.all().order_by('-created_at')[:2])
        hero_items = sorted(chain(latest_movies, latest_series_hero), key=lambda x: x.created_at, reverse=True)

    suggested_series = list(home_setting.suggested_series.all())
    if not suggested_series:
        suggested_series = list(Series.objects.filter(is_dubbed=True).order_by('-created_at')[:12])
        if not suggested_series:
            suggested_series = list(Series.objects.all().order_by('-created_at')[:12])

    suggested_series_chunks = [suggested_series[i:i + 6] for i in range(0, len(suggested_series), 6)]

    from movie.models import Person
    featured_actors = list(home_setting.featured_actors.all())
    if not featured_actors:
        featured_actors = list(Person.objects.filter(is_actor=True)[:10])

    # Halfprice items
    halfprice_movies = list(home_setting.halfprice_movies.all())
    halfprice_series = list(home_setting.halfprice_series.all())
    halfprice_items = sorted(chain(halfprice_movies, halfprice_series), key=lambda x: x.created_at, reverse=True)
    if not halfprice_items:
        hp_m = list(Movie.objects.filter(screenshot_1__isnull=False).order_by('-created_at')[:5])
        if not hp_m:
            hp_m = list(Movie.objects.all().order_by('-created_at')[:5])
        hp_s = list(Series.objects.filter(screenshot_1__isnull=False).order_by('-created_at')[:5])
        if not hp_s:
            hp_s = list(Series.objects.all().order_by('-created_at')[:5])
        halfprice_items = sorted(chain(hp_m, hp_s), key=lambda x: x.created_at, reverse=True)[:10]

    home_trailers = list(home_setting.trailers.all())

    return render(request, 'core/index.html', {
        'genres': genres,
        'countries': countries,
        'home_setting': home_setting,
        'hero_items': hero_items,
        'suggested_series': suggested_series,
        'suggested_series_chunks': suggested_series_chunks,
        'featured_actors': featured_actors,
        'halfprice_items': halfprice_items,
        'home_trailers': home_trailers,
        'latest_series': latest_series,
        'dubbed_series': dubbed_series,
        'dubbed_all': dubbed_all,
        'animations': animations,
    })

def custom_404_view(request, exception=None):
    return render(request, 'core/404.html', status=404)

import json
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from .models import UserTasteSettings
from movie.models import Movie, Series

@login_required
def selection_view(request):
    if request.user.has_completed_onboarding:
        next_url = request.GET.get('next')
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
        return redirect('/')

    settings = UserTasteSettings.objects.first()
    
    movies = settings.movies.all() if (settings and settings.movies.exists()) else Movie.objects.all()[:6]
    series = settings.series.all() if (settings and settings.series.exists()) else Series.objects.all()[:6]
    
    items = []
    for m in movies:
        genre_str = "، ".join([g.name for g in m.genres.all()])
        items.append({
            'id': f"movie-{m.id}",
            'title': m.title,
            'genre': genre_str if genre_str else _("فیلم"),
            'img': m.cover.url if m.cover else '',
        })
    for s in series:
        genre_str = "، ".join([g.name for g in s.genres.all()])
        items.append({
            'id': f"series-{s.id}",
            'title': s.title,
            'genre': genre_str if genre_str else _("سریال"),
            'img': s.cover.url if s.cover else '',
        })
        
    context = {
        'page_title': settings.title if (settings and settings.title) else _("با انتخاب حداقل 3 عنوان مورد علاقه خود، فیلم و سریال‌های مرتبط با سلیقه‌تان را به شما نمایش خواهیم داد."),
        'items_json': json.dumps(items)
    }
    return render(request, 'core/selection.html', context)

@login_required
@require_POST
def api_selection_submit(request):
    if request.user.has_completed_onboarding:
        return JsonResponse({'error': _("شما قبلاً سلیقه خود را انتخاب کرده‌اید.")}, status=400)
        
    try:
        data = json.loads(request.body)
        selections = data.get('selections', [])
        next_url = request.GET.get('next') or request.POST.get('next') or data.get('next')
        
        if len(selections) < 3:
            return JsonResponse({'error': _("لطفاً حداقل ۳ مورد را انتخاب کنید.")}, status=400)
            
        movie_ids = [int(item.split('-')[1]) for item in selections if item.startswith('movie-')]
        series_ids = [int(item.split('-')[1]) for item in selections if item.startswith('series-')]
        
        request.user.favorite_movies.set(Movie.objects.filter(id__in=movie_ids))
        request.user.favorite_series.set(Series.objects.filter(id__in=series_ids))
        
        request.user.has_completed_onboarding = True
        request.user.save()
        
        redirect_url = '/accounts/user-info/'
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            redirect_url = next_url
            
        return JsonResponse({'message': _("انتخاب‌های شما با موفقیت ثبت شد."), 'redirect_url': redirect_url})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': _("داده‌های نامعتبر")}, status=400)


@require_POST
def api_subscribe_newsletter(request):
    """
    AJAX endpoint for newsletter subscription.
    """
    email = request.POST.get('email') or ''
    if not email and request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            email = body.get('email', '')
        except Exception:
            pass

    from . import services
    success, message = services.subscribe_newsletter(email)
    status_code = 200 if success else 400
    return JsonResponse({
        'success': success,
        'message': str(message),
        'title': str(_("ثبت در خبرنامه")) if success else str(_("خطا"))
    }, status=status_code)

