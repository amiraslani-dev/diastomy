from django.contrib import admin
from .models import Favorite, WatchHistory, Satisfaction

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'series', 'created_at']

@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'episode', 'watched_duration', 'total_duration', 'updated_at']

@admin.register(Satisfaction)
class SatisfactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'series', 'is_like', 'created_at']
