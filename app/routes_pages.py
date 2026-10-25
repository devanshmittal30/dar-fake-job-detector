"""app/routes_pages.py
Page routing blueprint for DAR Fake Job Detector.

Serves all 10 user-facing HTML views following:
- docs/03_TECHNICAL_DESIGN.md (section 7)
- docs/02_UI_UX_SPEC.md (section 3)
"""

from flask import Blueprint, render_template, request
from app.predictor import predict
from app.temp_store import TEMPORARY_RESULTS, get_demo_ad_result

bp_pages = Blueprint("pages", __name__)


@bp_pages.route("/")
def home():
    """Home landing page with hero banner, proof boxes, how-it-works, and ratings."""
    return render_template("home.html")


@bp_pages.route("/analyze")
def analyze():
    """Analyze job posting page (Text, Image/Camera, and Link inputs)."""
    return render_template("analyze.html")


@bp_pages.route("/result/<ad_id>")
def result(ad_id: str):
    """Result page displaying verdict, probability gauge, explainability, and voting.

    Follows docs/02_UI_UX_SPEC.md (section 8) and roadmap prompt P11.
    """
    model_override = request.args.get("model")
    # TEMPORARY: Lookup in-memory dictionary until P12 database
    res = TEMPORARY_RESULTS.get(ad_id)

    if not res:
        res = get_demo_ad_result(ad_id)

    # Allow model switching on the result page ("See the other model's result")
    if model_override in ("lr", "rf") and res.get("raw_text"):
        updated_res = predict(res["raw_text"], model_key=model_override)
        updated_res["raw_text"] = res["raw_text"]
        updated_res["model_key"] = model_override
        updated_res["word_count"] = res.get("word_count", len(res["raw_text"].split()))
        updated_res["source"] = res.get("source", "text")
        TEMPORARY_RESULTS[ad_id] = updated_res
        res = updated_res

    current_model = res.get("model_key", "lr")
    other_model_key = "rf" if current_model == "lr" else "lr"
    other_model_name = "Random Forest" if other_model_key == "rf" else "Logistic Regression"

    return render_template(
        "result.html",
        ad_id=ad_id,
        res=res,
        other_model_key=other_model_key,
        other_model_name=other_model_name
    )


@bp_pages.route("/community")
def community():
    """Community page with recent analyzed postings, vote filters, and search."""
    return render_template("community.html")


@bp_pages.route("/awareness")
def awareness():
    """Scam awareness page with animated statistics, fraud patterns, and safety advice."""
    return render_template("awareness.html")


@bp_pages.route("/performance")
def performance():
    """Model performance page showing accuracy, recall, confusion matrices, and ROC/PR curves."""
    return render_template("performance.html")


@bp_pages.route("/faq")
def faq():
    """Frequently Asked Questions accordion page."""
    return render_template("faq.html")


@bp_pages.route("/about")
def about():
    """About DAR page with mission, methodology, limitations, and creator bio."""
    return render_template("about.html")


@bp_pages.route("/auth")
def auth():
    """Authentication page (Login & Registration tabs)."""
    return render_template("auth.html")
