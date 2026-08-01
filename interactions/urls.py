from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path('my-list/', views.my_list_view, name='my_list'),
    path('api/my-list/', views.api_my_list_view, name='api_my_list'),
    path('api/bookmark/toggle/', views.api_toggle_bookmark_view, name='api_toggle_bookmark'),
    path('api/watch-history/<int:pk>/remove/', views.api_remove_watch_history_view, name='api_remove_watch_history'),
]
