from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import HomeView
from .admin_site import propz_admin_site

urlpatterns = [
    path('admin/', propz_admin_site.urls),
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls')),
    path('properties/', include('properties.urls')),
    path('maintenance/', include('maintenance.urls')),
    path('tenancy/', include('tenancy.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

