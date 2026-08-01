from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('404/', views.custom_404_view, name='page_404'),
    path('selection/', views.selection_view, name='selection'),
    path('api/selection/submit/', views.api_selection_submit, name='api_selection_submit'),
    path('api/newsletter/subscribe/', views.api_subscribe_newsletter, name='api_subscribe_newsletter'),
]
