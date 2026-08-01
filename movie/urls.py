from django.urls import path
from . import views, api_views

app_name = 'movie'

urlpatterns = [
    path('search/', views.search_view, name='search'),
    path('archive/', views.archive_view, name='archive'),
    path('movies/', views.movies_archive_view, name='movies_archive'),
    path('series-archive/', views.series_archive_view, name='series_archive'),
    path('genre/<slug:slug>/', views.genre_archive_view, name='genre_archive'),
    path('country/<slug:slug>/', views.country_archive_view, name='country_archive'),
    path('actors/', views.actors_list, name='actors_list'),
    path('actor/<slug:slug>/', views.actor_detail, name='actor_detail'),
    
    path('series/<slug:slug>/', views.series_detail, name='series_detail'),
    path('series/<slug:slug>/comment/', views.add_series_comment, name='add_series_comment'),
    path('series/<slug:slug>/like/', views.like_series, name='like_series'),
    path('series/<slug:slug>/save/', views.save_series, name='save_series'),
    path('comment/<int:comment_id>/like/', views.like_series_comment, name='like_series_comment'),
    path('comment/<int:comment_id>/dislike/', views.dislike_series_comment, name='dislike_series_comment'),
    
    path('movie/<slug:slug>/', views.movie_detail, name='movie_detail'),
    path('movie/<slug:slug>/comment/', views.add_movie_comment, name='add_movie_comment'),
    path('movie/<slug:slug>/like/', views.like_movie, name='like_movie'),
    path('movie/<slug:slug>/save/', views.save_movie, name='save_movie'),
    path('movie-comment/<int:comment_id>/like/', views.like_movie_comment, name='like_movie_comment'),
    path('movie-comment/<int:comment_id>/dislike/', views.dislike_movie_comment, name='dislike_movie_comment'),
    
    path('api/actors/', api_views.api_actors_list, name='api_actors_list'),
    path('api/actor/<slug:slug>/', api_views.api_actor_detail, name='api_actor_detail'),
    path('api/live-search/', api_views.api_live_search, name='api_live_search'),
    path('api/filter/', api_views.api_filter_movies, name='api_filter_movies'),
]
