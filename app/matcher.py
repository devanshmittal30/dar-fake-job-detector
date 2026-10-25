"""app/matcher.py
Duplicate and near-duplicate job advertisement matching engine for DAR.

Following docs/03_TECHNICAL_DESIGN.md (section 5.4):
- Exact match: SHA-256 hash on normalized text (preprocess.clean_text via predictor.make_ad_id).
- Near-duplicate match: In-memory cache of newest 5,000 ads using TF-IDF character n-grams
  (analyzer="char_wb", ngram_range=(3, 5)) and cosine similarity with threshold 0.85.
"""

from collections import deque
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Ad
from app.predictor import make_ad_id
from ml.preprocess import clean_text

MAX_CACHE_SIZE = 5000
SIMILARITY_THRESHOLD = 0.85

# In-memory ad cache: deque of dicts {"ad_id": str, "clean_text": str}
_ad_cache: deque[dict[str, str]] = deque(maxlen=MAX_CACHE_SIZE)
_ad_id_set: set[str] = set()


def clear_cache() -> None:
    """Clear in-memory cache (primarily used in test fixtures)."""
    _ad_cache.clear()
    _ad_id_set.clear()


def index_ad(ad_id: str, text: str) -> None:
    """Add an ad to the in-memory matching cache.

    Args:
        ad_id: 64-character SHA-256 hash.
        text: Raw or cleaned job ad text.
    """
    if not ad_id or not text:
        return

    cleaned = clean_text(text)
    if not cleaned:
        return

    if ad_id in _ad_id_set:
        return

    # If cache is full, oldest item will be removed by deque; keep set in sync
    if len(_ad_cache) >= MAX_CACHE_SIZE:
        oldest = _ad_cache[0]
        _ad_id_set.discard(oldest["ad_id"])

    _ad_cache.append({"ad_id": ad_id, "clean_text": cleaned})
    _ad_id_set.add(ad_id)


def load_cache_from_db(limit: int = MAX_CACHE_SIZE) -> None:
    """Populate matcher cache with the newest ads from the database on startup."""
    try:
        newest_ads = Ad.query.order_by(Ad.first_checked_at.desc()).limit(limit).all()
        for ad in reversed(newest_ads):
            index_ad(ad.ad_id, ad.full_text)
    except Exception:
        # Database table might not be initialized yet on fresh test run
        pass


def find_matching_ad(text: str) -> str | None:
    """Check if the provided text matches an existing ad (exact or near-duplicate).

    Args:
        text: Raw job advertisement text.

    Returns:
        Existing ad_id if match found (exact or similarity >= 0.85), else None.
    """
    if not text or not str(text).strip():
        return None

    cleaned_query = clean_text(text)
    if not cleaned_query:
        return None

    # Step 1: Exact match via SHA-256
    exact_id = make_ad_id(text)

    # Check database for exact match
    try:
        from app.models import db
        existing_db_ad = db.session.get(Ad, exact_id)
        if existing_db_ad:
            index_ad(existing_db_ad.ad_id, existing_db_ad.full_text)
            return existing_db_ad.ad_id
    except Exception:
        pass

    # Check cache for exact match
    if exact_id in _ad_id_set:
        return exact_id

    # Step 2: Near-duplicate match against in-memory cache
    if not _ad_cache:
        return None

    cached_texts = [item["clean_text"] for item in _ad_cache]
    cached_ids = [item["ad_id"] for item in _ad_cache]

    # Vectorize with character n-grams (3 to 5) with word boundaries
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        sublinear_tf=True
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(cached_texts)
        query_vector = vectorizer.transform([cleaned_query])
        similarities = cosine_similarity(query_vector, tfidf_matrix)[0]

        best_idx = int(similarities.argmax())
        best_sim = float(similarities[best_idx])

        if best_sim >= SIMILARITY_THRESHOLD:
            return cached_ids[best_idx]
    except Exception:
        return None

    return None
