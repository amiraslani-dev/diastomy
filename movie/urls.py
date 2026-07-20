from django.urls import path
from . import views

app_name = 'movie'

urlpatterns = [
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
]
