"""
Storefront shipping and PIN code serviceability views.
"""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from apps.core.views import is_json_request
from apps.shipping.services.estimator import estimate_delivery


@ratelimit(key="ip", rate="20/m", block=False)
@require_http_methods(["GET", "POST"])
def shipping_check(request: HttpRequest) -> HttpResponse:
    """
    Validates a 6-digit Indian PIN code and calculates delivery arrival dates.
    Caches the checked PIN in the session for cart/checkout autofill.
    """
    if getattr(request, "limited", False):
        if is_json_request(request):
            return JsonResponse({"serviceable": False, "error": "Rate limit exceeded."}, status=429)
        messages.error(request, "Too many PIN code queries. Please wait a moment.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    pincode = (request.POST.get("pincode") or request.GET.get("pincode") or "").strip()
    if not pincode:
        if is_json_request(request):
            return JsonResponse({"serviceable": False, "error": "PIN code required."}, status=400)
        messages.error(request, "Please enter a valid 6-digit PIN code.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    estimate = estimate_delivery(pincode)

    if estimate.serviceable:
        request.session["pincode"] = pincode
        request.session.modified = True
        msg = f"Delivery serviceable to PIN {pincode} ({estimate.est_days_min}–{estimate.est_days_max} business days)."
        messages.success(request, msg)
    else:
        msg = estimate.unavailable_reason or f"Delivery unavailable for PIN {pincode}."
        messages.warning(request, msg)

    if is_json_request(request):
        return JsonResponse({
            "serviceable": estimate.serviceable,
            "pincode": pincode,
            "est_days_min": estimate.est_days_min,
            "est_days_max": estimate.est_days_max,
            "date_min": estimate.date_min.isoformat() if estimate.date_min else None,
            "date_max": estimate.date_max.isoformat() if estimate.date_max else None,
            "cod_allowed": estimate.cod_allowed,
            "error": estimate.unavailable_reason,
        })

    referrer = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(referrer)
