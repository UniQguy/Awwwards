"""
Root URL configuration for ELECTROCART.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """Basic operational liveness check."""
    return JsonResponse({"status": "ok", "service": "electrocart"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
]
