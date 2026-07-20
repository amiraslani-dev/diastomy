from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('selection/', views.selection_view, name='selection'),
    path('api/selection/submit/', views.api_selection_submit, name='api_selection_submit'),
]
