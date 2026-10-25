# Document 3: Technical Design Document

**Product:** DAR, Fake Job Detector | **Creator:** Devansh Mittal
Read together with `01_PRD.md` and `02_UI_UX_SPEC.md`. This file fixes the technology. **Antigravity must use only what is listed as allowed.** If something is missing, ask the owner.

---

## 1. Overview and architecture

```
Browser (phone / laptop)
  HTML + CSS + vanilla JavaScript (camera, upload, charts, animations)
        |  HTTPS
        v
Flask web app  (gunicorn, 1 worker, 2 threads, in a Docker container on Render)
  Pages (Jinja2 templates) + JSON API
  predictor.py : loads the two trained model files once at start
  rules.py     : rule-based warning flags
  matcher.py   : finds the same/similar ad already analysed
  ocr.py       : Pillow image preparation + Tesseract OCR
  fetcher.py   : safe download of a job link + text extraction
  auth, votes, ratings (Flask-Login, Flask-SQLAlchemy)
        |
        v
PostgreSQL on Neon (production)    SQLite file (local development)
```

Data flow:
1. **Text:** browser sends text to `POST /api/analyze` -> clean text -> match to existing ad -> model probability -> verdict + reasons + flags -> save -> browser opens `/result/<ad_id>`.
2. **Image (device or camera):** browser sends image to `POST /api/ocr` -> text returned in an editable box -> user presses Analyze -> same as flow 1.
3. **Link:** browser sends URL to `POST /api/fetch` -> text returned in an editable box -> Analyze -> same as flow 1.
4. **Vote / rating:** logged-in browser posts to `/api/ads/<ad_id>/vote` or `/rating` with the CSRF token.

---

## 2. Languages (only these)

| Language | Used for |
|---|---|
| Python 3.11 | Backend, machine learning, tests |
| HTML5 | Page structure (Jinja2 templates) |
| CSS3 | Styling with CSS variables (own stylesheet) |
| JavaScript (ES2020, vanilla, no framework) | Camera, uploads, animations, calling the API |
| SQL (through SQLAlchemy, and for the owner's approval query) | Database |
| Dockerfile / shell | Packaging for hosting |

Not allowed: TypeScript, Node.js backend, PHP, Java, any other language.

---

## 3. Libraries and tools

### 3.1 Required by the course (data and ML)
| Library | Used for |
|---|---|
| numpy | Arrays and numeric work |
| pandas | Loading CSVs, cleaning, merging datasets |
| matplotlib | Plots saved as images |
| seaborn | Statistical plots (class balance, confusion matrices) |
| scikit-learn | TF-IDF, Logistic Regression, Random Forest, cross-validation, metrics, cosine similarity |

### 3.2 Other Python packages (allowed)
| Package | Used for |
|---|---|
| joblib | Saving and loading trained models |
| Flask | Web framework (includes Jinja2 and Werkzeug) |
| Flask-SQLAlchemy | Database models |
| Flask-Login | User sessions |
| Flask-WTF | CSRF protection |
| Flask-Limiter | Rate limiting |
| psycopg2-binary | PostgreSQL driver |
| gunicorn | Production web server |
| python-dotenv | Reading `.env` locally |
| Pillow | Image checking and preparation |
| pytesseract (+ the Tesseract OCR program, English data) | Reading text from images |
| requests | Downloading a job link |
| beautifulsoup4 | Extracting text from a web page |
| pytest | Tests |

scipy is installed automatically with scikit-learn. No other packages without the owner's approval.

### 3.3 Frontend (allowed)
| Item | Used for |
|---|---|
| Chart.js (one pinned 4.x version, file stored in `static/js/vendor/`) | Charts (bar, donut) on Awareness and Home |
| Lucide icons (inline SVG files stored in the project) | Icons |
| Google Fonts: Plus Jakarta Sans, Inter | Fonts |
| Browser APIs: `getUserMedia`, `FileReader`, `fetch`, `IntersectionObserver`, `canvas` | Camera, upload, animations |

### 3.4 Not allowed (examples)
TensorFlow, PyTorch, Keras, transformers/BERT, XGBoost, LightGBM, CatBoost, gensim, NLTK, spaCy, OpenCV, EasyOCR, PaddleOCR, cloud OCR or AI APIs, Django, FastAPI, Streamlit, Gradio, React, Vue, Angular, jQuery, Bootstrap, Tailwind, MongoDB, Firebase, Redis, Selenium, Playwright, Kubernetes.

### 3.5 Development and hosting tools
Git and GitHub; Docker (image for hosting); Neon (free PostgreSQL); Render (free web service, Docker); Antigravity (AI code editor); Kaggle (data download, free account).

### 3.6 Dependency rule
`requirements.txt` lists exact versions that worked (create with `pip freeze` after the first successful run, keep only the packages above and their dependencies). The scikit-learn version used for training must be the same one used by the server, otherwise the saved model may not load.

---

## 4. Environment variables

| Variable | Meaning |
|---|---|
| `SECRET_KEY` | Long random text for sessions (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | Neon connection string in production; if empty, use local SQLite `sqlite:///instance/dar.db`. Convert a leading `postgres://` to `postgresql://` |
| `FLASK_ENV` | `development` or `production` (production turns on Secure cookies) |
| `TESSERACT_CMD` | Optional full path of the Tesseract program (needed on Windows, for example `C:\Program Files\Tesseract-OCR\tesseract.exe`) |

`.env` is never committed; `.env.example` lists the names without values.

---

## 5. Data and machine learning

### 5.1 Task
Binary text classification: input = text of a job ad; output = probability that it is fake. Label 1 = fake (fraudulent), 0 = real. This matches topic 53: NLP classification, TF-IDF, Logistic Regression, Random Forest, metrics Accuracy, Precision, Recall.

### 5.2 Where the data comes from

| ID | Dataset | Use | Notes |
|---|---|---|---|
| **D1 (primary)** | Kaggle "Real / Fake Job Posting Prediction" (processed version of EMSCAD, Employment Scam Aegean Dataset, University of the Aegean). File `fake_job_postings.csv` | Training and testing | 17,880 job ads: 17,014 real, 866 fake (under 5%). Columns: job_id, title, location, department, salary_range, company_profile, description, requirements, benefits, telecommuting, has_company_logo, has_questions, employment_type, required_experience, required_education, industry, function, **fraudulent** (label). Download from Kaggle with a free account; copy the licence text shown on the Kaggle page into `DATA_SOURCES.md` |
| **D2... (optional, owner-verified)** | Another labelled fake/real job-posting dataset | More training data | Add only if it (a) has a real/fake label made by someone else, (b) has job text, (c) has a licence that allows academic use. Record name, URL, rows, fake count, licence and date in `DATA_SOURCES.md`. **Status: no second labelled dataset has been verified.** A Kaggle upload named "Real or Fake Jobs" (by whenamancodes) appeared in a search but could not be opened for checking; it may be a copy of D1, which the duplicate-removal step would remove |
| **E1 (external test, recommended)** | 30 fake and 30 real ads collected by the owner: fake ones from ads named in official scam warnings or news reports; real ones from current career pages of known companies. Saved as `data/external/external_test.csv` with columns `text,label` | Real-world check only. Never used for training or tuning | Shows how the model behaves on social-media-style ads. Do not write fake ads yourself and do not use AI to generate them |

**About "huge data":** the number of FAKE examples in public data is small (866 in D1). Adding many unlabelled or assumed-real ads (for example a LinkedIn job-postings dataset, which has no fake label) adds more real examples but no fake ones, can teach the model "LinkedIn style = real", and adds label noise. It is not recommended and is not part of this project unless the owner decides otherwise and records the risk. Be ready to explain this in viva: more fake examples, not more real ones, improve fake-ad detection.

Rules: raw CSV files are never committed to GitHub (size and licence); `data/README.md` explains how to download them.

### 5.3 Text and preprocessing (one shared module `ml/preprocess.py`, used in training AND in the app)
- The model uses **text only**: title + company_profile + description + requirements + benefits joined with spaces. Structured columns (has_company_logo, telecommuting, salary_range, etc.) are NOT features because an image gives text only. They may be used in exploratory plots only.
- Cleaning steps in order: fill missing with empty text; join fields; lowercase; remove HTML tags; replace URLs with `urltoken`, emails with `emailtoken`, phone numbers with `phonetoken`; keep letters, digits and basic currency/percent symbols; collapse spaces. No stemming or lemmatising.
- Remove empty texts and exact duplicates across all datasets before splitting.

### 5.4 Same-ad matching (`app/matcher.py`, needed so votes are shared across screenshots)
OCR gives slightly different text each time, so an exact hash alone would almost never match two screenshots of the same ad.
1. Clean and normalise the new text. Compute `ad_id` = SHA-256 of the normalised text. If a stored ad has this id, it is the same ad.
2. Otherwise compute the TF-IDF vector of the new text with the vectorizer from the Logistic Regression pipeline (`pipeline.named_steps["tfidf"]`) and compare it by cosine similarity (`sklearn.metrics.pairwise.cosine_similarity`) with the vectors of stored ads (keep an in-memory cache of the newest 5000 ads; the app runs one worker so the cache stays consistent).
3. If the best similarity is **0.85 or higher**, use that stored ad (increase its `check_count`); otherwise create a new ad.
4. The threshold 0.85 is a starting value. Tune it with a small test: take 5 different job ads, make 2 screenshots of each, run OCR; choose the threshold where same-ad pairs match and different ads do not. Record the result in `NOTES.md`.

### 5.5 Train / test split and tuning
- One stratified split: 80% train, 20% test, `random_state=42`. The test set is used only once, at the end.
- Hyperparameters and the decision threshold are chosen only with 5-fold stratified cross-validation on the training part (`GridSearchCV`, `cross_val_predict`).
- The TF-IDF vectorizer is fitted on training data only, inside a scikit-learn `Pipeline` (step names `tfidf` and `clf`) so cross-validation does not leak.

### 5.6 Models (exactly two)

| Setting | Logistic Regression | Random Forest |
|---|---|---|
| Vectorizer | `TfidfVectorizer(ngram_range=(1,2), max_features=20000, min_df=3, sublinear_tf=True, stop_words="english")` | same |
| Imbalance | `class_weight="balanced"` | `class_weight="balanced_subsample"` |
| Parameters to tune | C in {0.1, 1, 10}, `solver="liblinear"` | n_estimators in {100, 200}, max_depth in {20, 40}, min_samples_leaf in {1, 2}, `n_jobs=-1`, `random_state=42` |
| Tuning score | `scoring="f1"` (fake class) | same |
| Why used | Fast, accurate on text, readable word weights | Non-linear, robust, good comparison |

Saved with `joblib.dump(..., compress=3)`. Each model file must stay under 50 MB (GitHub warns at 50 MB and blocks files over 100 MB; free hosting has limited memory). If larger, reduce `n_estimators`, `max_depth` or `max_features`.

### 5.7 Evaluation (once, on the 20% test set; also on E1 if available)
Report for both models: accuracy, precision, recall, F1 (fake class), ROC-AUC, PR-AUC, confusion matrix. Save to `models/metrics.json`.
- Why not accuracy alone: with under 5% fake ads, a model that always says "real" gets about 95% accuracy and catches no fake ad. Precision = of ads called fake, how many really are. Recall = of all fake ads, how many were caught.
- Decision threshold `T` per model: chosen on cross-validated predictions on the training part to maximise F1 of the fake class; saved in `model_config.json`.
- Verdict rule: Likely Fake if `p >= T + 0.10`; Likely Real if `p <= T - 0.10`; otherwise Uncertain.
- The default model shown on the site is the one with the higher test F1 (`default_model` in `model_config.json`).
- Error analysis: save 10 false positives and 10 false negatives with likely reasons (viva notes).
- Never change a model or threshold after seeing test results. Never show a number that did not come from these files.

### 5.8 Explainability
- **Model words:** always from the Logistic Regression model, even when Random Forest is selected (label: "Top words, from Logistic Regression"). Contribution of a word = coefficient x TF-IDF value of that word in this ad. Show the top 8 words towards Fake and the top 5 towards Real.
- **Warning flags** (`app/rules.py`, regular expressions; flags never change the verdict): asks for money, fee or deposit; asks for bank, Aadhaar, PAN or OTP; contact only through WhatsApp or Telegram; free email domain as contact; "no interview" or "instant joining"; unrealistic pay words; urgency words; no company name or details.
- Highlight matches in the ad text: escape the text first, then wrap matches in `<mark>`.

### 5.9 Artifacts created by training
`models/lr_pipeline.joblib`, `models/rf_pipeline.joblib`, `models/model_config.json` (thresholds, uncertain band 0.10, default model, sklearn version, training date, dataset names and row counts, best parameters, training row count), `models/metrics.json`, and plots in `app/static/img/plots/`: class balance, confusion matrices, metric comparison, ROC and PR curves, top fake and real words. Fixed `random_state=42`.

---

## 6. Project structure

```
dar-fake-job-detector/
  README.md  .gitignore  .env.example  requirements.txt  Dockerfile  .dockerignore  wsgi.py
  DATA_SOURCES.md  NOTES.md
  docs/                01_PRD.md 02_UI_UX_SPEC.md 03_TECHNICAL_DESIGN.md 04_DEVELOPMENT_ROADMAP.md
  dar-brand/           4 logo SVG files (originals)
  data/
    README.md  raw/ (NOT in git)  processed/ (NOT in git)  external/external_test.csv
  ml/                  preprocess.py eda.py build_dataset.py train.py evaluate.py
  models/              *.joblib  model_config.json  metrics.json
  app/
    __init__.py (create_app)  config.py  models.py
    routes_pages.py  routes_api.py  routes_auth.py
    predictor.py  rules.py  matcher.py  ocr.py  fetcher.py
    templates/         base.html + one file per page + partials
    static/css/main.css   static/js/ (main.js, analyze.js, result.js, home.js, vendor/chart.js)
    static/img/ (logos, plots)   static/data/india_stats.json
  tests/               test_preprocess.py test_rules.py test_predictor.py test_matcher.py test_api.py test_auth.py test_fetcher.py test_ocr.py
```

---

## 7. API specification

All JSON; errors return `{"error": "message"}` with a proper HTTP status. Browser calls send the CSRF token.

| Method and path | Login | Request | Response |
|---|---|---|---|
| `POST /api/analyze` | no | `{"text","model":"lr"\|"rf","source":"text"\|"image"\|"link"}` | `{"ad_id","verdict","probability","threshold","model","top_fake_words":[{"word","weight"}],"top_real_words":[...],"flags":[{"code","message"}],"highlighted_html"}` |
| `POST /api/ocr` | no | multipart `image` (JPG/PNG, max 5 MB) | `{"text"}` or `{"error":"no_text_found"}` |
| `POST /api/fetch` | no | `{"url"}` | `{"text"}` or error |
| `GET /api/ads/<ad_id>` | no | | `{"ad_id","snippet","ai_label","ai_probability","fake_votes","genuine_votes","my_vote"}` |
| `POST /api/ads/<ad_id>/vote` | yes | `{"vote":"fake"\|"genuine"}` (thumbs down = fake, thumbs up = genuine) | updated counts |
| `POST /api/ads/<ad_id>/rating` | yes | `{"stars":1-5,"comment":"optional, max 200"}` | `{"ok":true}` |
| `GET /api/community` | no | query `filter` (all, fake, genuine, disputed), `q`, `sort`, `page` | `{"items":[...],"page","pages"}` |
| `GET /api/home` | no | | `{"analyses_total","training_rows","accuracy","recall","precision","avg_rating","rating_count","distribution","reviews":[{"stars","comment","first_name","date"}]}` (reviews: only approved, 4 or 5 stars, newest 6) |
| `GET /api/metrics` | no | | `metrics.json` + `model_config.json` content without server paths |
| `GET /api/stats` | no | | `india_stats.json` |
| `POST /auth/register`, `/auth/login`, `/auth/logout`, `GET /auth/me` | | name, email, password | session cookie |
| `GET /health` | no | | `{"status":"ok"}` |

Page routes: `/`, `/analyze`, `/result/<ad_id>`, `/community`, `/awareness`, `/performance`, `/faq`, `/about`, `/auth`, error handlers 404 and 500.

---

## 8. Database (Flask-SQLAlchemy models; `db.create_all()` at start, no migration tool)

- **users:** id (PK), name, email (unique, stored lowercase), password_hash, created_at.
- **ads:** ad_id (PK, 64-character hash), snippet (first 200 characters), full_text, ai_label, ai_probability, model_used, first_checked_at, check_count.
- **votes:** id (PK), user_id (FK), ad_id (FK), vote ("fake" or "genuine"), created_at, updated_at, UNIQUE(user_id, ad_id).
- **ratings:** id (PK), user_id (FK), ad_id (FK), stars (1 to 5), comment (max 200, optional), approved (boolean, default false), created_at, UNIQUE(user_id, ad_id).

`analyses_total` = sum of `ads.check_count`. Home average rating = average of `stars` over ALL ratings.
**Owner approval of comments (no admin page):** in the Neon SQL editor run `UPDATE ratings SET approved = true WHERE id = <id>;`. To clear development test data before launch: delete rows from `ratings`, `votes`, `ads` (in that order), and keep `users` if needed.
Production data lives only in Neon (the free host has no persistent disk).

---

## 9. Security and privacy

- **Passwords:** `werkzeug.security.generate_password_hash`; never stored or logged in plain text; minimum 8 characters.
- **Sessions:** Flask-Login with `SECRET_KEY` from the environment; cookies `HttpOnly`, `SameSite=Lax`, `Secure` in production.
- **CSRF:** Flask-WTF on all POST forms and API calls from the site.
- **Rate limits (Flask-Limiter):** login and register 10 per minute per IP; analyze, ocr, fetch 30 per minute per IP; vote and rating 30 per minute per user.
- **Output escaping:** Jinja2 auto-escape on; highlighted text built by escaping first, then wrapping matches.
- **Safe link fetching (`fetcher.py`):** only `http` and `https`; resolve the host and reject private, loopback, link-local and metadata addresses (for example 127.0.0.1, 10.x, 192.168.x, 169.254.169.254); timeout 8 seconds; read at most 1 MB; at most 3 redirects, re-checking each; no cookies; plain User-Agent.
- **Uploads (`ocr.py`):** JPG/PNG only, maximum 5 MB, verify with Pillow, downscale very large images, process in memory, never save to disk, discard metadata.
- **Redirect after login:** relative paths only.
- **Secrets:** only in environment variables; `.env` git-ignored.
- **Errors:** friendly pages; no stack traces to users.
- **Privacy:** stored data = name, email, password hash, analysed ad text, votes, ratings. No tracking or advertising scripts. The Analyze page warns users not to submit personal details. The owner's phone and email are shown publicly only in the footer.

---

## 10. Testing plan (pytest + manual)

1. **ML:** no overlap between train and test texts (assert); `metrics.json` exists; the model files load under the pinned scikit-learn version; file sizes under 50 MB.
2. **Unit tests:** preprocessing (at least 6), each warning flag, verdict thresholds, `ad_id` hashing, matcher (exact copy matches, noisy copy matches, different ad does not), highlighted output is escaped.
3. **API tests:** each endpoint with valid and invalid input; vote uniqueness and change of vote; login required for vote and rating; ratings not shown on `/api/home` until approved; the average counts all ratings; unsafe URLs rejected (localhost, 127.0.0.1, 169.254.169.254, file://, 10.x.x.x); rate limit.
4. **Manual:** 5 fake-looking and 5 real-looking ads through text, image and link; one real phone screenshot; one live camera capture.
5. **Device test on the LIVE link:** one phone (mobile data) and one laptop.
6. **Accessibility quick check:** keyboard-only use of the Analyze page and result voting; reduced-motion setting on.
7. **Demo rehearsal** twice, including the sleeping-server wake-up.

---

## 11. Deployment specification

- **Repository:** GitHub `dar-fake-job-detector`; `main` branch holds the final version; commit after each working step. Git-ignored: `.env`, `.venv/`, `data/raw/`, `data/processed/`, `instance/`, `*.db`, `__pycache__/`.
- **Docker image:** `python:3.11-slim`; install `tesseract-ocr` and `tesseract-ocr-eng` with apt (no recommends, clean the cache); copy `requirements.txt` first and `pip install --no-cache-dir`; copy the project; run as a non-root user; start `gunicorn wsgi:app` bound to `0.0.0.0:$PORT` with 1 worker, 2 threads, timeout 120.
- **Neon:** create a free project, copy the connection string, put it in Render as `DATABASE_URL`. (Neon's free plan: permanent, no card, 1 GB per project; compute suspends after 5 idle minutes and wakes on the next request.)
- **Render:** new Web Service from the GitHub repo, runtime Docker, instance type Free, environment variables `SECRET_KEY`, `DATABASE_URL`, `FLASK_ENV=production`, health check path `/health`.
- **Free-plan facts (checked 24 Oct 2026 on provider pages; re-check):** Render free web services sleep after 15 minutes without traffic and need about a minute to wake; 750 free instance hours per month; no persistent disk; build minutes and bandwidth limited. Render's free-instance RAM was not stated on the page checked; confirm on Render's pricing page. Hugging Face Docker Spaces need a paid plan and are not used.
- **Fallback if memory is too small:** (1) shrink the models (section 5.6); (2) deploy the live site with Logistic Regression only and keep Random Forest in the local demo; explain this in viva.
- **Before any demo:** open the live site 5 minutes earlier.

---

## 12. Performance and size budgets

Text analysis under 3 seconds; OCR under 15 seconds; each model file under 50 MB; one gunicorn worker; matcher cache of at most 5000 ads; image processing limited to 4000 px width.

---

## 13. Code quality rules for Antigravity

Small functions with clear names; comments in simple language (the owner must explain the code); no dead code; no hard-coded numbers shown on the UI; one shared `preprocess.py` for training and serving; type hints optional; tests for every module listed in section 10.

---

## 14. Limitations (say these in viva and on the About page, in plain words)

1. Public data has few fake examples (866 in the main dataset), so catching fake ads is harder than the accuracy number suggests.
2. The model learned from job-portal text; social-media posters look different (domain shift), so performance there can be lower. The external test measures this.
3. OCR mistakes change the text; users can correct it.
4. English only.
5. Dataset labels can contain errors.
6. The model gives a probability, not proof.
7. Same-ad matching uses a similarity threshold and can occasionally match or miss.
8. Free hosting sleeps when idle.
9. Community votes can be wrong or biased; they are shown separately from the AI verdict.

---

## 15. Plain-language glossary (viva)

- **NLP classification:** teaching a computer to put text into groups (fake or real).
- **TF-IDF:** a score for each word: high if the word is frequent in this ad but rare in other ads, so informative words count more than common ones like "the".
- **Logistic Regression:** a weighted sum of word scores turned into a probability; the weights show which words push towards fake.
- **Random Forest:** many decision trees that vote.
- **Class imbalance:** far more real than fake ads; handled with class weights and a tuned threshold.
- **Precision / Recall / F1:** of ads called fake, how many were fake / of all fake ads, how many were caught / the balance of both.
- **Confusion matrix:** table of right and wrong calls.
- **Train/test split:** learn on one part, grade on a part never seen.
- **Cross-validation:** repeating train/validate on the training part to choose settings fairly.
- **OCR:** software that reads text from an image.
- **Cosine similarity:** a score from 0 to 1 for how alike two texts are, used to recognise the same ad.
- **Domain shift:** the real-world data differs from the training data.
