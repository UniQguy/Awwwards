"""
HTTP endpoints for Razorpay checkout payment verification and inbound webhook processing.
"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.orders.models import Order
from apps.payments.services.webhook_processor import (
    process_webhook_payload,
    verify_and_capture_checkout_payment,
)


@require_POST
def razorpay_verify_view(request):
    """
    POST endpoint called by checkout frontend to verify and finalize online payment.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid JSON body."}, status=400)

    order_number = data.get("order_number")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not (order_number and razorpay_order_id and razorpay_payment_id and razorpay_signature):
        return JsonResponse({"success": False, "error": "Missing required signature parameters."}, status=400)

    order = Order.objects.filter(order_number=order_number).first()
    if not order:
        return JsonResponse({"success": False, "error": f"Order '{order_number}' not found."}, status=404)

    success = verify_and_capture_checkout_payment(
        order=order,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    if success:
        return JsonResponse({
            "success": True,
            "order_number": order.order_number,
            "status": order.status,
            "message": "Payment verified and order confirmed.",
        })
    else:
        return JsonResponse({
            "success": False,
            "order_number": order.order_number,
            "status": order.status,
            "error": "Payment verification failed or stock reservation expired.",
        }, status=400)


@csrf_exempt
@require_POST
def razorpay_webhook_view(request):
    """
    POST endpoint for asynchronous inbound Razorpay webhooks.
    """
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
