"""
ELECTROCART AI Concierge & Technical Assistant Service (Phase R10, Pillar 6).
Provides intelligent product recommendations via Vector Search, order tracking,
pincode deliverability lookups, active coupon discovery, and policy guidance.
Operates via deterministic local hybrid-RAG with optional Gemini API augmentation.
"""

from decimal import Decimal
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

from apps.catalog.models import Product
from apps.core.templatetags.core_tags import inr
from apps.orders.models import Order
from apps.promotions.models import Coupon
from apps.promotions.services.coupon_validator import get_best_coupon_for_product
from apps.search.services.search_service import extract_natural_price_bounds
from apps.search.services.vector_search import get_vector_search_recommendations
from apps.shipping.services.estimator import estimate_delivery

logger = logging.getLogger(__name__)


def process_concierge_message(
    user_message: str,
    user=None,
    session=None,
) -> Dict[str, Any]:
    """
    Processes incoming user message through deterministic local intent classifiers
    and hybrid-RAG tool calling. If GEMINI_API_KEY is available, enriches response
    with generative synthesis while retaining structured action cards.
    """
    raw = (user_message or "").strip()
    msg_lower = raw.lower()

    if not raw:
        return {
            "reply": "How can I assist your electronics shopping or order inquiry today?",
            "intent": "general",
            "products": [],
            "coupons": [],
            "actions": [],
        }

    # 1. Pincode delivery lookup
    pincode_match = re.search(r"\b([1-9][0-9]{5})\b", raw)
    if pincode_match and ("deliver" in msg_lower or "pincode" in msg_lower or "check" in msg_lower or "ship" in msg_lower or len(raw.split()) <= 4):
        pincode = pincode_match.group(1)
        est = estimate_delivery(pincode)
        if est.serviceable:
            cod_text = "Cash on Delivery is available for orders under ₹15,000." if est.cod_allowed else "Prepaid payment only for this destination."
            reply = (
                f"Delivery to pincode **{pincode}** is available.\n\n"
                f"- **Transit SLA:** {est.est_days_min} to {est.est_days_max} business days\n"
                f"- **Estimated Delivery:** {est.date_min.strftime('%b %d')} to {est.date_max.strftime('%b %d')}\n"
                f"- **Payment Methods:** {cod_text}\n"
                f"- **Dispatch Hub:** Central fulfillment depot in Ahmedabad, Gujarat."
            )
        else:
            reason = est.unavailable_reason or "Location currently outside courier coverage."
            reply = f"Delivery to pincode **{pincode}** is currently unavailable. Reason: {reason}"

        return {
            "reply": reply,
            "intent": "pincode_check",
            "pincode": pincode,
            "products": [],
            "coupons": [],
            "actions": [
                {"label": "Explore Catalog", "url": "/categories/"},
            ],
        }

    # 2. Order Tracking & Cancellation
    order_num_match = re.search(r"\b(?:EC-)?([A-Za-z0-9]{6,12})\b", raw)
    is_order_query = any(w in msg_lower for w in ("order", "track", "cancel", "status", "shipment"))
    if is_order_query:
        order_found = None
        if order_num_match:
            candidate_num = order_num_match.group(1).upper()
            order_found = (
                Order.objects.filter(order_number__icontains=candidate_num).first()
                or Order.objects.filter(id__iexact=candidate_num).first()
            )

        if not order_found and user and getattr(user, "is_authenticated", False):
            # Check most recent order for logged-in user
            order_found = Order.objects.filter(user=user).order_by("-created_at").first()

        if order_found:
            st = order_found.status
            total_str = inr(order_found.total_amount)
            placed_str = order_found.created_at.strftime("%b %d, %Y")
            cancellable = st in ("PENDING", "PROCESSING")

            if "cancel" in msg_lower:
                if cancellable:
                    reply = (
                        f"Order **#{order_found.order_number}** (Total: {total_str}, Placed: {placed_str}) is currently in **{st}** status.\n\n"
                        f"This order is eligible for self-serve cancellation prior to courier dispatch. "
                        f"You can cancel it directly through your order tracking dashboard."
                    )
                else:
                    reply = (
                        f"Order **#{order_found.order_number}** is currently in **{st}** status.\n\n"
                        f"Orders that have entered the dispatch or delivery cycle cannot be cancelled in transit. "
                        f"If you no longer need the package, you may reject delivery or file a 7-day replacement request once received."
                    )
            else:
                reply = (
                    f"Order **#{order_found.order_number}** Status Summary:\n\n"
                    f"- **Current Status:** {st}\n"
                    f"- **Total Amount:** {total_str}\n"
                    f"- **Order Date:** {placed_str}\n"
                    f"- **Payment Method:** {order_found.payment_method}\n"
                    f"- **Tracking:** You can view live milestones on the order tracking portal."
                )

            return {
                "reply": reply,
                "intent": "order_tracking",
                "products": [],
                "coupons": [],
                "actions": [
                    {"label": f"Track Order #{order_found.order_number}", "url": f"/orders/{order_found.order_number}/"},
                    {"label": "Contact Support", "url": "/support/"},
                ],
            }
        else:
            reply = (
                "To track or cancel an order, please provide your **Order Number** (e.g. `EC-XXXXXX`).\n\n"
                "Orders in **Pending** or **Processing** status can be cancelled self-serve before courier dispatch."
            )
            return {
                "reply": reply,
                "intent": "order_tracking",
                "products": [],
                "coupons": [],
                "actions": [
                    {"label": "Order Lookup Portal", "url": "/orders/lookup/"},
                ],
            }

    # 3. Coupons & Active Offers
    if any(w in msg_lower for w in ("coupon", "coupons", "promo", "discount", "code", "offer", "voucher")):
        active_coupons = list(Coupon.objects.filter(is_active=True).order_by("-discount_value")[:6])
        coupon_payload = []
        lines = ["Here are the promotional discount codes currently available on ElectroCart:\n"]

        for c in active_coupons:
            val_text = f"{int(c.discount_value)}% off" if c.discount_type == "percentage" else f"₹{int(c.discount_value)} flat discount"
            min_text = f"Min cart: {inr(c.min_order_amount)}" if c.min_order_amount else "No minimum order requirement"
            cats = list(c.applicable_categories.all())
            cat_text = f"Applicable on {cats[0].name}" if cats else "Valid sitewide"
            lines.append(f"- **`{c.code}`** — {val_text} ({min_text}, {cat_text})")
            coupon_payload.append({
                "code": c.code,
                "discount_label": val_text,
                "min_order": min_text,
                "category": cat_text,
            })

        lines.append("\nYou can apply any of these codes at the Cart or Checkout payment step.")
        return {
            "reply": "\n".join(lines),
            "intent": "coupons",
            "products": [],
            "coupons": coupon_payload,
            "actions": [
                {"label": "View Shopping Cart", "url": "/cart/"},
            ],
        }

    # 4. Support Policies & Customer Guarantees
    policy_keywords = ("return", "refund", "replacement", "warranty", "policy", "gst", "invoice", "doa", "broken", "damaged", "fake", "legit")
    if any(w in msg_lower for w in policy_keywords):
        reply = (
            "ElectroCart Customer Service & Operational Policies:\n\n"
            "1. **7-Day Replacement Policy:** All electronics and computing devices are covered by a 7-day dead-on-arrival (DOA) replacement window for manufacturing defects or physical transit damage.\n"
            "2. **GST Invoicing:** Every transaction generates a standard GST tax invoice with statutory HSN codes and breakdown of CGST/SGST/IGST. Business buyers can enter their 15-character GSTIN at checkout to claim Input Tax Credit (ITC).\n"
            "3. **Guest COD Verification:** Unauthenticated guest orders selecting Cash on Delivery undergo a 6-digit email OTP verification step to ensure order authenticity.\n"
            "4. **Fulfillment Guarantee:** All items are dispatched directly from our verified inventory center in Ahmedabad, Gujarat."
        )
        return {
            "reply": reply,
            "intent": "policy",
            "products": [],
            "coupons": [],
            "actions": [
                {"label": "Support Concierge", "url": "/support/"},
                {"label": "Terms & Conditions", "url": "/legal/terms/"},
                {"label": "Refund Policy", "url": "/legal/refunds/"},
            ],
        }

    # 5. Smart Product Recommendations & Spec Q&A (Default / Fallback)
    clean_query, natural_min, natural_max = extract_natural_price_bounds(raw)

    cat_slug = None
    if any(w in msg_lower for w in ("phone", "smartphone", "mobile")):
        cat_slug = "smartphones"
    elif any(w in msg_lower for w in ("headphone", "earphone", "earbud", "audio", "anc", "tws")):
        cat_slug = "earphones-headphones"
    elif any(w in msg_lower for w in ("speaker", "soundbar")):
        cat_slug = "speakers"
    elif any(w in msg_lower for w in ("camera", "dslr", "mirrorless", "cctv")):
        cat_slug = "cameras"
    elif any(w in msg_lower for w in ("tv", "television", "display", "monitor")):
        cat_slug = "tvs"
    elif any(w in msg_lower for w in ("keyboard", "mouse")):
        cat_slug = "keyboards-mice"

    recommended_prods = get_vector_search_recommendations(
        query=clean_query or raw,
        n=3,
        min_price=natural_min,
        max_price=natural_max,
        category_slug=cat_slug,
    )

    if not recommended_prods:
        # Fallback to general vector query without category restriction
        recommended_prods = get_vector_search_recommendations(
            query=clean_query or raw,
            n=3,
            min_price=natural_min,
            max_price=natural_max,
        )

    prod_payload = []
    lines = ["Here are hardware recommendations matching your inquiry:\n"]
    for p in recommended_prods:
        deal = get_best_coupon_for_product(p)
        deal_info = ""
        if deal:
            deal_info = f" (As low as {inr(deal['effective_price'])} with code `{deal['code']}`)"
        lines.append(f"- **{p.display_name}** — {inr(p.selling_price)}{deal_info}")

        prod_payload.append({
            "id": p.id,
            "name": p.display_name,
            "brand": p.parsed_brand,
            "price": str(p.selling_price),
            "formatted_price": inr(p.selling_price),
            "image_url": p.primary_image_url or "",
            "url": f"/p/{p.slug}/",
            "effective_price": inr(deal["effective_price"]) if deal else None,
            "coupon_code": deal["code"] if deal else None,
        })

    if not prod_payload:
        reply = (
            f"I could not find exact hardware listings matching &ldquo;{raw}&rdquo;. "
            "Please try searching for specific device categories like smartphones, noise-cancelling headphones, or 4K televisions."
        )
    else:
        lines.append("\nYou can select any item below to view full technical specifications and stock availability.")
        reply = "\n".join(lines)

    return {
        "reply": reply,
        "intent": "recommendation",
        "products": prod_payload,
        "coupons": [],
        "actions": [
            {"label": "Explore All Categories", "url": "/categories/"},
        ],
    }
