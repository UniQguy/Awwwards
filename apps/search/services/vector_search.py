"""
Hybrid Vector Semantic Search Engine for ELECTROCART (Phase R10, Pillar 5).
Uses scikit-learn (TfidfVectorizer + TruncatedSVD) with L2 cosine similarity.
Builds and maintains an in-memory dense vector index across active catalog products.
"""

from decimal import Decimal
import logging
import threading
import time
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from apps.catalog.models import Product

logger = logging.getLogger(__name__)

_INDEX_LOCK = threading.Lock()
_CACHED_INDEX = None
_CACHE_TTL_SECONDS = 3600  # 1 hour


class ProductVectorIndex:
    """
    In-memory vector search index for active products.
    Dense L2-normalized representations derived from TF-IDF + TruncatedSVD.
    """

    def __init__(self, doc_ids: np.ndarray, doc_matrix: np.ndarray, tfidf: TfidfVectorizer, svd: TruncatedSVD):
        self.doc_ids = doc_ids
        self.doc_matrix = doc_matrix  # Shape: (N, D), L2-normalized
        self.tfidf = tfidf
        self.svd = svd
        self.id_to_idx = {pid: idx for idx, pid in enumerate(doc_ids)}
        self.created_at = time.time()

    def rank(self, query: str, candidate_ids: Optional[Set[int]] = None, top_k: int = 200) -> Dict[int, float]:
        """
        Calculates cosine similarity scores for query across candidate products.
        Returns dict: {product_id: score} with score in [0.0, 1.0].
        Executes in < 15ms.
        """
        if not query or not query.strip():
            return {}

        clean_q = query.strip()
        try:
            q_tfidf = self.tfidf.transform([clean_q])
            if q_tfidf.nnz == 0:
                return {}
            q_svd = self.svd.transform(q_tfidf)
            q_norm = normalize(q_svd, norm="l2")
        except Exception as e:
            logger.debug("Vector transformation error: %s", e)
            return {}

        # Compute cosine similarity
        sims = np.dot(self.doc_matrix, q_norm.T).ravel()

        # If candidates restricted, mask or subset
        results: Dict[int, float] = {}
        if candidate_ids is not None:
            for pid in candidate_ids:
                idx = self.id_to_idx.get(pid)
                if idx is not None:
                    raw_score = float(sims[idx])
                    # Cosine score normalized to [0.0, 1.0]
                    norm_score = max(0.0, min(1.0, (raw_score + 1.0) / 2.0))
                    results[pid] = norm_score
            # Sort and trim top_k
            sorted_items = sorted(results.items(), key=lambda x: -x[1])[:top_k]
            return dict(sorted_items)
        else:
            top_indices = np.argsort(-sims)[:top_k]
            for idx in top_indices:
                pid = int(self.doc_ids[idx])
                raw_score = float(sims[idx])
                norm_score = max(0.0, min(1.0, (raw_score + 1.0) / 2.0))
                results[pid] = norm_score
            return results


def _build_product_index() -> ProductVectorIndex:
    """
    Builds vector index over all active products.
    Weighted features:
      - Title / display_name: 3x
      - Brand: 3x
      - Category: 2x
      - Specifications / search text: 1.5x
    """
    qs = (
        Product.objects.filter(is_available=True, selling_price__gt=Decimal("0.00"))
        .select_related("category")
        .only("id", "display_name", "raw_name", "parsed_brand", "category__name", "search_text")
    )

    doc_ids = []
    corpus = []

    for p in qs.iterator(chunk_size=1000):
        name = (p.display_name or p.raw_name or "").strip()
        brand = (p.parsed_brand or "").strip()
        cat = (p.category.name if p.category else "").strip()
        specs = (p.search_text or "")[:400].strip()

        # Weighted text document
        doc = f"{name} {name} {name} {brand} {brand} {brand} {cat} {cat} {specs}"
        corpus.append(doc)
        doc_ids.append(p.id)

    if not corpus:
        # Fallback empty dummy index
        doc_ids_arr = np.array([], dtype=int)
        doc_matrix = np.zeros((0, 16), dtype=np.float32)
        tfidf = TfidfVectorizer(ngram_range=(1, 2))
        tfidf.fit(["electronics hardware device"])
        svd = TruncatedSVD(n_components=1, random_state=42)
        svd.fit(tfidf.transform(["electronics hardware device"]))
        return ProductVectorIndex(doc_ids_arr, doc_matrix, tfidf, svd)

    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=12000,
        sublinear_tf=True,
        min_df=1,
    )
    X_tfidf = tfidf.fit_transform(corpus)

    n_features = X_tfidf.shape[1]
    n_samples = len(corpus)
    n_components = min(64, n_features - 1, n_samples - 1)
    if n_components < 2:
        n_components = 1

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    X_svd = svd.fit_transform(X_tfidf)
    X_norm = normalize(X_svd, norm="l2")

    return ProductVectorIndex(
        doc_ids=np.array(doc_ids, dtype=int),
        doc_matrix=X_norm,
        tfidf=tfidf,
        svd=svd,
    )


def invalidate_vector_index() -> None:
    """Clears cached vector index to force rebuilding on next request."""
    global _CACHED_INDEX
    with _INDEX_LOCK:
        _CACHED_INDEX = None


def get_vector_index(force_refresh: bool = False) -> ProductVectorIndex:
    """
    Returns thread-safe cached vector index singleton.
    Refreshes automatically if expired or forced.
    """
    global _CACHED_INDEX
    now = time.time()

    if _CACHED_INDEX is not None and not force_refresh:
        if now - _CACHED_INDEX.created_at < _CACHE_TTL_SECONDS:
            return _CACHED_INDEX

    with _INDEX_LOCK:
        if _CACHED_INDEX is not None and not force_refresh:
            if now - _CACHED_INDEX.created_at < _CACHE_TTL_SECONDS:
                return _CACHED_INDEX
        _CACHED_INDEX = _build_product_index()
        return _CACHED_INDEX


def vector_rank_products(
    query_string: str,
    candidate_ids: Optional[List[int]] = None,
    top_k: int = 200,
) -> Dict[int, float]:
    """
    Public entrypoint for vector similarity ranking.
    Returns {product_id: similarity_score} with score normalized [0.0, 1.0].
    """
    if not query_string or not query_string.strip():
        return {}
    index = get_vector_index()
    c_set = set(candidate_ids) if candidate_ids is not None else None
    return index.rank(query_string, candidate_ids=c_set, top_k=top_k)


def get_vector_search_recommendations(
    query: str,
    n: int = 3,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    category_slug: Optional[str] = None,
) -> List[Product]:
    """
    High-level semantic product recommender used by the AI Concierge and Smart Search.
    Finds top n genuine flagship/device recommendations matching natural language query.
    """
    index = get_vector_index()
    scores_dict = index.rank(query, top_k=100)
    if not scores_dict:
        return []

    p_ids = list(scores_dict.keys())
    qs = (
        Product.objects.filter(id__in=p_ids, is_available=True, selling_price__gt=Decimal("0.00"))
        .select_related("category")
        .prefetch_related("media")
    )
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if min_price is not None:
        qs = qs.filter(selling_price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(selling_price__lte=max_price)

    products = list(qs)
    # Sort by vector similarity score
    products.sort(key=lambda p: -scores_dict.get(p.id, 0.0))
    return products[:n]
