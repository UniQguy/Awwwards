"""
Catalog search and faceted exploration service for ELECTROCART.
Features:
- Multi-tier ranking:
  1. Exact SKU or title match
  2. All tokens as whole words
  3. Brand + Model match
  4. All tokens as prefixes
  5. Fuzzy fallback (typo & trigram/difflib)
- Synonym & plural/singular expansion (earbuds/earphone/headphone, tv/television, powerbank, mobile/phone/smartphone)
- Zero-result fallback: "Closest matches for X" with did-you-mean (never empty void)
- Near-duplicate collapse via family_key with "N options" count
- Deterministic tie-breaking: rating count desc, price asc
"""

from decimal import Decimal
import difflib
import re
from typing import Any, Dict, List, Optional, Set

from django.db.models import Count, Q, QuerySet

from apps.catalog.models import Category, Product
from apps.catalog.services.brands import get_known_brands
from apps.catalog.services.families import family_key
from apps.catalog.services.price_distribution import calculate_price_distribution


SYNONYM_GROUPS = [
    {"earbuds", "earbud", "earphone", "earphones", "headphone", "headphones"},
    {"tv", "tvs", "television", "televisions"},
    {"powerbank", "powerbanks", "power bank", "power banks"},
    {"mobile", "mobiles", "phone", "phones", "smartphone", "smartphones"},
]


def get_token_synonyms(token: str) -> Set[str]:
    """Returns synonyms and singular/plural variations for a token."""
    t = token.lower().strip()
    syns = {t}
    for group in SYNONYM_GROUPS:
        if t in group:
            syns.update(group)
    # Singularize common English plurals
    if t.endswith("s") and len(t) > 3:
        sing = t[:-1]
        syns.add(sing)
        for group in SYNONYM_GROUPS:
            if sing in group:
                syns.update(group)
    return syns


def calculate_match_score(
    product: Product,
    query_clean: str,
    tokens: List[str],
) -> int:
    """
    Ranks product candidate against clean query and tokens:
      1000: Exact SKU or exact title/raw_name match
       800: All tokens (or synonyms) match as whole words
       600: Brand + model match
       400: All tokens (or synonyms) match as word prefixes
       200+: Fuzzy similarity score (difflib)
         0: No match
    """
    p_sku = (product.sku or "").lower().strip()
    p_title = (product.display_name or "").lower().strip()
    p_raw = (product.raw_name or "").lower().strip()
    p_brand = (product.parsed_brand or "").lower().strip()
    p_search = (product.search_text or "").lower().strip()

    # 1. Exact SKU or title match
    if query_clean in (p_sku, p_title, p_raw):
        return 1000

    title_words = set(re.findall(r"\w+", p_title))
    search_words = set(re.findall(r"\w+", p_search)) | title_words

    # 2. All tokens as whole words (accounting for synonyms)
    all_tokens_as_whole_words = True
    for t in tokens:
        syns = get_token_synonyms(t)
        if not (syns & search_words):
            all_tokens_as_whole_words = False
            break
    if all_tokens_as_whole_words:
        return 800

    # 3. Brand + Model match
    # At least one token matches brand and at least one token matches a word in title/model
    brand_tokens = [t for t in tokens if t in p_brand or any(syn in p_brand for syn in get_token_synonyms(t))]
    model_tokens = [t for t in tokens if t in title_words or any(syn in title_words for syn in get_token_synonyms(t))]
    if brand_tokens and model_tokens:
        return 600

    # 4. All tokens as prefixes
    all_tokens_as_prefixes = True
    for t in tokens:
        syns = get_token_synonyms(t)
        if not any(any(w.startswith(syn) for syn in syns) for w in search_words):
            all_tokens_as_prefixes = False
            break
    if all_tokens_as_prefixes:
        return 400

    # 5. Fuzzy match (difflib)
    # Check overall title ratio or token-level fuzzy matches (handling typos like "hedphones")
    title_ratio = difflib.SequenceMatcher(None, query_clean, p_title).ratio()
    token_ratios = []
    for t in tokens:
        best_t = max((difflib.SequenceMatcher(None, t, w).ratio() for w in search_words), default=0.0)
        token_ratios.append(best_t)
    avg_token_ratio = sum(token_ratios) / len(token_ratios) if token_ratios else 0.0

    if title_ratio >= 0.55 or avg_token_ratio >= 0.65:
        fuzzy_score = int(max(title_ratio, avg_token_ratio) * 100)
        return 200 + fuzzy_score

    return 0


def execute_catalog_search(
    query: str = "",
    category_slug: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    min_rating: Optional[Decimal] = None,
    sort_by: str = "popularity",
    collapsed: bool = True,
) -> Dict[str, Any]:
    """
    Executes tiered catalog search with synonym matching, fuzzy typo correction,
    zero-result fallback, and family_key deduplication.
    """
    base_qs = (
        Product.objects.filter(is_available=True, selling_price__gt=0)
        .select_related("category", "inventory")
        .prefetch_related("media", "specifications")
    )

    # Apply faceted filters
    if category_slug:
        base_qs = base_qs.filter(category__slug=category_slug)
    if brand:
        base_qs = base_qs.filter(parsed_brand__iexact=brand)
    if min_price is not None:
        base_qs = base_qs.filter(selling_price__gte=min_price)
    if max_price is not None:
        base_qs = base_qs.filter(selling_price__lte=max_price)
    if min_rating is not None:
        base_qs = base_qs.filter(source_rating__gte=min_rating)

    clean_query = query.strip()
    is_fallback = False
    fallback_label = ""
    did_you_mean = None

    if not clean_query:
        # Standard unranked faceted exploration
        sort_options = {
            "popularity": ["-source_rating_count", "display_name"],
            "price_asc": ["selling_price", "id"],
            "price_desc": ["-selling_price", "id"],
            "rating": ["-source_rating", "-source_rating_count"],
            "newest": ["-created_at"],
        }
        order_fields = sort_options.get(sort_by, ["-source_rating_count", "display_name"])
        ordered_qs = base_qs.order_by(*order_fields)
        candidates = list(ordered_qs[:300])
        ranked_products = candidates
    else:
        tokens = [t.lower() for t in re.findall(r"\w+", clean_query) if len(t) > 0]
        query_lower = clean_query.lower()

        # Build candidate filter: exact SKU, full-text tokens, or expanded synonyms
        token_q = Q(sku__iexact=clean_query) | Q(display_name__icontains=clean_query)
        for t in tokens:
            for syn in get_token_synonyms(t):
                token_q |= Q(search_text__icontains=syn) | Q(parsed_brand__icontains=syn)

        candidate_qs = base_qs.filter(token_q)
        candidates = list(candidate_qs[:300])

        # If strict token match yields fewer than 5 items, pull broad candidates for fuzzy analysis
        if len(candidates) < 5:
            broad_q = Q()
            for t in tokens:
                broad_q |= Q(search_text__icontains=t[:3]) if len(t) >= 3 else Q(search_text__icontains=t)
            extra_candidates = list(base_qs.filter(broad_q).order_by("-source_rating_count")[:200])
            seen_ids = {p.id for p in candidates}
            for p in extra_candidates:
                if p.id not in seen_ids:
                    candidates.append(p)
                    seen_ids.add(p.id)

        # If candidates pool is still empty, pull top popular products as fallback pool
        if not candidates:
            candidates = list(base_qs.order_by("-source_rating_count")[:100])

        # Score and rank candidates
        scored_candidates = []
        for p in candidates:
            score = calculate_match_score(p, query_lower, tokens)
            rating_count = p.source_rating_count or 0
            price = p.selling_price or Decimal("999999.00")
            scored_candidates.append((score, rating_count, price, p))

        # Sort order: highest score, highest rating count, lowest price, id
        scored_candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[3].id))

        # Check if we have direct matches (score >= 400) or fuzzy matches (score > 0)
        exact_matches = [item[3] for item in scored_candidates if item[0] >= 400]
        fuzzy_matches = [item[3] for item in scored_candidates if 0 < item[0] < 400]

        if exact_matches:
            ranked_products = exact_matches + fuzzy_matches
        elif fuzzy_matches:
            is_fallback = True
            fallback_label = f"Closest matches for &ldquo;{clean_query}&rdquo;"
            ranked_products = fuzzy_matches
        else:
            # Zero results fallback: show closest matches labeled "Closest matches for X"
            is_fallback = True
            fallback_label = f"Closest matches for &ldquo;{clean_query}&rdquo;"
            ranked_products = [item[3] for item in scored_candidates[:24]]

        # Compute "did you mean" spelling suggestion
        known_vocab = list(get_known_brands()) + list(Category.objects.values_list("name", flat=True))
        synonym_flat = [w for grp in SYNONYM_GROUPS for w in grp]
        known_vocab.extend(synonym_flat)
        closest = difflib.get_close_matches(query_lower, known_vocab, n=1, cutoff=0.55)
        if closest and closest[0].lower() != query_lower:
            did_you_mean = closest[0]

    # Deduplicate near-duplicate variants using family_key
    if collapsed:
        family_map: Dict[str, List[Product]] = {}
        for p in ranked_products:
            f_key = family_key(p.raw_name) or p.display_name.lower().strip()
            if f_key not in family_map:
                family_map[f_key] = []
            family_map[f_key].append(p)

        collapsed_products = []
        for f_key, members in family_map.items():
            rep = members[0]
            rep.option_count = len(members)
            collapsed_products.append(rep)
        final_products = collapsed_products
    else:
        final_products = ranked_products

    # Facets computation
    category_facets = list(
        Category.objects.filter(products__is_available=True)
        .annotate(product_count=Count("products", filter=Q(products__selling_price__gt=0)))
        .values("name", "slug", "product_count")
        .order_by("-product_count")
    )

    brand_facets = list(
        Product.objects.filter(is_available=True, selling_price__gt=0)
        .exclude(parsed_brand="Unknown")
        .values("parsed_brand")
        .annotate(count=Count("id"))
        .order_by("-count")[:15]
    )

    price_histogram = calculate_price_distribution(base_qs)

    return {
        "products": final_products,
        "total_count": len(final_products),
        "query": clean_query,
        "did_you_mean": did_you_mean,
        "is_fallback": is_fallback,
        "fallback_label": fallback_label,
        "facets": {
            "categories": category_facets,
            "brands": brand_facets,
            "price_histogram": price_histogram,
        },
    }
