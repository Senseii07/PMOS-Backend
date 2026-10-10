"""
Root URL configuration for Serene Wellness backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/campaigns/", include("apps.campaigns.urls")),
    path("api/health/", include("apps.health.urls")),
    path("api/conditions/", include("apps.conditions.urls")),
    path("api/assistant/", include("apps.assistant.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
