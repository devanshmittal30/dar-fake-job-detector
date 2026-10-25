"""app/routes_api.py
JSON API blueprint for DAR Fake Job Detector.

Implements endpoints specified in docs/03_TECHNICAL_DESIGN.md (section 7 & 9):
- POST /api/analyze: Text analysis and prediction engine
- POST /api/fetch: SSRF-safe URL content fetcher
"""

from flask import Blueprint, jsonify, request

from app.fetcher import FetchError, safe_fetch_job_text
from app.matcher import find_matching_ad, index_ad
from app.models import Ad, db
from app.ocr import OCRError, extract_text_from_image
from app.predictor import predict

bp_api = Blueprint("api", __name__, url_prefix="/api")


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
