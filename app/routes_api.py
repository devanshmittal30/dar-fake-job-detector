"""app/routes_api.py
JSON API blueprint for DAR Fake Job Detector.

Implements endpoints specified in docs/03_TECHNICAL_DESIGN.md (section 7 & 9):
- POST /api/analyze: Text analysis and prediction engine
- POST /api/fetch: SSRF-safe URL content fetcher
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify, request
from flask_login import current_user
from sqlalchemy import case, func

from app.fetcher import FetchError, safe_fetch_job_text
from app.matcher import find_matching_ad, index_ad
from app.models import Ad, Rating, User, Vote, db, utc_now
from app.ocr import OCRError, extract_text_from_image
from app.predictor import predict

bp_api = Blueprint("api", __name__, url_prefix="/api")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "models" / "model_config.json"
METRICS_FILE = PROJECT_ROOT / "models" / "metrics.json"
STATS_FILE = PROJECT_ROOT / "app" / "static" / "data" / "india_stats.json"


@bp_api.route("/analyze", methods=["POST"])
def analyze_job():
    """Analyze a job posting text and return verdict, confidence, and explanations.

    Expects JSON:
        {
            "text": str,
            "model": "lr" | "rf" (optional),
            "source": "text" | "image" | "link" (optional)
        }

    Validation rules (docs/02_UI_UX_SPEC.md section 7.1):
        - Empty text -> "Please paste the job ad text to analyze."
        - Fewer than 50 words -> "Please paste the full ad (at least 50 words)."
    """
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body expected."}), 400

    raw_text = data.get("text", "")
    if not raw_text or not str(raw_text).strip():
        return jsonify({"error": "Please paste the job ad text to analyze."}), 400

    text_str = str(raw_text).strip()
    words = text_str.split()
    if len(words) < 50:
        return jsonify({
            "error": "Please paste the full ad (at least 50 words).",
            "word_count": len(words)
        }), 400

    model_key = data.get("model", "lr")
    if model_key not in ("lr", "rf"):
        model_key = "lr"

    try:
        # 1. Check for existing exact or near-duplicate ad
        matched_ad_id = find_matching_ad(text_str)

        # 2. Compute AI prediction & explanations
        result = predict(text_str, model_key=model_key)
        result["raw_text"] = text_str
        result["model_key"] = model_key
        result["word_count"] = len(words)
        result["source"] = data.get("source", "text")

        # 3. Save or update in database (docs/03_TECHNICAL_DESIGN.md section 8)
        if matched_ad_id:
            existing_ad = db.session.get(Ad, matched_ad_id)
            if existing_ad:
                existing_ad.check_count += 1
                result["ad_id"] = existing_ad.ad_id
                result["check_count"] = existing_ad.check_count
                db.session.commit()
            else:
                matched_ad_id = None

        if not matched_ad_id:
            new_ad = Ad(
                ad_id=result["ad_id"],
                snippet=text_str[:200],
                full_text=text_str,
                ai_label=result["verdict"],
                ai_probability=result["probability"],
                model_used=model_key,
                check_count=1
            )
            db.session.add(new_ad)
            db.session.commit()
            index_ad(new_ad.ad_id, new_ad.full_text)
            result["check_count"] = 1

        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@bp_api.route("/fetch", methods=["POST"])
def fetch_job_url():
    """Safely fetch visible text from a job posting URL.

    Expects JSON:
        {
            "url": str
        }

    Returns:
        {"text": str} or {"error": str}
    """
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body expected."}), 400

    url = data.get("url", "")
    if not url or not str(url).strip():
        return jsonify({"error": "Please enter a valid job URL."}), 400

    try:
        extracted_text = safe_fetch_job_text(str(url).strip())
        return jsonify({"text": extracted_text}), 200
    except FetchError as fe:
        return jsonify({"error": str(fe)}), 400
    except Exception as e:
        return jsonify({
            "error": "We couldn't read that page (it may need a login). Paste the text instead."
        }), 400


@bp_api.route("/ocr", methods=["POST"])
def ocr_job_image():
    """Extract text from an uploaded job advertisement image.

    Expects multipart/form-data:
        file in request.files["image"] (JPG/PNG, max 5 MB)

    Returns:
        {"text": str} or {"error": "no_text_found", ...}
    """
    if "image" not in request.files:
        return jsonify({"error": "Please select an image file to upload."}), 400

    file = request.files["image"]
    if not file or not file.filename:
        return jsonify({"error": "No image selected."}), 400

    try:
        image_bytes = file.read()
        extracted_text = extract_text_from_image(image_bytes)
        return jsonify({"text": extracted_text}), 200
    except OCRError as oe:
        err_str = str(oe)
        if err_str == "no_text_found":
            return jsonify({
                "error": "no_text_found",
                "message": "We couldn't read any text. Try a clearer photo or paste the text instead."
            }), 400
        return jsonify({"error": err_str}), 400
    except Exception as e:
        return jsonify({"error": f"Image processing failed: {str(e)}"}), 500


def format_time_ago(dt: datetime | None) -> str:
    """Return friendly human-readable time elapsed string."""
    if not dt:
        return "recently"
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    years = months // 12
    return f"{years}y ago"


def check_disagreement(ai_label: str, fake_votes: int, genuine_votes: int) -> bool:
    """Check if AI verdict and community vote majority disagree (requires >= 3 votes).
    
    Following docs/01_PRD.md section 6.1:
    - If total votes >= 3 and AI verdict differs from majority, show amber disagreement note.
    """
    total = fake_votes + genuine_votes
    if total < 3:
        return False
    if fake_votes > genuine_votes:
        return ai_label in ("Likely Real", "Real")
    elif genuine_votes > fake_votes:
        return ai_label in ("Likely Fake", "Fake")
    return False


@bp_api.route("/ads/<ad_id>", methods=["GET"])
def get_ad_details(ad_id: str):
    """Retrieve ad details, AI verdict, and community vote counts.
    
    Response format (docs/03_TECHNICAL_DESIGN.md section 7):
        {"ad_id", "snippet", "ai_label", "ai_probability", "fake_votes", "genuine_votes", "my_vote"}
    """
    ad = db.session.get(Ad, ad_id)
    if not ad:
        return jsonify({"error": "Ad not found"}), 404

    fake_votes = Vote.query.filter_by(ad_id=ad.ad_id, vote="fake").count()
    genuine_votes = Vote.query.filter_by(ad_id=ad.ad_id, vote="genuine").count()
    total_votes = fake_votes + genuine_votes

    my_vote = None
    if current_user.is_authenticated:
        user_vote = Vote.query.filter_by(ad_id=ad.ad_id, user_id=current_user.id).first()
        if user_vote:
            my_vote = user_vote.vote

    disagreement = check_disagreement(ad.ai_label, fake_votes, genuine_votes)
    fake_percent = round((fake_votes / total_votes) * 100, 1) if total_votes > 0 else 0
    genuine_percent = round((genuine_votes / total_votes) * 100, 1) if total_votes > 0 else 0

    return jsonify({
        "ad_id": ad.ad_id,
        "snippet": ad.snippet,
        "ai_label": ad.ai_label,
        "ai_probability": ad.ai_probability,
        "fake_votes": fake_votes,
        "genuine_votes": genuine_votes,
        "total_votes": total_votes,
        "fake_percent": fake_percent,
        "genuine_percent": genuine_percent,
        "my_vote": my_vote,
        "disagreement": disagreement,
        "disagreement_message": (
            "The AI and the community disagree. Verify the company on its official website."
            if disagreement else None
        )
    }), 200


@bp_api.route("/ads/<ad_id>/vote", methods=["POST"])
def vote_ad(ad_id: str):
    """Submit or change community authenticity vote for an ad (login required).
    
    Request JSON:
        {"vote": "fake" | "genuine"}
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Login required"}), 401

    ad = db.session.get(Ad, ad_id)
    if not ad:
        return jsonify({"error": "Ad not found"}), 404

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body expected."}), 400

    vote = data.get("vote")
    if vote not in ("fake", "genuine"):
        return jsonify({"error": "Invalid vote value. Must be 'fake' or 'genuine'."}), 400

    # One vote per account per ad; changeable
    existing_vote = Vote.query.filter_by(user_id=current_user.id, ad_id=ad.ad_id).first()
    if existing_vote:
        existing_vote.vote = vote
        existing_vote.updated_at = utc_now()
    else:
        new_vote = Vote(user_id=current_user.id, ad_id=ad.ad_id, vote=vote)
        db.session.add(new_vote)

    db.session.commit()

    fake_votes = Vote.query.filter_by(ad_id=ad.ad_id, vote="fake").count()
    genuine_votes = Vote.query.filter_by(ad_id=ad.ad_id, vote="genuine").count()
    total_votes = fake_votes + genuine_votes

    disagreement = check_disagreement(ad.ai_label, fake_votes, genuine_votes)
    fake_percent = round((fake_votes / total_votes) * 100, 1) if total_votes > 0 else 0
    genuine_percent = round((genuine_votes / total_votes) * 100, 1) if total_votes > 0 else 0

    return jsonify({
        "ok": True,
        "ad_id": ad.ad_id,
        "fake_votes": fake_votes,
        "genuine_votes": genuine_votes,
        "total_votes": total_votes,
        "fake_percent": fake_percent,
        "genuine_percent": genuine_percent,
        "my_vote": vote,
        "disagreement": disagreement,
        "disagreement_message": (
            "The AI and the community disagree. Verify the company on its official website."
            if disagreement else None
        )
    }), 200


@bp_api.route("/ads/<ad_id>/rating", methods=["POST"])
def rate_ad(ad_id: str):
    """Submit a star rating (1 to 5) and optional comment up to 200 chars (login required).
    
    Request JSON:
        {"stars": 1-5, "comment": "optional, max 200"}
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "Login required"}), 401

    ad = db.session.get(Ad, ad_id)
    if not ad:
        return jsonify({"error": "Ad not found"}), 404

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid request. JSON body expected."}), 400

    raw_stars = data.get("stars")
    try:
        stars = int(raw_stars)
    except (TypeError, ValueError):
        return jsonify({"error": "Stars must be an integer between 1 and 5."}), 400

    if stars < 1 or stars > 5:
        return jsonify({"error": "Stars must be between 1 and 5."}), 400

    comment = data.get("comment")
    if comment is not None:
        comment = str(comment).strip()
        if len(comment) > 200:
            return jsonify({"error": "Comment must be 200 characters or fewer."}), 400
        if not comment:
            comment = None

    existing_rating = Rating.query.filter_by(user_id=current_user.id, ad_id=ad.ad_id).first()
    if existing_rating:
        existing_rating.stars = stars
        existing_rating.comment = comment
        existing_rating.approved = False
    else:
        new_rating = Rating(
            user_id=current_user.id,
            ad_id=ad.ad_id,
            stars=stars,
            comment=comment,
            approved=False
        )
        db.session.add(new_rating)

    db.session.commit()
    return jsonify({
        "ok": True,
        "message": "Thank you. Comments are reviewed before they appear on our home page."
    }), 200


@bp_api.route("/community", methods=["GET"])
def get_community():
    """List analyzed job ads with community verification stats, search, and filters.
    
    Query params:
        filter: "all" | "fake" | "genuine" | "disputed" (default "all")
        q: search keyword
        sort: "newest" | "votes" (default "newest")
        page: page number (default 1)
        
    Disputed rule (01_PRD.md F14):
        both sides have at least 3 votes and the smaller side at least 30%.
    """
    filter_type = request.args.get("filter", "all").strip().lower()
    search_q = request.args.get("q", "").strip()
    sort_type = request.args.get("sort", "newest").strip().lower()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    per_page = 12

    # Aggregate votes by ad_id using a subquery
    vote_sub = db.session.query(
        Vote.ad_id,
        func.coalesce(func.sum(case((Vote.vote == "fake", 1), else_=0)), 0).label("fake_votes"),
        func.coalesce(func.sum(case((Vote.vote == "genuine", 1), else_=0)), 0).label("genuine_votes")
    ).group_by(Vote.ad_id).subquery()

    fake_col = func.coalesce(vote_sub.c.fake_votes, 0)
    genuine_col = func.coalesce(vote_sub.c.genuine_votes, 0)
    total_col = fake_col + genuine_col

    query = db.session.query(
        Ad,
        fake_col.label("fake_count"),
        genuine_col.label("genuine_count")
    ).outerjoin(vote_sub, Ad.ad_id == vote_sub.c.ad_id)

    # Search keyword
    if search_q:
        query = query.filter(
            (Ad.snippet.ilike(f"%{search_q}%")) | (Ad.full_text.ilike(f"%{search_q}%"))
        )

    # Filter chips
    if filter_type == "fake":
        query = query.filter(fake_col > genuine_col)
    elif filter_type == "genuine":
        query = query.filter(genuine_col > fake_col)
    elif filter_type == "disputed":
        # Disputed: both sides >= 3 and min(fake, genuine) / total >= 30%
        # Equivalent to integer logic: fake >= 3 AND genuine >= 3 AND 7*fake >= 3*genuine AND 7*genuine >= 3*fake
        query = query.filter(
            fake_col >= 3,
            genuine_col >= 3,
            7 * fake_col >= 3 * genuine_col,
            7 * genuine_col >= 3 * fake_col
        )

    # Sort
    if sort_type == "votes":
        query = query.order_by(total_col.desc(), Ad.first_checked_at.desc())
    else:
        query = query.order_by(Ad.first_checked_at.desc())

    total_items = query.count()
    total_pages = max(1, (total_items + per_page - 1) // per_page)
    if page > total_pages and total_items > 0:
        page = total_pages

    records = query.offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for ad, fake_count, genuine_count in records:
        f_count = int(fake_count or 0)
        g_count = int(genuine_count or 0)
        t_count = f_count + g_count
        f_pct = round((f_count / t_count) * 100, 1) if t_count > 0 else 0
        g_pct = round((g_count / t_count) * 100, 1) if t_count > 0 else 0
        disputed = (
            f_count >= 3
            and g_count >= 3
            and 7 * f_count >= 3 * g_count
            and 7 * g_count >= 3 * f_count
        )

        items.append({
            "ad_id": ad.ad_id,
            "snippet": ad.snippet[:120] if ad.snippet else ad.full_text[:120],
            "ai_label": ad.ai_label,
            "ai_probability": round(ad.ai_probability * 100, 1),
            "fake_votes": f_count,
            "genuine_votes": g_count,
            "total_votes": t_count,
            "fake_percent": f_pct,
            "genuine_percent": g_pct,
            "is_disputed": disputed,
            "first_checked_at": ad.first_checked_at.isoformat() if ad.first_checked_at else None,
            "time_ago": format_time_ago(ad.first_checked_at)
        })

    return jsonify({
        "items": items,
        "page": page,
        "pages": total_pages,
        "total": total_items
    }), 200


@bp_api.route("/home", methods=["GET"])
def get_home_data():
    """Return live metrics for proof boxes and approved user reviews for Home page.
    
    Response format (docs/03_TECHNICAL_DESIGN.md section 7):
        {
            "analyses_total": int,
            "training_rows": int | "n/a",
            "accuracy": float | "n/a",
            "recall": float | "n/a",
            "precision": float | "n/a",
            "avg_rating": float | None,
            "rating_count": int,
            "distribution": {"1": int, "2": int, "3": int, "4": int, "5": int},
            "reviews": [{"stars": int, "comment": str, "first_name": str, "date": str}]
        }
    """
    # 1. Total jobs checked across the platform
    total_checks = db.session.query(func.coalesce(func.sum(Ad.check_count), 0)).scalar() or 0

    # 2. Training rows and test metrics
    training_rows = "n/a"
    accuracy = "n/a"
    recall = "n/a"
    precision = "n/a"
    default_model = "lr"

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                training_rows = cfg.get("training_row_count", "n/a")
                default_model = cfg.get("default_model", "lr")
        except Exception:
            pass

    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                metrics = json.load(f)
                test_m = metrics.get(default_model, {}).get("test", {})
                if "accuracy" in test_m:
                    accuracy = round(float(test_m["accuracy"]) * 100, 1)
                if "recall" in test_m:
                    recall = round(float(test_m["recall"]) * 100, 1)
                if "precision" in test_m:
                    precision = round(float(test_m["precision"]) * 100, 1)
        except Exception:
            pass

    # 3. Overall ratings and star distribution
    rating_count = Rating.query.count()
    raw_avg = db.session.query(func.avg(Rating.stars)).scalar()
    avg_rating = round(float(raw_avg), 1) if raw_avg is not None else None

    distribution = {str(i): 0 for i in range(1, 6)}
    dist_query = db.session.query(Rating.stars, func.count(Rating.id)).group_by(Rating.stars).all()
    for s_val, count_val in dist_query:
        if 1 <= s_val <= 5:
            distribution[str(s_val)] = count_val

    # 4. Up to 6 newest approved reviews with 4 or 5 stars
    approved_ratings = (
        Rating.query
        .filter(
            Rating.approved == True,
            Rating.stars.in_([4, 5]),
            Rating.comment.isnot(None),
            Rating.comment != ""
        )
        .order_by(Rating.created_at.desc())
        .limit(6)
        .all()
    )

    reviews = []
    for r in approved_ratings:
        first_name = "Anonymous"
        if r.user and r.user.name:
            first_name = r.user.name.strip().split()[0]
        date_str = r.created_at.strftime("%b %d, %Y") if r.created_at else ""

        reviews.append({
            "stars": r.stars,
            "comment": r.comment,
            "first_name": first_name,
            "date": date_str
        })

    return jsonify({
        "analyses_total": total_checks,
        "training_rows": training_rows,
        "accuracy": accuracy,
        "recall": recall,
        "precision": precision,
        "avg_rating": avg_rating,
        "rating_count": rating_count,
        "distribution": distribution,
        "reviews": reviews
    }), 200


@bp_api.route("/stats", methods=["GET"])
def get_india_stats():
    """Return Indian cyber fraud and scam awareness statistics from india_stats.json.
    
    Response format (docs/03_TECHNICAL_DESIGN.md section 7 & 02_UI_UX_SPEC.md section 14).
    """
    if not STATS_FILE.exists():
        return jsonify({"error": "Statistics data not found"}), 404
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load statistics: {str(e)}"}), 500


@bp_api.route("/metrics", methods=["GET"])
def get_model_metrics():
    """Return model performance metrics and configuration without server paths.
    
    Response format (docs/03_TECHNICAL_DESIGN.md section 7):
        {"metrics": {...}, "config": {...}}
    """
    metrics_content = {}
    config_content = {}

    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                metrics_content = json.load(f)
        except Exception:
            pass

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_content = json.load(f)
        except Exception:
            pass

    # Sanitize config: exclude any potential filesystem paths
    sanitized_config = {k: v for k, v in config_content.items() if not k.endswith("_path")}

    return jsonify({
        "metrics": metrics_content,
        "config": sanitized_config
    }), 200

