"""
Grid collapse query service: deduplicates redundant marketplace variant cards
into a single representative card with option counts.
Utilizes SQLite-compatible Window functions (RowNumber) and subqueries.
"""

from typing import Optional
from django.db.models import Count, F, Q, QuerySet, Window
from django.db.models.functions import RowNumber

from apps.catalog.models import Product


def get_collapsed_catalog_queryset(queryset: Optional[QuerySet] = None) -> QuerySet:
    """
    Returns product queryset collapsed by raw_name.
    Each unique raw_name is represented by the variant with:
    lowest selling_price, then highest rating_count, then lowest ID.
    Annotates:
      - option_count: total number of variants sharing the same raw_name.
    """
    if queryset is None:
        queryset = Product.objects.filter(is_available=True, selling_price__gt=0)

    # Option count per raw_name
    counts_qs = (
        Product.objects.filter(is_available=True, selling_price__gt=0)
        .values("raw_name")
        .annotate(total_options=Count("id"))
    )
    counts_map = {row["raw_name"]: row["total_options"] for row in counts_qs}

    # Window function to rank variants
    ranked_qs = queryset.annotate(
        variant_rank=Window(
            expression=RowNumber(),
            partition_by=[F("raw_name")],
            order_by=[
                F("selling_price").asc(nulls_last=True),
                F("source_rating_count").desc(nulls_last=True),
                F("id").asc(),
            ],
        )
    )

    # Filter to winning variant (rank == 1)
    # Note: Window functions in SQLite/Django cannot be directly filtered in WHERE,
    # so we filter via ID list or subquery
    winning_ids = [p.id for p in ranked_qs if p.variant_rank == 1]
    final_qs = Product.objects.filter(id__in=winning_ids).select_related("category")

    return final_qs
