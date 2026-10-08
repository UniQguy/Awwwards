"""
HTTP endpoints for Razorpay checkout payment verification, webhooks, and storefront payment pages.
"""

from decimal import Decimal
import json

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.core.views import is_json_request
from apps.inventory.services.reservation_service import convert_reservation
from apps.orders.models import Order
from apps.orders.services.invoicing import generate_invoice
from apps.payments.services.webhook_processor import (
    process_webhook_payload,
    verify_and_capture_checkout_payment,
)


def _validate_order_access(request: HttpRequest, order: Order) -> bool:
    if request.user.is_authenticated and order.user == request.user:
        return True
    token = request.GET.get("token") or request.session.get(f"order_token_{order.order_number}")
    session_token = request.session.get(f"order_token_{order.order_number}")
    if token and token == session_token:
        return True
    return False


@require_GET
def razorpay_checkout_page(request: HttpRequest, order_number: str) -> HttpResponse:
    """
    Renders Razorpay modal checkout screen and handles non-JS COD fallback.
    """
    order = get_object_or_404(Order, order_number=order_number)

    if not _validate_order_access(request, order):
        raise Http404("Order not found or authorization expired.")

    if order.payment_status == Order.PAYMENT_STATUS_CAPTURED:
        return redirect("order_success", order_number=order.order_number)

    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    keys_unconfigured = not key_id or key_id == "rzp_test_placeholder"
    amount_paise = int(order.total_amount * 100)
    can_cod = (order.total_amount <= Decimal("50000.00"))

    context = {
        "order": order,
        "key_id": key_id,
        "keys_unconfigured": keys_unconfigured,
        "amount_paise": amount_paise,
        "can_cod": can_cod,
        "token": request.GET.get("token") or request.session.get(f"order_token_{order.order_number}"),
        "breadcrumbs": [{"title": "Payment", "url": f"/payments/razorpay/checkout/{order.order_number}/"}],
    }
    return render(request, "payments/razorpay_checkout.html", context)


@require_POST
def razorpay_switch_cod(request: HttpRequest, order_number: str) -> HttpResponseRedirect:
    """
    Fallback action allowing customer to convert an online payment order to Cash on Delivery.
    """
    order = get_object_or_404(Order, order_number=order_number)

    if not _validate_order_access(request, order):
        raise Http404("Order access unauthorized.")

    if order.total_amount > Decimal("50000.00"):
        messages.error(request, "Cash on Delivery is limited to orders up to ₹50,000.")
        return redirect("payments:razorpay_checkout", order_number=order.order_number)

    order.payment_method = Order.PAYMENT_METHOD_COD
    order.status = Order.STATUS_CONFIRMED
    order.save(update_fields=["payment_method", "status", "updated_at"])

    # Convert reservations to permanent stock reduction
    for res in order.reservations.filter(status="reserved"):
        convert_reservation(res, order=order)

    # Issue invoice
    generate_invoice(order)

    token = request.session.get(f"order_token_{order.order_number}", "")
    messages.success(request, "Order switched to Cash on Delivery (COD) successfully!")
    return redirect(f"/orders/{order.order_number}/success/?token={token}")


@require_POST
def razorpay_verify_view(request: HttpRequest) -> HttpResponse:
    """
    Endpoint verifying and finalizing online payment from Razorpay modal.
    Accepts both standard POST form data and application/json bodies.
    """
    is_json = (request.content_type == "application/json") or is_json_request(request)

    if request.content_type == "application/json" or not request.POST:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except ValueError:
            return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)
    else:
        data = request.POST

    order_number = data.get("order_number")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not (order_number and razorpay_order_id and razorpay_payment_id and razorpay_signature):
        if is_json:
            return JsonResponse({"success": False, "error": "Missing required signature parameters."}, status=400)
        messages.error(request, "Incomplete payment confirmation received.")
        return redirect("payments:payment_failed", order_number=order_number or "unknown")

    order = Order.objects.filter(order_number=order_number).first()
    if not order:
        if is_json:
            return JsonResponse({"success": False, "error": f"Order '{order_number}' not found."}, status=404)
        raise Http404(f"Order '{order_number}' not found.")

    success = verify_and_capture_checkout_payment(
        order=order,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    if success:
        if is_json:
            return JsonResponse({
                "success": True,
                "order_number": order.order_number,
                "status": order.status,
                "message": "Payment verified and order confirmed.",
            })
        token = request.session.get(f"order_token_{order.order_number}", "")
        messages.success(request, "Payment verified successfully!")
        return redirect(f"/orders/{order.order_number}/success/?token={token}")
    else:
        if is_json:
            return JsonResponse({
                "success": False,
                "order_number": order.order_number,
                "status": order.status,
                "error": "Payment verification failed or stock reservation expired.",
            }, status=400)
        return redirect("payments:payment_failed", order_number=order.order_number)


from django_ratelimit.decorators import ratelimit


@csrf_exempt
@ratelimit(key="ip", rate="120/m", block=False)
@require_POST
def razorpay_webhook_view(request: HttpRequest) -> JsonResponse:
    """
    POST endpoint for asynchronous inbound Razorpay webhooks.
    """
    if getattr(request, "limited", False):
        return JsonResponse({"error": "Rate limit exceeded."}, status=429)

    raw_body = request.body
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not signature:
        return JsonResponse({"error": "Missing X-Razorpay-Signature header."}, status=400)

    try:
        res = process_webhook_payload(raw_body=raw_body, signature_header=signature)
        return JsonResponse(res, status=200)
    except PermissionError as e:
        return JsonResponse({"error": str(e)}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def payment_failed(request: HttpRequest, order_number: str) -> HttpResponse:
    order = get_object_or_404(Order, order_number=order_number)
    can_cod = (order.total_amount <= Decimal("50000.00"))
    return render(request, "payments/failed.html", {"order": order, "can_cod": can_cod})


@require_GET
def payment_cancelled(request: HttpRequest, order_number: str) -> HttpResponse:
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "payments/cancelled.html", {"order": order})


@require_GET
def payment_pending(request: HttpRequest, order_number: str) -> HttpResponse:
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "payments/pending.html", {"order": order})
