"""
Root URL configuration for ELECTROCART.
"""

import os
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.accounts.views import email_verification_sent_view, resend_verification_email
from apps.core.sitemaps import sitemaps
from apps.core.views import (
    about,
    contact_us,
    csrf_failure,
    error_400,
    error_403,
    error_404,
    error_429,
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

admin.site.site_header = "Electrocart administration"
admin.site.site_title = "Electrocart administration"
admin.site.index_title = "Store Management & Operations"

_original_admin_index = admin.site.index


def _custom_admin_index(request, extra_context=None):
    from decimal import Decimal
    from django.db.models import Count, F, Q
    from django.utils import timezone
    from apps.catalog.models import Product
    from apps.inventory.models import Inventory
    from apps.orders.models import Order

    today = timezone.localdate()
    orders_today_qs = Order.objects.filter(created_at__date=today)
    orders_today_count = orders_today_qs.count()

    # Sum in Python Decimal (never float)
    revenue_today = Decimal("0.00")
    for val in orders_today_qs.values_list("total_amount", flat=True):
        if val is not None:
            revenue_today += Decimal(str(val))

    status_counts = list(
        Order.objects.values("status").annotate(count=Count("id")).order_by("status")
    )

    low_stock_count = Inventory.objects.filter(
        quantity__gt=0, quantity__lte=F("low_stock_threshold")
    ).count()

    products_without_price = Product.objects.filter(
        Q(selling_price__isnull=True) | Q(selling_price=0)
    ).count()

    dashboard = {
        "orders_today": orders_today_count,
        "revenue_today": revenue_today,
        "orders_by_status": status_counts,
        "low_stock_count": low_stock_count,
        "products_without_price": products_without_price,
    }

    ctx = dict(extra_context or {})
    ctx["dashboard"] = dashboard
    return _original_admin_index(request, extra_context=ctx)


admin.site.index = _custom_admin_index


urlpatterns = [
    path(admin_path, admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("about/", about, name="about"),
    path("contact/", contact_us, name="contact"),
    path("health/", health_check, name="health_check"),

    # Customer Authentication & Accounts
    path("accounts/confirm-email/resend/", resend_verification_email, name="account_resend_verification_email"),
    path("accounts/confirm-email/", email_verification_sent_view, name="account_email_verification_sent"),
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
    path("400-test/", error_400, name="error_400_test"),
    path("403-test/", error_403, name="error_403_test"),
    path("403-csrf-test/", csrf_failure, name="csrf_failure_test"),
    path("404-test-page/", error_404, name="error_404_test"),
    path("429-test/", error_429, name="error_429_test"),
    path("500-test/", error_500, name="error_500_test"),

    # Catalog & Editorial Storefront
    path("", include("apps.catalog.urls")),
]

from django.conf import settings
if getattr(settings, "DEBUG", False):
    from apps.core.views_outbox import dev_outbox
    from django.conf.urls.static import static
    urlpatterns.insert(0, path("dev/outbox/", dev_outbox, name="dev_outbox"))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
handler429 = "apps.core.views.error_429"


