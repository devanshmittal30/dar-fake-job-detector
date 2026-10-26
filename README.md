# DAR — Fake Job Posting Detector

> **Check before you apply.**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.1-black.svg)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn_1.9.1-orange.svg)](https://scikit-learn.org/)
[![License: CC-BY-4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

---

## 1. What DAR Is

**DAR** (*"fear"* in Hindi — fake job postings should fear it) is an AI-powered fake job posting detection web application designed to protect job seekers and students from employment scams. Job advertisements can be submitted in three ways:
1. **Direct Text:** Pasting raw job descriptions.
2. **Screenshots & Posters (OCR):** Uploading images or taking live camera photos of flyers, Instagram/WhatsApp posters, and message forwards.
3. **Job Links:** Fetching live job postings securely from external URLs.

DAR analyzes the text using Machine Learning (TF-IDF with Logistic Regression or Random Forest), evaluates rule-based warning signs (e.g. registration fees, vague company names, salary anomalies, personal messaging apps), highlights suspicious phrases directly in the job text, and combines AI predictions with community crowd-sourced verification.

Created as a first-year college project by **Devansh Mittal**.

- **Live Application:** [https://dar-fake-job-detector.onrender.com](https://dar-fake-job-detector.onrender.com)
- **Source Code Repository:** [https://github.com/devanshmittal30/dar-fake-job-detector](https://github.com/devanshmittal30/dar-fake-job-detector)

---

## 2. Key Features

- **Multi-Modal Input:**
  - **Paste Text:** Clean text input with sample templates (Registration fee scam, Data entry scam, Legitimate Software Engineer role).
  - **Image / OCR:** Upload JPG/PNG screenshots or capture via mobile/web camera using local Tesseract OCR engine with an in-browser editable text preview before submission.
  - **Link Fetch:** Safe URL fetching with SSRF protection, strict private IP blocking, 8-second timeouts, and 1 MB content limits.
- **Explainable Machine Learning:**
  - Clear verdicts: **Likely Fake**, **Likely Real**, or **Uncertain** with an explanation band.
  - Model confidence percentage and tuned decision threshold indicator.
  - Top fake-associated and real-associated vocabulary weights.
  - Interactive highlighted text view color-coded by model feature weights with full HTML escaping.
  - Rule-based red-flag warnings (money requests, personal email domains, Telegram/WhatsApp contacts, etc.).
- **Community Crowd-Sourced Verification:**
  - Hash-based and similarity-based job ad matching across duplicate posts and screenshots.
  - Thumbs up (Genuine) and Thumbs down (Fake) voting with authenticated one-vote-per-user enforcement.
  - User reviews and 1–5 star ratings (with owner moderation approval before public display on the Home page).
- **Public Awareness & Transparency:**
  - **Awareness Page:** Official government and cybercrime statistics on employment fraud, tips carousel, and action steps if scammed.
  - **Model Performance Page:** Live metrics, confusion matrix, precision/recall/F1 breakdowns, top-words charts, and external test dataset results.
  - **FAQ Page:** Common questions about scam mechanisms, model limits, and safe job-seeking practices.

---

## 3. Technology Stack

- **Backend:** Python 3.11, [Flask](https://flask.palletsprojects.com/) 3.1.3, [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) 3.1.1, [Flask-Login](https://flask-login.readthedocs.io/) 0.6.3, [Flask-WTF](https://flask-wtf.readthedocs.io/) 1.3.0, [Flask-Limiter](https://flask-limiter.readthedocs.io/) 4.1.1, [Gunicorn](https://gunicorn.org/) 26.2.0.
- **Machine Learning & NLP:** [scikit-learn](https://scikit-learn.org/) 1.9.1 (Logistic Regression & Random Forest classifiers), [pandas](https://pandas.pydata.org/) 3.1.0, [numpy](https://numpy.org/) 2.4.6, [joblib](https://joblib.readthedocs.io/) 1.6.0.
- **OCR Engine:** [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (English language pack) + [pytesseract](https://pypi.org/project/pytesseract/) 0.3.13, [Pillow](https://python-pillow.org/) 13.0.0.
- **Frontend:** Semantic HTML5, Vanilla CSS3 (Custom Design System with responsive mobile-first tokens), Vanilla JavaScript (ES6+), [Chart.js](https://www.chartjs.org/) 4.4.7 (locally pinned).
- **Database:** SQLite (local development in `instance/dar.db`) / PostgreSQL on [Neon](https://neon.tech) (production).
- **Deployment:** [Docker](https://www.docker.com/) container on [Render](https://render.com) (Free Tier web service).

---

## 4. Local Setup & Running

### Prerequisites
- Python 3.11 installed.
- Git installed.
- Tesseract OCR installed:
  - **macOS:** `brew install tesseract`
  - **Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng`
  - **Windows:** Download and install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Add `C:\Program Files\Tesseract-OCR` to system PATH or set `TESSERACT_CMD` in `.env`.

---

### Mac / Linux Commands

```bash
# 1. Clone the repository
git clone https://github.com/devanshmittal30/dar-fake-job-detector.git
cd dar-fake-job-detector

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Upgrade pip and install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create local environment file
cat <<EOF > .env
SECRET_KEY=local-dev-secret-key-32-chars-minimum
FLASK_ENV=development
EOF

# 5. Run the application
python3 run.py
```
Open `http://127.0.0.1:5001` in your browser.

---

### Windows Commands (Command Prompt / PowerShell)

```cmd
:: 1. Clone the repository
git clone https://github.com/devanshmittal30/dar-fake-job-detector.git
cd dar-fake-job-detector

:: 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

:: 3. Upgrade pip and install pinned dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. Create .env file with your settings
echo SECRET_KEY=local-dev-secret-key-32-chars-minimum > .env
echo FLASK_ENV=development >> .env
:: If Tesseract is not in PATH, uncomment and set:
:: echo TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe >> .env

:: 5. Run the application
python run.py
```
Open `http://127.0.0.1:5001` in your browser.

---

## 5. How to Train the Models

Pre-trained pipeline models are committed in `models/` (`lr_pipeline.joblib` and `rf_pipeline.joblib`), so retraining is not required to run the web application.

To retrain the models from the dataset:

1. **Download the raw dataset:**
   - Download `fake_job_postings.csv` from [Kaggle EMSCAD](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction).
   - Place the file at `data/raw/fake_job_postings.csv`.
2. **Build and clean dataset splits:**
   ```bash
   python ml/build_dataset.py
   ```
   Cleans missing values, deduplicates ads, balances classes, and produces train/validation/test splits in `data/processed/`.
3. **Train Logistic Regression & Random Forest:**
   ```bash
   python ml/train.py
   ```
   Trains TF-IDF pipelines with optimal hyperparameter search and outputs `.joblib` pipelines to `models/`.
4. **Evaluate and generate metrics:**
   ```bash
   python ml/evaluate.py
   ```
   Generates `models/metrics.json`, `models/model_config.json`, confusion matrices, and ROC curve plots.

---

## 6. How to Run Tests

DAR includes a full automated test suite with 97 unit, security, ML, accessibility, and integration tests:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test module
pytest tests/test_security_qa.py
```

---

## 7. Environment Variables

| Variable | Required | Default (Dev) | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes (in prod) | Development fallback key | Secret key for Flask session signing and CSRF tokens. |
| `FLASK_ENV` | No | `development` | Setting to `production` enables `Secure` cookie flags (`SameSite=Lax`, `HttpOnly`). |
| `DATABASE_URL` | No | `sqlite:///instance/dar.db` | Database connection URL. In production, use Neon PostgreSQL connection string. |
| `PORT` | No | `5000` | Port for Gunicorn server (automatically supplied by Render). |
| `TESSERACT_CMD` | No | System default (`tesseract`) | Explicit absolute path to Tesseract binary if not in system PATH. |

---

## 8. Deployment Guide

DAR is designed for deployment on free cloud tiers using **Neon** (PostgreSQL) and **Render** (Docker).

### Step 1: Set up Neon PostgreSQL
1. Sign up for a free account at [neon.tech](https://neon.tech).
2. Create a project named `dar` (choose a region close to your target users).
3. Copy the PostgreSQL connection string (starts with `postgresql://...`).

### Step 2: Deploy to Render
1. Sign up for a free account at [render.com](https://render.com).
2. Click **New +** > **Web Service**.
3. Connect your GitHub account and select the `dar-fake-job-detector` repository.
4. Configure service settings:
   - **Name:** `dar-fake-job-detector`
   - **Runtime:** `Docker`
   - **Instance Type:** `Free`
5. Under **Environment Variables**, add:
   - `SECRET_KEY`: Generate a random key using `python -c "import secrets; print(secrets.token_hex(32))"`
   - `DATABASE_URL`: Paste your Neon connection string.
   - `FLASK_ENV`: `production`
6. Under **Advanced Settings**:
   - **Health Check Path:** `/health`
   - **Auto-Deploy:** `Yes`
7. Click **Create Web Service**.
8. After build and deployment succeed, your site will be live at `https://<service-name>.onrender.com`.

### Free-Tier Hosting Notes
- Render free-tier services sleep after 15 minutes of inactivity. The first request after sleep takes ~50–60 seconds to spin up the container.
- Before demonstrations or evaluations, open the live link 5 minutes ahead of time to wake the service.
- SQLite is stored in memory/ephemeral container storage; persistent community votes and user accounts are preserved on Neon PostgreSQL.

---

## 9. Docker (Local Build & Run)

A production-ready `Dockerfile` is provided:
- Base: `python:3.11-slim`
- Installs `tesseract-ocr` and English trained data with clean apt caches.
- Runs as a dedicated non-root user (`daruser`).
- Serves via Gunicorn with 1 worker, 2 threads, and a 120-second timeout.

### Building & Running with Docker
If Docker Desktop is installed on your local machine:

```bash
# Build Docker image
docker build -t dar-app .

# Run container locally on port 5000
docker run -p 5000:5000 -e PORT=5000 -e SECRET_KEY="local-docker-secret" dar-app
```
Open `http://localhost:5000`.

*(Note: If Docker is not installed on your system, follow the local Python virtual environment instructions in Section 4).*

---

## 10. Dataset Sources & Licences

| Dataset ID | Dataset Name & Origin | Rows | Fake Ads | Licence | Details |
|---|---|---|---|---|---|
| **D1 (Primary)** | Kaggle "Real / Fake Job Posting Prediction" (EMSCAD, University of the Aegean) | 17,880 | 866 (~4.8%) | Open Database License / CC-BY (Academic Use) | Primary corpus for training and validation splits. See [DATA_SOURCES.md](DATA_SOURCES.md). |
| **E1 (External Test)** | Independent real-world sample collected from company career portals and scam alerts | 60 | 30 | Owner Collection | Unseen evaluation benchmark measuring cross-domain performance. |

---

## 11. System Limitations

As an honest machine learning project, DAR's boundaries and limitations are transparently documented:

1. **Extreme Class Imbalance:** Public datasets contain few fake examples (866 in EMSCAD), making fraud detection harder than simple accuracy implies.
2. **Domain Shift:** Models trained on traditional job board postings experience lower confidence on WhatsApp flyers or social media posters.
3. **OCR Dependency:** Scanned image quality, noise, and handwriting can introduce textual errors that alter model predictions (an in-app text editor is provided).
4. **Language Restriction:** Currently English-only.
5. **Dataset Noise:** Labels in public benchmark datasets may occasionally contain mislabeled samples.
6. **Probabilistic Output:** Predictions represent statistical probabilities, not legal proof of fraud.
7. **Similarity Matching Thresholds:** Duplicate ad matching relies on a cosine similarity threshold, which can occasionally miss heavily rewritten ads.
8. **Free Cloud Sleep Cycles:** Free cloud hosting sleeps when idle and requires ~1 minute to wake.
9. **Community Vote Subjectivity:** Crowd-sourced votes reflect user opinions and are displayed separately from the algorithmic AI verdict.

---

## 12. Author & Acknowledgements

- **Author:** Devansh Mittal (First-year college project)
- **Project Repository:** [https://github.com/devanshmittal30/dar-fake-job-detector](https://github.com/devanshmittal30/dar-fake-job-detector)
- **Documentation:** See `docs/01_PRD.md`, `docs/02_UI_UX_SPEC.md`, `docs/03_TECHNICAL_DESIGN.md`, and `docs/04_DEVELOPMENT_ROADMAP.md`.
