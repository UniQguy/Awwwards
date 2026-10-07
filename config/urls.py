"""
Root URL configuration for ELECTROCART.
"""

import os
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core.sitemaps import sitemaps
from apps.core.views import (
    about,
    error_400,
    error_403,
    error_404,
    error_500,
    health_check,
    legal_privacy,
    legal_refunds,
    legal_shipping,
    legal_terms,
    robots_txt,
)

ADMIN_URL = os.environ.get("ADMIN_URL", "admin/").strip("/")
admin_path = f"{ADMIN_URL}/" if ADMIN_URL else "admin/"

urlpatterns = [
    path(admin_path, admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("about/", about, name="about"),
    path("health/", health_check, name="health_check"),

    # Customer Authentication & Accounts
    path("accounts/", include("allauth.urls")),
    path("account/", include("apps.accounts.urls")),

    # Commerce Flows
    path("cart/", include("apps.cart.urls")),
    path("wishlist/", include("apps.wishlist.urls")),
    path("shipping/", include("apps.shipping.urls")),
    path("search/", include("apps.search.urls")),
    path("payments/", include("apps.payments.urls")),
    path("", include("apps.orders.urls")),

    # Legal & Regulatory Policies
    path("legal/terms/", legal_terms, name="legal_terms"),
    path("legal/privacy/", legal_privacy, name="legal_privacy"),
    path("legal/shipping/", legal_shipping, name="legal_shipping"),
    path("legal/refunds/", legal_refunds, name="legal_refunds"),

    # QA and Test Endpoints
    path("404-test-page/", error_404, name="error_404_test"),

    # Catalog & Editorial Storefront
    path("", include("apps.catalog.urls")),
]

handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
handler429 = "apps.core.views.error_429"

