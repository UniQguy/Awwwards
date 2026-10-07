"""
Core application views for system health, legal policy pages, error handlers, and request helpers.
"""

from django.conf import settings
from django.db import DatabaseError, connections
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def health_check(request):
    """
    Operational health check endpoint.
    Actively verifies default database connectivity before returning status ok.
    """
    try:
        connection = connections["default"]
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse(
            {"status": "ok", "service": "electrocart", "database": "healthy"},
            status=200,
        )
    except DatabaseError as exc:
        return JsonResponse(
            {
                "status": "error",
                "service": "electrocart",
                "database": "unhealthy",
                "detail": str(exc),
            },
            status=503,
        )


def is_json_request(request) -> bool:
    """
    Detects if client expects a JSON response (for AJAX progressive enhancement).
    """
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )


# ==============================================================================
# LEGAL & EDITORIAL STATIC PAGES
# ==============================================================================

def legal_terms(request):
    return render(request, "pages/terms.html")


def legal_privacy(request):
    return render(request, "pages/privacy.html")


def legal_shipping(request):
    return render(request, "pages/shipping.html")


def legal_refunds(request):
    return render(request, "pages/refunds.html")


def about(request):
    return render(request, "pages/about.html")


def robots_txt(request):
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
    admin_slug = getattr(settings, "ADMIN_URL", "admin/").strip("/")
    lines = [
        "User-agent: *",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /account/",
        "Disallow: /orders/",
        f"Disallow: /{admin_slug}/",
        "Disallow: /search/",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


# ==============================================================================
# CUSTOM ERROR HANDLERS (WP1)
# ==============================================================================

def csrf_failure(request, reason=""):
    """
    Renders custom 403 page when CSRF token verification fails.
    """
    print(f"CSRF FAILURE REASON: {reason} for path {request.path}")
    return render(
        request,
        "403.html",
        {"reason": f"Security verification failed: {reason}"},
        status=403,
    )


def error_400(request, exception=None):
    return render(request, "400.html", status=400)


def error_403(request, exception=None):
    return render(request, "403.html", status=403)


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    """
    500 error handler. Must not query database or depend on global context processors.
    """
    return render(request, "500.html", status=500)


def error_429(request, exception=None):
    """
    HTTP 429 Too Many Requests rate-limit failure view.
    """
    return render(request, "429.html", status=429)
