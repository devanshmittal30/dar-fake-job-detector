"""app/routes_pages.py
Page routing blueprint for DAR Fake Job Detector.

Serves all 10 user-facing HTML views following:
- docs/03_TECHNICAL_DESIGN.md (section 7)
- docs/02_UI_UX_SPEC.md (section 3)
"""

from flask import Blueprint, render_template

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
    """Result page displaying verdict, probability gauge, explainability, and voting."""
    return render_template("result.html", ad_id=ad_id)


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
