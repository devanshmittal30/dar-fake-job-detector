"""app/routes_pages.py
Page routing blueprint for DAR Fake Job Detector.

Serves all 10 user-facing HTML views following:
- docs/03_TECHNICAL_DESIGN.md (section 7)
- docs/02_UI_UX_SPEC.md (section 3)
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from app.models import Ad, db
from app.predictor import predict

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

    Follows docs/02_UI_UX_SPEC.md (section 8) and roadmap prompt P11 & P12.
    """
    model_override = request.args.get("model")
    ad = db.session.get(Ad, ad_id)

    # For standalone testing / demo visits, auto-seed demo Ad if requested
    if not ad and (ad_id.startswith("demo_") or ad_id.startswith("test_")):
        demo_text = (
            "URGENT HIRING: Data Entry Operator needed immediately. Work from home and earn 45,000 rupees "
            "weekly with flexible hours. Instant joining without any interview needed. Selected candidates "
            "must pay a refundable registration fee of 1500 rupees for training kit and verification before start. "
            "Contact our HR manager strictly on WhatsApp at 9876543210 or join our Telegram channel t.me/fastjobs today. "
            "Please send your Aadhaar card and PAN card copies to confirm your seat immediately. Limited vacancies available!"
        )
        ad = Ad(
            ad_id=ad_id,
            snippet=demo_text[:200],
            full_text=demo_text,
            ai_label="Likely Fake",
            ai_probability=0.94,
            model_used="lr",
            check_count=1
        )
        db.session.add(ad)
        db.session.commit()

    if not ad:
        flash("Job posting not found. Please paste an ad to analyze.", "info")
        return redirect(url_for("pages.analyze"))

    model_to_use = model_override if model_override in ("lr", "rf") else ad.model_used
    res = predict(ad.full_text, model_key=model_to_use)
    res["ad_id"] = ad.ad_id
    res["raw_text"] = ad.full_text
    res["model_key"] = model_to_use
    res["check_count"] = ad.check_count

    other_model_key = "rf" if model_to_use == "lr" else "lr"
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
