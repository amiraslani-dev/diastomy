from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from core.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
    path('accounts/api/', include('accounts.api_urls')),
]

handler404 = 'core.views.custom_404_view'

from movie.views import movies_archive_view, series_archive_view

urlpatterns += i18n_patterns(
    path('', home, name='home'),
    path('movies/', movies_archive_view, name='movies_archive'),
    path('series/', series_archive_view, name='series_archive'),
    path('', include('core.urls')),
    path('movie/', include('movie.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include(('interactions.urls', 'interactions'), namespace='interactions')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
