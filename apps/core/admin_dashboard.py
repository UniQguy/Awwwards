"""
Store Operations Admin Dashboard service.
Strictly read-only: never performs database writes.
Computes all currency aggregations using Python Decimal (never SQL Sum/Avg).
"""

from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Count, F, Q
from django.urls import reverse
from django.utils import timezone

from apps.accounts.views import mask_email
from apps.catalog.models import Product
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem

DASHBOARD_RANGE_DAYS = 7
ALLOWED_RANGES = (7, 30)


def resolve_range_days(range_param: Any) -> int:
    """Whitelist range parameter to 7 or 30 days, defaulting to DASHBOARD_RANGE_DAYS."""
    try:
        val = int(range_param)
        if val in ALLOWED_RANGES:
            return val
    except (TypeError, ValueError):
        pass
    return DASHBOARD_RANGE_DAYS


def get_admin_dashboard_context(range_days: int = DASHBOARD_RANGE_DAYS, request=None) -> Dict[str, Any]:
    """
    Builds context for the admin operations dashboard.
    Runs at most 7 focused queries, leaving ample budget under the 12-query limit.
    """
    if range_days not in ALLOWED_RANGES:
        range_days = DASHBOARD_RANGE_DAYS

    today = timezone.localdate()
    range_start_date = today - timedelta(days=range_days - 1)
    range_start_dt = timezone.make_aware(datetime.combine(range_start_date, time.min))

    # --------------------------------------------------------------------------
    # Query 1: Orders in selected range
    # --------------------------------------------------------------------------
    orders_in_range = list(
        Order.objects.filter(created_at__gte=range_start_dt).values(
            "id",
            "order_number",
            "created_at",
            "total_amount",
            "status",
            "payment_method",
            "guest_email",
            "user__email",
        )
    )

    # 1. KPI Calculations in Python Decimal
    orders_today_list = [o for o in orders_in_range if timezone.localtime(o["created_at"]).date() == today]
    orders_today_count = len(orders_today_list)
    revenue_today = sum(
        (Decimal(str(o["total_amount"])) for o in orders_today_list if o["status"] != Order.STATUS_CANCELLED),
        Decimal("0.00"),
    )

    orders_in_range_count = len(orders_in_range)
    non_cancelled_in_range = [o for o in orders_in_range if o["status"] != Order.STATUS_CANCELLED]
    revenue_in_range = sum(
        (Decimal(str(o["total_amount"])) for o in non_cancelled_in_range),
        Decimal("0.00"),
    )
    cancelled_orders_count = sum(1 for o in orders_in_range if o["status"] == Order.STATUS_CANCELLED)

    if non_cancelled_in_range:
        average_order_value = (revenue_in_range / len(non_cancelled_in_range)).quantize(Decimal("1.00"))
    else:
        average_order_value = Decimal("0.00")

    # --------------------------------------------------------------------------
    # Query 2: Pending orders (placed + confirmed + packed) across entire store
    # --------------------------------------------------------------------------
    pending_statuses = ["pending", "placed", "confirmed", "processing", "packed"]
    pending_orders_count = Order.objects.filter(status__in=pending_statuses).count()

    # --------------------------------------------------------------------------
    # 2. Orders per day for the range (SVG chart + accessible table fallback)
    # --------------------------------------------------------------------------
    day_counts_map = defaultdict(int)
    for o in orders_in_range:
        day_counts_map[timezone.localtime(o["created_at"]).date()] += 1

    orders_per_day: List[Dict[str, Any]] = []
    current_d = range_start_date
    while current_d <= today:
        cnt = day_counts_map[current_d]
        orders_per_day.append({
            "date": current_d,
            "label": current_d.strftime("%b %d") if range_days == 7 else current_d.strftime("%d/%m"),
            "full_label": current_d.strftime("%b %d, %Y"),
            "count": cnt,
        })
        current_d += timedelta(days=1)

    max_day_orders = max([d["count"] for d in orders_per_day] or [0])
    chart_max_y = max(max_day_orders + 2, 5)

    # Compute bar chart geometry for inline SVG (viewBox 0 0 500 160)
    chart_width = 500
    chart_height = 140
    y_baseline = 120
    n_days = len(orders_per_day)
    col_width = chart_width / n_days
    bar_width = max(int(col_width * 0.55), 6)

    svg_bars = []
    for idx, d in enumerate(orders_per_day):
        val = d["count"]
        bar_h = int((val / chart_max_y) * (y_baseline - 25)) if chart_max_y > 0 else 0
        bx = int(idx * col_width + (col_width - bar_width) / 2)
        by = y_baseline - bar_h
        text_y = max(by - 5, 15)
        svg_bars.append({
            "x": bx,
            "y": by,
            "width": bar_width,
            "height": max(bar_h, 2) if val > 0 else 0,
            "val": val,
            "label": d["label"],
            "center_x": bx + bar_width // 2,
            "text_y": text_y,
        })

    # --------------------------------------------------------------------------
    # 3. Orders by status (horizontal bars)
    # --------------------------------------------------------------------------
    status_display_map = {
        "pending": "Placed",
        "placed": "Placed",
        "confirmed": "Confirmed",
        "processing": "Packed",
        "packed": "Packed",
        "shipped": "Shipped",
        "delivered": "Delivered",
        "cancelled": "Cancelled",
        "refund_required": "Refund Required",
        "refunded": "Refunded",
    }
    status_color_map = {
        "Placed": "#3b82f6",
        "Confirmed": "#22c55e",
        "Packed": "#f59e0b",
        "Shipped": "#06b6d4",
        "Delivered": "#10b981",
        "Cancelled": "#ef4444",
        "Refund Required": "#ec4899",
        "Refunded": "#8b5cf6",
    }

    status_counts_map = defaultdict(int)
    for o in orders_in_range:
        st_label = status_display_map.get(o["status"], o["status"].title())
        status_counts_map[st_label] += 1

    preferred_order = ["Placed", "Confirmed", "Packed", "Shipped", "Delivered", "Cancelled"]
    orders_by_status = []
    max_status_count = max(status_counts_map.values()) if status_counts_map else 0
    for st_name in preferred_order:
        cnt = status_counts_map.get(st_name, 0)
        pct = int((cnt / max_status_count * 100)) if max_status_count > 0 else 0
        orders_by_status.append({
            "status": st_name,
            "count": cnt,
            "pct": max(pct, 4) if cnt > 0 else 0,
            "color": status_color_map.get(st_name, "#64748b"),
        })

    # --------------------------------------------------------------------------
    # 4. Payment split: COD vs online
    # --------------------------------------------------------------------------
    cod_count = sum(1 for o in orders_in_range if o["payment_method"] == Order.PAYMENT_METHOD_COD)
    online_count = sum(1 for o in orders_in_range if o["payment_method"] != Order.PAYMENT_METHOD_COD)
    total_split = cod_count + online_count
    if total_split > 0:
        cod_pct = round((cod_count / total_split) * 100)
        online_pct = 100 - cod_pct
    else:
        cod_pct = 0
        online_pct = 0

    payment_split = {
        "cod_count": cod_count,
        "cod_pct": cod_pct,
        "online_count": online_count,
        "online_pct": online_pct,
        "total_orders": total_split,
        # SVG ring stroke dash values (circumference for radius 40 = ~251.32)
        "cod_stroke": round((cod_pct / 100) * 251.32, 2),
        "online_stroke": round((online_pct / 100) * 251.32, 2),
    }

    # --------------------------------------------------------------------------
    # Query 3: OrderItem snapshots for Top Products and Top Categories
    # --------------------------------------------------------------------------
    order_items = list(
        OrderItem.objects.filter(order__created_at__gte=range_start_dt)
        .exclude(order__status=Order.STATUS_CANCELLED)
        .values(
            "product_id",
            "product_title",
            "product__category__name",
            "quantity",
            "line_total",
        )
    )

    product_sales: Dict[int, Dict[str, Any]] = {}
    category_sales: Dict[str, int] = defaultdict(int)

    for item in order_items:
        p_id = item["product_id"]
        title = item["product_title"]
        qty = item["quantity"]
        rev = Decimal(str(item["line_total"]))
        cat_name = item["product__category__name"] or "General"

        if p_id not in product_sales:
            product_sales[p_id] = {
                "product_id": p_id,
                "title": title,
                "units": 0,
                "revenue": Decimal("0.00"),
            }
        product_sales[p_id]["units"] += qty
        product_sales[p_id]["revenue"] += rev

        category_sales[cat_name] += qty

    top_products = sorted(
        product_sales.values(),
        key=lambda x: (-x["units"], -x["revenue"]),
    )[:5]

    top_categories = sorted(
        [{"name": k, "units": v} for k, v in category_sales.items()],
        key=lambda x: -x["units"],
    )[:5]

    # --------------------------------------------------------------------------
    # Query 4: Latest 8 orders table
    # --------------------------------------------------------------------------
    latest_orders_raw = list(
        Order.objects.select_related("user").order_by("-created_at")[:8]
    )
    latest_orders = []
    for ord_obj in latest_orders_raw:
        email = ord_obj.user.email if ord_obj.user else ord_obj.guest_email
        st_display = status_display_map.get(ord_obj.status, ord_obj.status.title())
        latest_orders.append({
            "id": ord_obj.id,
            "order_number": ord_obj.order_number,
            "change_url": reverse("admin:orders_order_change", args=[ord_obj.id]),
            "customer": mask_email(email) if email else "Guest",
            "total_amount": ord_obj.total_amount,
            "status": ord_obj.status,
            "status_label": st_display,
            "created_at": ord_obj.created_at,
        })

    # --------------------------------------------------------------------------
    # Query 5: Stock Health aggregates (low stock & out of stock)
    # Counts only purchasable products: is_available=True and selling_price > 0
    # --------------------------------------------------------------------------
    stock_counts = Inventory.objects.aggregate(
        low_stock=Count(
            "id",
            filter=Q(
                product__is_available=True,
                product__selling_price__gt=0,
                quantity__gt=0,
                quantity__lte=F("low_stock_threshold"),
            ),
        ),
        out_of_stock=Count(
            "id",
            filter=Q(
                product__is_available=True,
                product__selling_price__gt=0,
                quantity=0,
            ),
        ),
    )
    low_stock_count = stock_counts["low_stock"] or 0
    out_of_stock_count = stock_counts["out_of_stock"] or 0

    # --------------------------------------------------------------------------
    # Query 6: Only N list of 8 lowest-stock products that are purchasable
    # --------------------------------------------------------------------------
    lowest_stock_items_raw = list(
        Inventory.objects.filter(
            product__is_available=True,
            product__selling_price__gt=0,
            quantity__gt=0,
        )
        .select_related("product")
        .order_by("quantity", "product__display_name")[:8]
    )
    lowest_stock_products = [
        {
            "display_name": inv.product.display_name,
            "sku": inv.product.sku,
            "quantity": inv.quantity,
            "change_url": reverse("admin:catalog_product_change", args=[inv.product.id]),
        }
        for inv in lowest_stock_items_raw
    ]

    # --------------------------------------------------------------------------
    # Query 7: Catalogue health counts
    # --------------------------------------------------------------------------
    cat_health = Product.objects.aggregate(
        unpriced=Count("id", filter=Q(selling_price__isnull=True) | Q(selling_price=0), distinct=True),
        unknown_brand=Count(
            "id",
            filter=Q(parsed_brand__isnull=True) | Q(parsed_brand="") | Q(parsed_brand__iexact="Unknown"),
            distinct=True,
        ),
        no_image=Count("id", filter=Q(media__isnull=True), distinct=True),
    )
    catalogue_health = {
        "unpriced_products": cat_health["unpriced"] or 0,
        "products_without_images": cat_health["no_image"] or 0,
        "unknown_brand_products": cat_health["unknown_brand"] or 0,
    }

    # --------------------------------------------------------------------------
    # Quick links navigation
    # --------------------------------------------------------------------------
    quick_links = [
        {"title": "Orders", "url": reverse("admin:orders_order_changelist")},
        {"title": "Products", "url": reverse("admin:catalog_product_changelist")},
        {"title": "Inventory", "url": reverse("admin:inventory_inventory_changelist")},
        {"title": "Coupons", "url": reverse("admin:promotions_coupon_changelist")},
        {"title": "Shipping config", "url": reverse("admin:shipping_shippingconfig_changelist")},
        {"title": "Contact messages", "url": reverse("admin:core_contactmessage_changelist")},
    ]

    return {
        "range_days": range_days,
        "orders_today": orders_today_count,
        "revenue_today": revenue_today,
        "orders_in_range": orders_in_range_count,
        "revenue_in_range": revenue_in_range,
        "average_order_value": average_order_value,
        "pending_orders": pending_orders_count,
        "cancelled_orders": cancelled_orders_count,
        "orders_per_day": orders_per_day,
        "svg_bars": svg_bars,
        "chart_max_y": chart_max_y,
        "orders_by_status": orders_by_status,
        "payment_split": payment_split,
        "top_products": top_products,
        "top_categories": top_categories,
        "latest_orders": latest_orders,
        "stock_health": {
            "out_of_stock": out_of_stock_count,
            "low_stock": low_stock_count,
            "lowest_stock_products": lowest_stock_products,
        },
        "catalogue_health": catalogue_health,
        "quick_links": quick_links,
        # Backwards-compatible aliases for existing tests
        "low_stock_count": low_stock_count,
        "products_without_price": catalogue_health["unpriced_products"],
    }
