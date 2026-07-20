from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from core.views import home

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('', include('core.urls')),
    path('movie/', include('movie.urls')),
    path('accounts/', include('accounts.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or settings.STATICFILES_DIRS[0])
    # Also add media support
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
