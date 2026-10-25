# DAR — Fake Job Posting Detector

> **Check before you apply.**

DAR is a web application that helps job seekers detect fake job advertisements using machine learning. It accepts job ads as text, images (via OCR), or links, and provides a verdict (Likely Fake / Likely Real / Uncertain) with explanations and community verification.

**⚠️ Work in progress** — see `docs/04_DEVELOPMENT_ROADMAP.md` for the build plan.

## Creator

Devansh Mittal

## Tech Stack

- **Backend:** Python 3.11, Flask, SQLAlchemy, Tesseract OCR
- **ML:** scikit-learn (Logistic Regression + Random Forest on TF-IDF features)
- **Frontend:** HTML5, CSS3, vanilla JavaScript, Chart.js 4.4.7 (pinned, stored locally)
- **Database:** SQLite (local) / PostgreSQL on Neon (production)
- **Hosting:** Docker on Render (free tier)

## Quick Start

_Setup instructions will be added after the scaffold is complete._

## Links

- **Live site:** [LIVE_URL]
- **Repository:** [GITHUB_REPO_URL]

## Licence

See `DATA_SOURCES.md` for dataset licences.
