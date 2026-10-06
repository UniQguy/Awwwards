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
            response["Referrer-Policy"] = "no-referrer"
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response["Pragma"] = "no-cache"

        return response
