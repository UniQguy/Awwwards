"""
Middleware for setting high-security headers on sensitive checkout and account endpoints.
"""

from django.http import HttpRequest, HttpResponse

SENSITIVE_PREFIXES = (
    "/orders/",
    "/checkout/",
    "/payments/",
    "/account/",
    "/accounts/",
    "/cart/",
)


class SensitivePageHeadersMiddleware:
    """
    Ensures that sensitive pages (checkout, orders, payment callbacks, account views)
    are never cached in intermediate or browser proxies and never leak referrer data.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        path = request.path_info
        if any(path.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
            response["Referrer-Policy"] = "same-origin"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response["Pragma"] = "no-cache"

        return response


class MotionDebugMiddleware:
    """
    Development-only motion override guard per Phase 6 standing orders.
    When settings.MOTION_DEBUG is False (production), strips ?motion= query parameter
    via redirect. When MOTION_DEBUG is True, allows ?motion=1|2|3 for tier testing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        from django.conf import settings
        from django.http import HttpResponseRedirect

        if not getattr(settings, "MOTION_DEBUG", False) and "motion" in request.GET:
            query = request.GET.copy()
            query.pop("motion", None)
            clean_url = request.path_info
            if query:
                clean_url += f"?{query.urlencode()}"
            return HttpResponseRedirect(clean_url)

        return self.get_response(request)


class SecurityHeadersMiddleware:
    """
    Applies strict baseline security headers to all HTTP responses:
    - Permissions-Policy: restricts browser APIs (camera, microphone, geolocation)
    - Cross-Origin-Opener-Policy: isolates browsing context
    - Referrer-Policy: default strict-origin-when-cross-origin
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), "
                'payment=(self "https://checkout.razorpay.com")'
            )
        if "Cross-Origin-Opener-Policy" not in response:
            response["Cross-Origin-Opener-Policy"] = "same-origin"
        if "Referrer-Policy" not in response:
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
