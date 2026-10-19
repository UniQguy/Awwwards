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


PINCODE_LOCATIONS = {
    "380": ("Ahmedabad", "Gujarat"),
    "382": ("Gandhinagar", "Gujarat"),
    "390": ("Vadodara", "Gujarat"),
    "395": ("Surat", "Gujarat"),
    "360": ("Rajkot", "Gujarat"),
    "400": ("Mumbai", "Maharashtra"),
    "411": ("Pune", "Maharashtra"),
    "560": ("Bengaluru", "Karnataka"),
    "600": ("Chennai", "Tamil Nadu"),
    "700": ("Kolkata", "West Bengal"),
    "110": ("Delhi", "Delhi"),
    "500": ("Hyderabad", "Telangana"),
    "302": ("Jaipur", "Rajasthan"),
}


def resolve_pincode_location(pincode: str) -> str:
    prefix3 = pincode[:3]
    if prefix3 in PINCODE_LOCATIONS:
        city, state = PINCODE_LOCATIONS[prefix3]
        return f"{city}, {state}"
    prefix2 = pincode[:2]
    state_map = {
        "38": "Gujarat", "39": "Gujarat", "36": "Gujarat", "37": "Gujarat",
        "40": "Maharashtra", "41": "Maharashtra", "42": "Maharashtra", "43": "Maharashtra", "44": "Maharashtra",
        "56": "Karnataka", "57": "Karnataka", "58": "Karnataka", "59": "Karnataka",
        "60": "Tamil Nadu", "61": "Tamil Nadu", "62": "Tamil Nadu", "63": "Tamil Nadu", "64": "Tamil Nadu",
        "11": "Delhi", "12": "Haryana", "13": "Haryana",
        "14": "Punjab", "15": "Punjab", "16": "Chandigarh",
        "20": "Uttar Pradesh", "21": "Uttar Pradesh", "22": "Uttar Pradesh",
        "70": "West Bengal", "50": "Telangana", "30": "Rajasthan",
    }
    return state_map.get(prefix2, "India")


@ratelimit(key="ip", rate="20/m", block=False)
@require_http_methods(["GET", "POST"])
def shipping_check(request: HttpRequest) -> HttpResponse:
    """
    Validates a 6-digit Indian PIN code and calculates delivery arrival dates.
    Caches the checked PIN in the session for cart/checkout autofill.
    """
    is_json = (
        is_json_request(request)
        or request.path.endswith("/estimate/")
        or request.GET.get("format") == "json"
    )

    if getattr(request, "limited", False):
        if is_json:
            return JsonResponse({"serviceable": False, "error": "Rate limit exceeded."}, status=429)
        from apps.core.views import error_429
        return error_429(request)

    pincode = (request.POST.get("pincode") or request.GET.get("pincode") or "").strip()
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        err_msg = f"✕ Service unavailable for PIN {pincode or 'N/A'} (Please enter a valid 6-digit Indian pincode)"
        if is_json:
            return JsonResponse({
                "serviceable": False,
                "pincode": pincode,
                "message": err_msg,
                "error": "Invalid PIN code format. Must be a 6-digit Indian postal code.",
            }, status=200)
        messages.error(request, "Please enter a valid 6-digit PIN code.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    estimate = estimate_delivery(pincode)
    loc_str = resolve_pincode_location(pincode)

    if estimate.serviceable:
        request.session["pincode"] = pincode
        request.session.modified = True
        est_min = 2 if pincode.startswith("380") else estimate.est_days_min
        est_max = 4 if pincode.startswith("380") else estimate.est_days_max
        msg = f"✓ Deliverable to {loc_str} ({pincode}) — Estimated delivery in {est_min}–{est_max} days • COD & Express Available"
        messages.success(request, msg)
    else:
        est_min = estimate.est_days_min
        est_max = estimate.est_days_max
        msg = f"✕ Service unavailable for PIN {pincode} (Please enter a valid 6-digit Indian pincode)"
        messages.warning(request, msg)

    if is_json:
        return JsonResponse({
            "serviceable": estimate.serviceable,
            "deliverable": estimate.serviceable,
            "pincode": pincode,
            "location": loc_str,
            "message": msg,
            "badge_text": msg,
            "est_days_min": est_min,
            "est_days_max": est_max,
            "date_min": estimate.date_min.isoformat() if estimate.date_min else None,
            "date_max": estimate.date_max.isoformat() if estimate.date_max else None,
            "cod_allowed": estimate.cod_allowed,
            "error": None if estimate.serviceable else estimate.unavailable_reason,
        })

    referrer = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(referrer)
