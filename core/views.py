from django.shortcuts import render

def home(request):
    return render(request, 'core/index.html')

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
        return redirect('/')

    settings = UserTasteSettings.objects.first()
    
    movies = settings.movies.all() if settings else []
    series = settings.series.all() if settings else []
    
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
        
        if len(selections) < 3:
            return JsonResponse({'error': _("لطفاً حداقل ۳ مورد را انتخاب کنید.")}, status=400)
            
        movie_ids = [int(item.split('-')[1]) for item in selections if item.startswith('movie-')]
        series_ids = [int(item.split('-')[1]) for item in selections if item.startswith('series-')]
        
        request.user.favorite_movies.set(Movie.objects.filter(id__in=movie_ids))
        request.user.favorite_series.set(Series.objects.filter(id__in=series_ids))
        
        request.user.has_completed_onboarding = True
        request.user.save()
        
        return JsonResponse({'message': _("انتخاب‌های شما با موفقیت ثبت شد."), 'redirect_url': '/accounts/user-info/'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': _("داده‌های نامعتبر")}, status=400)
