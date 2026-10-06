"""
Storefront views for checkout flow, order confirmation, tracking, invoice presentation, and cancellation.
"""

from decimal import Decimal
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django_ratelimit.decorators import ratelimit

from apps.accounts.models import Address, IndianState
from apps.cart.services.cart_calculator import calculate_cart_summary
from apps.cart.services.cart_service import get_or_create_cart
from apps.orders.models import Order
from apps.orders.services.invoicing import generate_invoice
from apps.orders.services.order_creator import place_order
from apps.orders.services.order_status import can_transition, transition_order_status
from apps.orders.services.tracking import get_tracking_info
from apps.orders.utils.number_words import number_to_words_inr
from apps.promotions.services.coupon_validator import validate_coupon
from apps.shipping.services.estimator import estimate_delivery


def _get_cart(request: HttpRequest):
    if request.user.is_authenticated:
        return get_or_create_cart(user=request.user)
    token = (
        request.COOKIES.get("electrocart_guest_token")
        or request.COOKIES.get("guest_token")
        or request.session.get("guest_token", "")
    )
    return get_or_create_cart(guest_token=token)


def _validate_order_access(request: HttpRequest, order: Order) -> bool:
    """Verifies that the current request is authorized to view or manage the order."""
    if request.user.is_authenticated and order.user == request.user:
        return True

    token = request.GET.get("token") or request.session.get(f"order_token_{order.order_number}")
    session_token = request.session.get(f"order_token_{order.order_number}")
    if token and token == session_token:
        return True

    # Check track grant
    if request.session.get(f"track_grant_{order.order_number}"):
        return True

    return False


# ==============================================================================
# CHECKOUT FLOW
# ==============================================================================


@require_GET
def checkout_start(request: HttpRequest) -> HttpResponse:
    """
    Step 0: Initial checkout gateway.
    Authenticated users jump straight to address entry. Guests choose guest checkout or login.
    """
    cart = _get_cart(request)
    if not cart.items.exists():
        messages.info(request, "Your cart is empty. Add items before proceeding to checkout.")
        return redirect("cart_detail")

    if request.user.is_authenticated:
        return redirect("checkout_address")

    summary = calculate_cart_summary(cart)
    context = {
        "cart": cart,
        "summary": summary,
        "breadcrumbs": [{"title": "Checkout", "url": "/checkout/"}],
    }
    return render(request, "orders/checkout_start.html", context)


@require_POST
def checkout_guest(request: HttpRequest) -> HttpResponseRedirect:
    """
    Captures guest customer contact info before shipping address entry.
    """
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    full_name = request.POST.get("full_name", "").strip()

    if not email or "@" not in email:
        messages.error(request, "Please enter a valid email address for order notifications.")
        return redirect("checkout_start")

    clean_phone = "".join(filter(str.isdigit, phone))
    if len(clean_phone) != 10:
        messages.error(request, "Please enter a valid 10-digit Indian mobile number.")
        return redirect("checkout_start")

    request.session["checkout_guest"] = {
        "email": email,
        "phone": clean_phone,
        "full_name": full_name or email.split("@")[0],
    }
    request.session.modified = True
    return redirect("checkout_address")


def checkout_address(request: HttpRequest) -> HttpResponse:
    """
    Step 1: Shipping destination selection or manual address input.
    Validates PIN serviceability before advancing.
    """
    cart = _get_cart(request)
    if not cart.items.exists():
        return redirect("cart_detail")

    if not request.user.is_authenticated and "checkout_guest" not in request.session:
        return redirect("checkout_start")

    saved_addresses = []
    if request.user.is_authenticated:
        saved_addresses = list(request.user.addresses.all())

    states = IndianState.choices

    if request.method == "POST":
        address_id = request.POST.get("address_id")
        if request.user.is_authenticated and address_id:
            addr = get_object_or_404(Address, id=address_id, user=request.user)
            est = estimate_delivery(addr.pincode)
            if not est.serviceable:
                messages.error(request, f"Saved address PIN {addr.pincode} is currently unserviceable: {est.unavailable_reason}")
                return redirect("checkout_address")

            address_data = {
                "full_name": addr.full_name,
                "phone": addr.phone,
                "line1": addr.line1,
                "line2": addr.line2,
                "landmark": addr.landmark,
                "city": addr.city,
                "state": addr.state,
                "pincode": addr.pincode,
            }
        else:
            full_name = request.POST.get("full_name", "").strip()
            phone = "".join(filter(str.isdigit, request.POST.get("phone", "").strip()))
            line1 = request.POST.get("line1", "").strip()
            line2 = request.POST.get("line2", "").strip()
            landmark = request.POST.get("landmark", "").strip()
            city = request.POST.get("city", "").strip()
            state = request.POST.get("state", "").strip()
            pincode = request.POST.get("pincode", "").strip()

            if not (full_name and line1 and city and state and pincode):
                messages.error(request, "Please fill in all required address fields.")
                return render(request, "orders/checkout_address.html", {
                    "saved_addresses": saved_addresses,
                    "states": states,
                    "form_data": request.POST,
                })

            if len(phone) != 10:
                messages.error(request, "Please provide a valid 10-digit Indian phone number.")
                return render(request, "orders/checkout_address.html", {
                    "saved_addresses": saved_addresses,
                    "states": states,
                    "form_data": request.POST,
                })

            est = estimate_delivery(pincode)
            if not est.serviceable:
                messages.error(request, est.unavailable_reason or f"PIN code {pincode} is not serviceable for delivery.")
                return render(request, "orders/checkout_address.html", {
                    "saved_addresses": saved_addresses,
                    "states": states,
                    "form_data": request.POST,
                })

            address_data = {
                "full_name": full_name,
                "phone": phone,
                "line1": line1,
                "line2": line2,
                "landmark": landmark,
                "city": city,
                "state": state,
                "pincode": pincode,
            }

            if request.user.is_authenticated and request.POST.get("save_address"):
                Address.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone,
                    line1=line1,
                    line2=line2,
                    landmark=landmark,
                    city=city,
                    state=state,
                    pincode=pincode,
                    is_default=(len(saved_addresses) == 0),
                )

        request.session["checkout_address"] = address_data
        request.session["pincode"] = address_data["pincode"]
        request.session.modified = True
        return redirect("checkout_review")

    initial_pincode = request.session.get("pincode", "")
    context = {
        "saved_addresses": saved_addresses,
        "states": states,
        "form_data": {"pincode": initial_pincode},
        "breadcrumbs": [
            {"title": "Checkout", "url": "/checkout/"},
            {"title": "Delivery Address", "url": "/checkout/address/"},
        ],
    }
    return render(request, "orders/checkout_address.html", context)


@require_GET
def checkout_review(request: HttpRequest) -> HttpResponse:
    """
    Step 2: Order summary review and payment method selection.
    Displays stock hold timer (15 min) and exact GST breakdown.
    """
    cart = _get_cart(request)
    if not cart.items.exists():
        return redirect("cart_detail")

    address = request.session.get("checkout_address")
    if not address:
        messages.warning(request, "Please specify a delivery address.")
        return redirect("checkout_address")

    applied_code = request.session.get("applied_coupon_code", "").strip()
    coupon_discount = Decimal("0.00")
    if applied_code:
        user = request.user if request.user.is_authenticated else None
        res = validate_coupon(applied_code, cart, user=user)
        if res.is_valid:
            coupon_discount = res.discount_amount

    summary = calculate_cart_summary(
        cart=cart,
        buyer_state=address.get("state", ""),
        coupon_discount=coupon_discount,
        payment_method="cod",
    )

    est = estimate_delivery(address["pincode"])
    can_cod = est.cod_allowed and summary["grand_total"] <= Decimal("50000.00")
    can_razorpay = True

    context = {
        "cart": cart,
        "summary": summary,
        "address": address,
        "estimate": est,
        "can_cod": can_cod,
        "can_razorpay": can_razorpay,
        "hold_minutes": 15,
        "breadcrumbs": [
            {"title": "Checkout", "url": "/checkout/"},
            {"title": "Review & Payment", "url": "/checkout/review/"},
        ],
    }
    return render(request, "orders/checkout_review.html", context)


@ratelimit(key="ip", rate="10/m", block=False)
@require_POST
def checkout_place(request: HttpRequest) -> HttpResponse:
    """
    Step 3: Final atomic order placement.
    Converts cart to Order, locks stock reservations, and redirects to COD success or Razorpay page.
    """
    if getattr(request, "limited", False):
        messages.error(request, "Too many checkout requests. Please wait a moment.")
        return redirect("checkout_review")

    cart = _get_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    address = request.session.get("checkout_address")
    if not address:
        messages.error(request, "Delivery address missing.")
        return redirect("checkout_address")

    payment_method = request.POST.get("payment_method", "cod").strip()
    if payment_method not in ["cod", "razorpay"]:
        payment_method = "cod"

    customer_notes = request.POST.get("notes", "").strip()

    guest_info = request.session.get("checkout_guest", {})
    guest_email = guest_info.get("email", "")
    guest_phone = guest_info.get("phone", "")

    user = request.user if request.user.is_authenticated else None
    coupon_code = request.session.get("applied_coupon_code", "")

    seller_gstin = getattr(settings, "SELLER_GSTIN", "").strip()
    is_bill_of_supply = not bool(seller_gstin)

    try:
        order = place_order(
            cart=cart,
            user=user,
            guest_email=guest_email,
            guest_phone=guest_phone,
            shipping_address=address,
            billing_address=address,
            payment_method=payment_method,
            coupon_code=coupon_code,
            customer_notes=customer_notes,
            is_bill_of_supply=is_bill_of_supply,
        )
    except Exception as exc:
        messages.error(request, f"Could not place order: {exc}")
        return redirect("checkout_review")

    # Authorize session for this order
    token = str(uuid.uuid4())
    request.session[f"order_token_{order.order_number}"] = token

    # Clear checkout session transient data
    for key in ["checkout_guest", "checkout_address", "applied_coupon_code"]:
        if key in request.session:
            del request.session[key]
    request.session.modified = True

    if payment_method == "cod":
        messages.success(request, f"Order #{order.order_number} confirmed! We will dispatch your gear promptly.")
        return redirect(f"/orders/{order.order_number}/success/?token={token}")
    else:
        return redirect(f"/payments/razorpay/checkout/{order.order_number}/?token={token}")


# ==============================================================================
# ORDER MANAGEMENT & TRACKING
# ==============================================================================


@require_GET
def order_success(request: HttpRequest, order_number: str) -> HttpResponse:
    """
    Order placement confirmation and receipt summary page.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product", "items__product__media"),
        order_number=order_number,
    )

    if not _validate_order_access(request, order):
        raise Http404("Order not found or authorization token expired.")

    context = {
        "order": order,
        "is_cod": order.payment_method == "cod",
        "token": request.GET.get("token") or request.session.get(f"order_token_{order.order_number}"),
        "breadcrumbs": [{"title": f"Order #{order.order_number}", "url": f"/orders/{order.order_number}/success/"}],
    }
    return render(request, "orders/order_success.html", context)


@require_POST
def order_cancel(request: HttpRequest, order_number: str) -> HttpResponse:
    """
    Cancels an active order, releasing stock holds and issuing credit note if invoiced.
    """
    order = get_object_or_404(Order, order_number=order_number)

    if not _validate_order_access(request, order):
        messages.error(request, "Unauthorized to cancel this order.")
        return redirect("home")

    if not can_transition(order.status, Order.STATUS_CANCELLED):
        messages.error(request, f"Order #{order.order_number} cannot be cancelled in status '{order.get_status_display()}'.")
        return redirect("order_success", order_number=order.order_number)

    user = request.user if request.user.is_authenticated else None
    transition_order_status(
        order,
        Order.STATUS_CANCELLED,
        notes="Customer cancelled order via web interface.",
        changed_by=user,
    )

    messages.success(request, f"Order #{order.order_number} has been cancelled successfully. Inventory restored.")
    return redirect("order_success", order_number=order.order_number)


@require_GET
def order_invoice(request: HttpRequest, order_number: str) -> HttpResponse:
    """
    Printable statutory GST Tax Invoice or Bill of Supply with amounts in Indian words.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "credit_notes"),
        order_number=order_number,
    )

    if not _validate_order_access(request, order):
        raise Http404("Invoice authorization failed.")

    invoice = getattr(order, "invoice", None)
    if not invoice:
        invoice = generate_invoice(order)

    total_in_words = number_to_words_inr(order.total_amount)

    context = {
        "order": order,
        "invoice": invoice,
        "total_in_words": total_in_words,
        "credit_notes": order.credit_notes.all(),
    }
    return render(request, "orders/invoice.html", context)


@ratelimit(key="ip", rate="15/m", block=False)
def order_track_lookup(request: HttpRequest) -> HttpResponse:
    """
    Public lookup form to track shipment by order number and contact email/phone.
    """
    if getattr(request, "limited", False):
        messages.error(request, "Too many tracking lookups. Please wait a minute.")
        return redirect("home")

    if request.method == "POST":
        order_num = request.POST.get("order_number", "").strip().upper()
        contact = request.POST.get("contact", "").strip().lower()

        order = Order.objects.filter(order_number=order_num).first()
        if order:
            matches = False
            clean_digits = "".join(filter(str.isdigit, contact))

            if order.user and order.user.email and order.user.email.lower() == contact:
                matches = True
            elif order.guest_email and order.guest_email.lower() == contact:
                matches = True
            elif order.guest_phone and clean_digits and order.guest_phone == clean_digits:
                matches = True
            elif order.shipping_address_snapshot.get("phone") == clean_digits and clean_digits:
                matches = True

            if matches:
                request.session[f"track_grant_{order.order_number}"] = True
                request.session.modified = True
                return redirect("order_track_timeline", order_number=order.order_number)

        messages.error(request, "No order matching those details was found. Please check your order number and contact information.")

    return render(request, "orders/track_lookup.html", {"breadcrumbs": [{"title": "Track Order", "url": "/orders/track/"}]})


@require_GET
def order_track_timeline(request: HttpRequest, order_number: str) -> HttpResponse:
    """
    Displays shipment milestones and live tracking progress.
    """
    order = get_object_or_404(Order.objects.prefetch_related("status_history"), order_number=order_number)

    if not _validate_order_access(request, order):
        messages.warning(request, "Please enter your contact details to view shipment tracking.")
        return redirect("order_track_lookup")

    tracking_info = get_tracking_info(order)

    context = {
        "order": order,
        "tracking_info": tracking_info,
        "status_history": order.status_history.all(),
        "breadcrumbs": [
            {"title": "Track Order", "url": "/orders/track/"},
            {"title": f"Shipment #{order.order_number}", "url": f"/orders/track/{order.order_number}/verify/"},
        ],
    }
    return render(request, "orders/track_timeline.html", context)
