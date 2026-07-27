from django.shortcuts import render, get_object_or_404
from .models import Series, Movie, Quality

def series_detail(request, slug):
    serial = get_object_or_404(Series, slug=slug)
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
