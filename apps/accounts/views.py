"""
Customer account views: dashboard, order history, address management, and profile settings.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.models import Address, IndianState
from apps.orders.models import Order
from apps.shipping.services.estimator import estimate_delivery


@login_required
@require_GET
def account_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Overview hub displaying customer profile snapshot, recent orders, and default address.
    """
    recent_orders = (
        request.user.orders.prefetch_related("items")
        .order_by("-created_at")[:5]
    )
    default_address = (
        request.user.addresses.filter(is_default=True).first()
        or request.user.addresses.first()
    )

    context = {
        "user": request.user,
        "recent_orders": recent_orders,
        "default_address": default_address,
        "breadcrumbs": [{"title": "Account", "url": "/account/"}],
    }
    return render(request, "account/dashboard.html", context)


@login_required
@require_GET
def account_order_list(request: HttpRequest) -> HttpResponse:
    """
    Paginated complete order history for authenticated customer.
    """
    orders_qs = (
        request.user.orders.prefetch_related("items")
        .order_by("-created_at")
    )
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "breadcrumbs": [
            {"title": "Account", "url": "/account/"},
            {"title": "Orders", "url": "/account/orders/"},
        ],
    }
    return render(request, "account/order_list.html", context)


@login_required
@require_GET
def account_order_detail(request: HttpRequest, order_number: str) -> HttpResponse:
    """
    Customer portal view of a specific historical order.
    """
    order = get_object_or_404(
        request.user.orders.prefetch_related("items__product", "status_history"),
        order_number=order_number,
    )

    context = {
        "order": order,
        "breadcrumbs": [
            {"title": "Account", "url": "/account/"},
            {"title": "Orders", "url": "/account/orders/"},
            {"title": f"Order #{order.order_number}", "url": f"/account/orders/{order.order_number}/"},
        ],
    }
    return render(request, "account/order_detail.html", context)


@login_required
@require_GET
def account_address_list(request: HttpRequest) -> HttpResponse:
    """
    List of all saved shipping addresses.
    """
    addresses = request.user.addresses.order_by("-is_default", "-created_at")
    context = {
        "addresses": addresses,
        "breadcrumbs": [
            {"title": "Account", "url": "/account/"},
            {"title": "Addresses", "url": "/account/addresses/"},
        ],
    }
    return render(request, "account/address_list.html", context)


@login_required
def account_address_form(request: HttpRequest, uuid=None) -> HttpResponse:
    """
    Create or edit saved address with PIN code validation.
    """
    address = None
    if uuid:
        address = get_object_or_404(Address, uuid=uuid, user=request.user)

    states = IndianState.choices

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = "".join(filter(str.isdigit, request.POST.get("phone", "").strip()))
        line1 = request.POST.get("line1", "").strip()
        line2 = request.POST.get("line2", "").strip()
        landmark = request.POST.get("landmark", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        is_default = request.POST.get("is_default") == "1"

        if not (full_name and line1 and city and state and pincode):
            messages.error(request, "Please fill in all mandatory address fields.")
            return render(request, "account/address_form.html", {
                "address": address,
                "states": states,
                "form_data": request.POST,
            })

        if len(phone) != 10:
            messages.error(request, "Please enter a valid 10-digit Indian phone number.")
            return render(request, "account/address_form.html", {
                "address": address,
                "states": states,
                "form_data": request.POST,
            })

        est = estimate_delivery(pincode)
        if not est.serviceable:
            messages.error(request, est.unavailable_reason or f"PIN code {pincode} is not serviceable for shipping.")
            return render(request, "account/address_form.html", {
                "address": address,
                "states": states,
                "form_data": request.POST,
            })

        if is_default:
            request.user.addresses.update(is_default=False)

        if address:
            address.full_name = full_name
            address.phone = phone
            address.line1 = line1
            address.line2 = line2
            address.landmark = landmark
            address.city = city
            address.state = state
            address.pincode = pincode
            if is_default:
                address.is_default = True
            address.save()
            messages.success(request, "Address updated successfully.")
        else:
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
                is_default=is_default or not request.user.addresses.exists(),
            )
            messages.success(request, "Address saved successfully.")

        return redirect("account_address_list")

    context = {
        "address": address,
        "states": states,
        "form_data": address,
        "breadcrumbs": [
            {"title": "Account", "url": "/account/"},
            {"title": "Addresses", "url": "/account/addresses/"},
            {"title": "Edit Address" if address else "Add Address", "url": "#"},
        ],
    }
    return render(request, "account/address_form.html", context)


@login_required
@require_POST
def account_address_delete(request: HttpRequest, uuid) -> HttpResponseRedirect:
    """
    Deletes a saved address.
    """
    address = get_object_or_404(Address, uuid=uuid, user=request.user)
    was_default = address.is_default
    address.delete()

    if was_default:
        next_addr = request.user.addresses.first()
        if next_addr:
            next_addr.is_default = True
            next_addr.save(update_fields=["is_default"])

    messages.info(request, "Address deleted.")
    return redirect("account_address_list")


@login_required
@require_POST
def account_address_set_default(request: HttpRequest, uuid) -> HttpResponseRedirect:
    """
    Sets an address as the primary default.
    """
    address = get_object_or_404(Address, uuid=uuid, user=request.user)
    request.user.addresses.exclude(id=address.id).update(is_default=False)
    address.is_default = True
    address.save(update_fields=["is_default"])
    messages.success(request, "Default shipping address updated.")
    return redirect("account_address_list")


@login_required
def account_profile(request: HttpRequest) -> HttpResponse:
    """
    Edits customer name and telephone.
    """
    user = request.user
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        user.full_name = full_name
        user.save(update_fields=["full_name", "updated_at"])
        messages.success(request, "Profile details updated successfully.")
        return redirect("account_profile")

    context = {
        "user": user,
        "breadcrumbs": [
            {"title": "Account", "url": "/account/"},
            {"title": "Profile", "url": "/account/profile/"},
        ],
    }
    return render(request, "account/profile.html", context)


def mask_email(email: str) -> str:
    """Masks local part of email: john.doe@example.com -> jo***e@example.com."""
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@", 1)
    user_part = parts[0]
    domain_part = parts[1]
    if len(user_part) <= 2:
        masked_user = user_part[0] + "***"
    else:
        masked_user = user_part[:2] + "***" + user_part[-1]
    return f"{masked_user}@{domain_part}"


@require_GET
def email_verification_sent_view(request: HttpRequest) -> HttpResponse:
    """
    Renders verification sent notice displaying the masked recipient email
    and providing a functional Resend confirmation button.
    """
    from django.conf import settings
    signup_email = request.session.get("account_verification_email", "")
    masked = mask_email(signup_email) if signup_email else ""
    context = {
        "signup_email": signup_email,
        "masked_email": masked,
        "demo_email_fallback": getattr(settings, "DEMO_EMAIL_FALLBACK", False),
    }
    return render(request, "account/verification_sent.html", context)


@require_POST
def resend_verification_email(request: HttpRequest) -> HttpResponse:
    """
    Resends account verification email for an unverified user.
    """
    email = request.POST.get("email", "").strip() or request.session.get("account_verification_email", "").strip()
    if email:
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            email_addr = EmailAddress.objects.filter(user=user, email__iexact=email).first()
            if not email_addr:
                email_addr = EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    primary=True,
                    verified=False,
                )
            if not email_addr.verified:
                email_addr.send_confirmation(request, signup=False)
                masked = mask_email(email)
                messages.success(request, f"A new confirmation link has been sent to {masked}.")
            else:
                messages.info(request, "This email address is already verified.")
        else:
            messages.info(request, "If an unverified account exists with that email, a confirmation link has been sent.")
    else:
        messages.error(request, "Could not determine email address to resend confirmation.")
    return redirect("account_email_verification_sent")

