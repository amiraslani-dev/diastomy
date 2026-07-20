from django.db import models
from django.conf import settings
from movie.models import Movie, Series, Episode

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites_list', verbose_name="کاربر")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites', verbose_name="فیلم")
    series = models.ForeignKey(Series, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites', verbose_name="سریال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "لیست علاقه‌مندی"
        verbose_name_plural = "لیست علاقه‌مندی‌ها"

    def __str__(self):
        target = self.movie.title if self.movie else (self.series.title if self.series else "نامشخص")
        return f"{self.user.username} - {target}"


class WatchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_history', verbose_name="کاربر")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name='watch_history', verbose_name="فیلم")
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True, related_name='watch_history', verbose_name="قسمت")
    watched_duration = models.PositiveIntegerField(default=0, help_text="مدت زمان تماشا شده به ثانیه", verbose_name="مدت تماشا شده")
    total_duration = models.PositiveIntegerField(default=0, help_text="مدت زمان کل ویدیو به ثانیه", verbose_name="مدت کل")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")

    class Meta:
        verbose_name = "تاریخچه تماشا"
        verbose_name_plural = "تاریخچه‌های تماشا"

    def __str__(self):
        target = self.movie.title if self.movie else (self.episode if self.episode else "نامشخص")
        return f"تاریخچه تماشای {self.user.username} - {target}"


class Satisfaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='satisfactions', verbose_name="کاربر")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name='satisfactions', verbose_name="فیلم")
    series = models.ForeignKey(Series, on_delete=models.CASCADE, null=True, blank=True, related_name='satisfactions', verbose_name="سریال")
    is_like = models.BooleanField(verbose_name="پسندیدن (لایک)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "لایک/دیس‌لایک"
        verbose_name_plural = "لایک‌ها و دیس‌لایک‌ها"

    def __str__(self):
        target = self.movie.title if self.movie else (self.series.title if self.series else "نامشخص")
        action = "پسندید" if self.is_like else "نپسندید"
        return f"{self.user.username} - {target} را {action}"
