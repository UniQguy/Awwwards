"""
Root URL configuration for ELECTROCART.
"""

from django.contrib import admin
from django.urls import include, path

from apps.core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("payments/", include("apps.payments.urls")),
    path("health/", health_check, name="health_check"),
]
