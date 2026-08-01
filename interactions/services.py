from django.utils.translation import gettext as _
from movie.models import Movie, Series
from .models import WatchHistory, Favorite


def get_user_saved_movies(user):
    """
    Returns queryset of movies bookmarked by the given user.
    """
    if not user or not user.is_authenticated:
        return Movie.objects.none()
    return Movie.objects.filter(bookmarks=user).select_related('highest_quality').order_by('-id')


def get_user_saved_series(user):
    """
    Returns queryset of series bookmarked by the given user.
    """
    if not user or not user.is_authenticated:
        return Series.objects.none()
    return Series.objects.filter(bookmarks=user).select_related('highest_quality').order_by('-id')


def get_user_watch_history(user):
    """
    Returns watch history entries for the given user.
    """
    if not user or not user.is_authenticated:
        return WatchHistory.objects.none()
    return WatchHistory.objects.filter(user=user).select_related('movie', 'episode', 'episode__season', 'episode__season__series').order_by('-updated_at')


def toggle_movie_bookmark(user, movie_id):
    """
    Toggles bookmark status for a movie for a user.
    """
    try:
        movie = Movie.objects.get(pk=movie_id)
        if user in movie.bookmarks.all():
            movie.bookmarks.remove(user)
            return True, _("فیلم از لیست ذخیره‌شده‌ها حذف شد."), False
        else:
            movie.bookmarks.add(user)
            return True, _("فیلم به لیست ذخیره‌شده‌ها اضافه شد."), True
    except Movie.DoesNotExist:
        return False, _("فیلم یافت نشد."), False


def toggle_series_bookmark(user, series_id):
    """
    Toggles bookmark status for a series for a user.
    """
    try:
        series = Series.objects.get(pk=series_id)
        if user in series.bookmarks.all():
            series.bookmarks.remove(user)
            return True, _("سریال از لیست ذخیره‌شده‌ها حذف شد."), False
        else:
            series.bookmarks.add(user)
            return True, _("سریال به لیست ذخیره‌شده‌ها اضافه شد."), True
    except Series.DoesNotExist:
        return False, _("سریال یافت نشد."), False


def remove_watch_history_item(user, history_id):
    """
    Removes a watch history item for a user.
    """
    try:
        item = WatchHistory.objects.get(pk=history_id, user=user)
        item.delete()
        return True, _("از تاریخچه تماشا حذف شد.")
    except WatchHistory.DoesNotExist:
        return False, _("آیتم یافت نشد.")
