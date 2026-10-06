"""
Price distribution service for faceted filtering and histogram rendering.
Provides 9 logarithmic brackets with conditional aggregation and log-scaled bar heights.
"""

from decimal import Decimal
import math
from typing import Any, Dict, List, Optional
from django.db.models import Case, Count, IntegerField, Q, QuerySet, When


PRICE_BRACKETS = [
    {"index": 0, "label": "Under INR 500", "min": Decimal("0.00"), "max": Decimal("499.99")},
    {"index": 1, "label": "INR 500 - 999", "min": Decimal("500.00"), "max": Decimal("999.99")},
    {"index": 2, "label": "INR 1,000 - 2,499", "min": Decimal("1000.00"), "max": Decimal("2499.99")},
    {"index": 3, "label": "INR 2,500 - 4,999", "min": Decimal("2500.00"), "max": Decimal("4999.99")},
    {"index": 4, "label": "INR 5,000 - 9,999", "min": Decimal("5000.00"), "max": Decimal("9999.99")},
    {"index": 5, "label": "INR 10,000 - 19,999", "min": Decimal("10000.00"), "max": Decimal("19999.99")},
    {"index": 6, "label": "INR 20,000 - 39,999", "min": Decimal("20000.00"), "max": Decimal("39999.99")},
    {"index": 7, "label": "INR 40,000 - 79,999", "min": Decimal("40000.00"), "max": Decimal("79999.99")},
    {"index": 8, "label": "INR 80,000+", "min": Decimal("80000.00"), "max": None},
]


def calculate_price_distribution(queryset: QuerySet) -> List[Dict[str, Any]]:
    """
    Computes count and log-scaled height (0 to 100) for each of the 9 price brackets.
    Safe for SQLite: uses Count with Q filters.
    """
    aggregations = {}
    for b in PRICE_BRACKETS:
        idx = b["index"]
        min_p = b["min"]
        max_p = b["max"]
        if max_p is not None:
            cond = Q(selling_price__gte=min_p, selling_price__lte=max_p)
        else:
            cond = Q(selling_price__gte=min_p)
        aggregations[f"b_{idx}"] = Count("id", filter=cond)

    results = queryset.aggregate(**aggregations)

    counts = [results.get(f"b_{b['index']}", 0) for b in PRICE_BRACKETS]
    max_count = max(counts) if counts else 0

    bars: List[Dict[str, Any]] = []
    for b, count in zip(PRICE_BRACKETS, counts):
        if max_count > 0 and count > 0:
            # Log scale height between 10% and 100% to keep low-count bars visible
            log_ratio = math.log(count + 1) / math.log(max_count + 1)
            height_pct = round(10 + (log_ratio * 90), 1)
        else:
            height_pct = 0.0

        bars.append({
            "index": b["index"],
            "label": b["label"],
            "min_price": b["min"],
            "max_price": b["max"],
            "count": count,
            "height_percent": height_pct,
        })

    return bars
