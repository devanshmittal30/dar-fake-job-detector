# Document 4: Development Roadmap and Antigravity Build Guide

**Product:** DAR, Fake Job Detector | **Owner:** Devansh Mittal | **Timeline:** 7 days
Goal: from an empty folder to a live website (works on phone and laptop) with all code on GitHub, built step by step with Antigravity.

---

## 1. Seven-day plan

| Day | Work | You have at the end |
|---|---|---|
| 1 | Install tools, accounts, download data, create repo, scaffold (P0-P2), EDA (P3) | Repo on GitHub, plots, data understood |
| 2 | Dataset build and split (P4), train (P5), evaluate (P6) | Two models, `metrics.json`, plots, numbers in `NOTES.md` |
| 3 | Predictor, rules (P7), Flask base and design system (P8), Analyze page with text and link (P9) | Text and link analysis working locally |
| 4 | Image input: OCR, import, camera (P10), Result page (P11) | Core demo working locally |
| 5 | Database, accounts, same-ad matching (P12), votes, ratings, Community (P13), Home (P14) | Full site locally |
| 6 | Awareness, Performance, FAQ, About (P15), security and QA (P16), Docker and README (P17), deploy | Live link |
| 7 | Phone and laptop tests, PPT, viva practice, demo rehearsal, screen recording | Submission ready |

If you fall behind, cut in this order: Priority 2 animations, Awareness stories section, Community filters beyond All/Fake/Genuine, Random Forest on the live site (keep Logistic Regression), ratings comments carousel.

---

## 2. Before you start (checklist)

### 2.1 Install
| Tool | Check |
|---|---|
| Python 3.11 | `python --version` (or `python3 --version`) |
| Git | `git --version`; then `git config --global user.name "Devansh Mittal"` and `git config --global user.email "<your email>"` |
| Antigravity | open it and sign in with your Google account (reports say it is free in public preview; check current status) |
| Tesseract OCR | `tesseract --version`. Windows: installer from the UB Mannheim Tesseract page, tick English data, note the path (usually `C:\Program Files\Tesseract-OCR\tesseract.exe`). Mac: `brew install tesseract`. Linux: `sudo apt install tesseract-ocr tesseract-ocr-eng` |
| Docker Desktop (optional) | `docker --version`; only to test the container locally |

### 2.2 Free accounts
GitHub, Kaggle, Neon, Render.

### 2.3 Get the data
1. Kaggle: search "Real / Fake Job Posting Prediction", download `fake_job_postings.csv`, copy the licence text.
2. Optional extra datasets: only if verified (label, text, licence). Write each in `DATA_SOURCES.md`. See `03_TECHNICAL_DESIGN.md` section 5.2 for why more real ads do not help.
3. Recommended: collect 30 fake and 30 real ads yourself for `data/external/external_test.csv` (columns `text,label`, 1 = fake). Fake: ads named in official scam warnings or news. Real: career pages of known companies. Do not write or generate fake ads yourself.

### 2.4 Make the project folder
```
dar-fake-job-detector/
  docs/                 (put the 4 documents here)
  dar-brand/            (the 4 SVG logo files)
  data/raw/             (put the Kaggle CSV here)
```
Open this folder in Antigravity (File > Open Folder).

### 2.5 Create an EMPTY GitHub repository
Name `dar-fake-job-detector`. Public if your teacher must see it, otherwise Private. Do NOT add a README or .gitignore there.

---

## 3. How to start in Antigravity (steps)

1. Open the project folder in Antigravity. Check that the `docs/` and `dar-brand/` folders are visible.
2. Open the agent chat (Agent Manager). Reports describe a manager view where the agent shows a plan and can test a web app in a built-in browser; your version may look different.
3. If your version has a Rules or Instructions setting, paste **P0** there. In any case, paste **P0** as the first message of every NEW conversation.
4. Then send **P1** (read and plan, no code). Read the plan. Answer its questions. Only then send P2.
5. Send ONE prompt at a time, in order. After each one: read its summary, run the thing, do the "You check" list, then commit and push (section 7).
6. Start a NEW conversation at each Stage heading (Stage 1, Stage 2, ...) and paste P0 again, so the agent does not forget the rules.
7. Keep `NOTES.md` yourself: final metrics, dataset list, problems you met, similarity-threshold result. It becomes your viva notes.

### Important tips
1. **Docs are the boss.** Never let the agent edit the four documents. If it wants a change, you decide.
2. **Plan before code.** Always ask for the plan first on big prompts. If it skips it, add "Show me your plan first and wait for my OK."
3. **One prompt at a time.** Do not paste several prompts together.
4. **Commit often.** After every working prompt: `git add .`, `git commit`, `git push`. If the agent breaks something you can go back.
5. **Check the stack.** If you see a library that is not in `03_TECHNICAL_DESIGN.md` section 3, use fix prompt G1.
6. **Never trust numbers you did not see produced.** Accuracy, counts and statistics must come from `metrics.json`, the database or `india_stats.json`. If you see a number typed into a template, ask the agent to remove it.
7. **Protect the test set.** The test set is used once, in P6. If the agent starts tuning on it, stop it (G1).
8. **No secrets in prompts.** Passwords, `SECRET_KEY` and the Neon string go only in `.env` and in Render's settings.
9. **Read the code you will explain.** Use G5 ("explain this file") for `preprocess.py`, `train.py`, `evaluate.py`, `predictor.py`, `rules.py`, `matcher.py`.
10. **When stuck:** copy the exact error text, start a new conversation, paste P0, then G3.
11. **Terminal permissions:** the agent may ask to run commands. Read them; allow installs and tests; refuse anything that deletes files outside the project.
12. **Look at the screen yourself.** Open the site on your phone browser early (same Wi-Fi at first) rather than waiting for the end.
13. **Windows users:** virtual environment commands are `python -m venv .venv` then `.venv\Scripts\activate`. Mac/Linux: `source .venv/bin/activate`.
14. **Backup:** keep a screen recording of the finished demo in case the internet fails.

---

## 4. The prompts

### P0. Master instruction (paste at the start of every new conversation)
```
You are helping me build a college project called DAR: a fake job posting detector website.
Source of truth: docs/01_PRD.md, docs/02_UI_UX_SPEC.md, docs/03_TECHNICAL_DESIGN.md, docs/04_DEVELOPMENT_ROADMAP.md. Read the relevant ones before every task. If something is not written there, ASK me; do not guess or invent.

Hard rules:
1. Use ONLY the technologies in section 3 of 03_TECHNICAL_DESIGN.md. No other libraries, frameworks or services. No deep learning. The only models are Logistic Regression and Random Forest (scikit-learn) on TF-IDF features.
2. Never invent data, statistics, ratings, reviews, counts, metrics or sources. Every number on the website comes from the database, models/metrics.json, models/model_config.json or app/static/data/india_stats.json.
3. Follow docs/02_UI_UX_SPEC.md exactly: colours, fonts, copy, order of sections, logo placement. Mobile first.
4. Write simple, well-commented code; I must explain it in viva. Small functions, clear names.
5. Never put secrets in code. Use environment variables and .env (git-ignored).
6. Work in small steps. Before editing, show a short plan. After finishing, tell me: (a) files created or changed, (b) how to run it, (c) how I can test it, (d) anything you were unsure about.
7. Write or update tests for what you build, and run them.
8. Do not edit the four documents. Do not delete or rewrite files outside the current task.
```

### Stage 1: Plan and scaffold (Day 1)

#### P1. Read and plan (no code)
```
Read all four documents in docs/ completely. Do not write code yet.
Reply with: (1) a summary of the project in 10 lines in your own words, (2) the exact folder structure you will create (must match 03_TECHNICAL_DESIGN.md section 6), (3) the contents of requirements.txt (allowed packages only, no versions yet), (4) the build order you will follow, (5) any questions, gaps or contradictions you found in the documents.
Wait for my approval.
```
You check: folder list matches; no forbidden packages. Answer its questions.

#### P2. Scaffold
```
Create the project scaffold exactly as in 03_TECHNICAL_DESIGN.md section 6:
- all folders and placeholder files with a one-line comment,
- requirements.txt with allowed packages only (no pinned versions yet),
- .gitignore excluding: .env, .venv/, venv/, __pycache__/, *.pyc, data/raw/, data/processed/, instance/, *.db, *.sqlite, .DS_Store, .pytest_cache/,
- .env.example with SECRET_KEY, DATABASE_URL, FLASK_ENV, TESSERACT_CMD (no real values),
- data/README.md explaining which datasets to download and where to put them,
- DATA_SOURCES.md with the table in 03_TECHNICAL_DESIGN.md section 5.2 (rows D1 and E1 filled from the document, other fields left for me),
- README.md with a short description and "work in progress",
- copy the four SVG files from dar-brand/ into app/static/img/.
Then give me the commands to create a Python 3.11 virtual environment and install requirements for Windows and for Mac/Linux, run the install, and run `python -c "import sklearn, pandas, numpy, matplotlib, seaborn; print('ok')"`.
```
You check: `.gitignore` exists; imports work. **Then do the first push (section 7).**

#### P3. Exploratory data analysis
```
Write ml/eda.py. Load the dataset CSV(s) from data/raw/ and, for the main dataset, print and save with matplotlib/seaborn into app/static/img/plots/:
1. shape, column names, missing values per column,
2. class balance (count and percentage of fraudulent 0/1) as a seaborn count plot,
3. text length (words) distribution for fake vs real,
4. top 20 most common words for fake and for real ads (CountVectorizer with English stop words),
5. percentage of fake ads by employment_type, required_experience and has_company_logo (for understanding only; these columns are NOT model features).
Clear titles and axis labels; comments in simple language. Do not train any model here.
```
You check: plots exist; note the fake percentage (about 5%).

### Stage 2: Data and model (Day 2)

#### P4. Clean dataset and split
```
Implement ml/preprocess.py and ml/build_dataset.py following 03_TECHNICAL_DESIGN.md sections 5.3 and 5.5.
- preprocess.py: clean_text(text) with exactly the steps in 5.3 (lowercase, remove HTML, replace URLs/emails/phone numbers with urltoken/emailtoken/phonetoken, keep letters, digits and basic currency/percent symbols, collapse spaces) and build_text(row) that joins title, company_profile, description, requirements, benefits. The web app will import this same module.
- build_dataset.py: load the CSVs listed in DATA_SOURCES.md, map each to [text, label], clean, drop empty texts, drop exact duplicates across all datasets (print how many were removed), then ONE stratified 80/20 split with random_state=42. Save data/processed/train.csv and data/processed/test.csv and print the class counts of each.
- tests/test_preprocess.py with at least 6 tests, and a test that asserts train and test share no text.
Never touch the test file after this step.
```
You check: counts add up; fake share is similar in both parts; tests pass.

#### P5. Train both models
```
Implement ml/train.py following 03_TECHNICAL_DESIGN.md sections 5.5, 5.6 and 5.9 exactly.
- Read data/processed/train.csv only.
- Two scikit-learn Pipelines with step names "tfidf" and "clf": TfidfVectorizer(ngram_range=(1,2), max_features=20000, min_df=3, sublinear_tf=True, stop_words="english") + LogisticRegression(class_weight="balanced", solver="liblinear"), and the same vectorizer + RandomForestClassifier(class_weight="balanced_subsample", n_jobs=-1, random_state=42).
- Tune with GridSearchCV, 5-fold StratifiedKFold, scoring="f1", over the parameter ranges in 5.6 only.
- For each model choose the decision threshold from cross_val_predict probabilities on the training data to maximise F1 of the fake class.
- Save with joblib (compress=3): models/lr_pipeline.joblib and models/rf_pipeline.joblib; print file sizes and warn if over 50 MB.
- Save models/model_config.json: thresholds, uncertain band 0.10, sklearn version, training date, dataset names and row counts, training row count, best parameters.
- Do NOT evaluate on the test set here. Print training time and cross-validation scores. Comment every step simply.
```
You check: two joblib files under 50 MB; `model_config.json` exists. If too big, use G2.

#### P6. Evaluate once on the test set
```
Implement ml/evaluate.py. Load data/processed/test.csv and the saved models. For each model compute on the test set, with the threshold from model_config.json: accuracy, precision, recall, F1 (fake class), ROC-AUC, PR-AUC (average precision) and the confusion matrix. If data/external/external_test.csv exists, compute the same metrics on it and report it separately as "external test".
Save everything to models/metrics.json (structure: model > split > metric). Save plots into app/static/img/plots/: confusion matrix per model, bar chart comparing precision/recall/F1/accuracy, ROC and PR curves, and bar charts of the top 15 words towards fake and towards real from the Logistic Regression coefficients.
Save a CSV with 10 false positives and 10 false negatives of the better model. Set "default_model" in model_config.json to the model with the higher test F1. Print a results table.
Do not change any model or threshold after seeing test results.
```
You check: copy the final numbers into `NOTES.md`. A much lower external-test score is the domain-shift limitation you explain in viva. **Commit and push.**

### Stage 3: Backend logic and first pages (Day 3)

#### P7. Predictor and rules
```
Implement app/predictor.py, app/rules.py and their tests following 03_TECHNICAL_DESIGN.md sections 5.7 and 5.8 and 01_PRD.md section 6.1.
- predictor.py: load both pipelines and model_config.json once at start. predict(text, model_key) returns probability of fake, verdict (Likely Fake if p >= T + 0.10, Likely Real if p <= T - 0.10, else Uncertain), threshold, model name, top 8 words towards Fake and top 5 towards Real for THIS text (LogisticRegression coefficient x tf-idf value, always from the LR pipeline), and a function that returns the ad text with matched words highlighted safely (escape first, then wrap in <mark>). Also make_ad_id(text) = SHA-256 of the normalised text. Input goes through ml/preprocess.py.
- rules.py: regex warning flags exactly as listed in 5.8, each with a code and a message. Flags never change the verdict.
- tests/test_predictor.py and tests/test_rules.py with at least 10 tests (thresholds, ad_id stability, each flag, empty input, escaped output).
Run all tests.
```
You check: tests pass; a quick command-line check with a fake-looking ad and a normal ad gives sensible output.

#### P8. Flask foundation and design system
```
Create the Flask app following 03_TECHNICAL_DESIGN.md sections 1, 6 and 7 and 02_UI_UX_SPEC.md sections 1 to 5:
- app/__init__.py with create_app(), config from environment (SECRET_KEY, DATABASE_URL, FLASK_ENV), wsgi.py, GET /health.
- templates/base.html: head tags from UI spec section 2 (favicon, apple-touch-icon, og tags, title), Google Fonts, header with dar-logo.svg and the descriptor "Fake Job Detector", desktop menu, mobile hamburger menu, mobile bottom bar, dark footer exactly as in UI spec 5.2 (logo at left, Quick Links, Resources, Contact Us with the phone and email given there), flash messages, skip-to-content link.
- static/css/main.css: all CSS variables and rules from UI spec section 1, buttons, cards, chips, badges, forms, tabs, toast, modal, skeleton, grid utilities, focus styles, prefers-reduced-motion rules.
- static/js/main.js: fetch wrapper that adds the CSRF token, toast, reveal-on-scroll (IntersectionObserver), count-up function.
- empty but working routes and templates for all 10 pages with correct headings; 404 and 500 pages with the logo.
Do not build page contents yet. Make everything responsive at 375 px and 1280 px.
```
You check: header, footer and logo look right on a phone-width window.

#### P9. Analyze page: text and link
```
Build the Analyze Job page (02_UI_UX_SPEC.md section 7) and the API for text and link:
- Tabs Text | Image | Link. Build Text and Link now; the Image tab shows "coming next".
- POST /api/analyze (03_TECHNICAL_DESIGN.md section 7) using predictor.py and rules.py; validation messages exactly as in the UI spec (fewer than 50 words, empty input). Model selector (segmented control) and the Analyze button with loading state.
- POST /api/fetch in app/fetcher.py with ALL safety rules from 03_TECHNICAL_DESIGN.md section 9 (http/https only, reject private/loopback/link-local addresses after resolving the host, 8 s timeout, 1 MB limit, max 3 redirects re-checked, no cookies) and BeautifulSoup text extraction. Tests for unsafe URLs: localhost, 127.0.0.1, 169.254.169.254, file://, 10.x.x.x.
- Flask-Limiter rate limits and Flask-WTF CSRF as in section 9.
After a successful analysis show a simple temporary result block (the real Result page comes later).
```
You check: paste an ad, get a verdict; unsafe URLs are refused.

### Stage 4: Image input and Result page (Day 4)

#### P10. OCR: import from device and open camera
```
Implement the Image tab (02_UI_UX_SPEC.md section 7.2) and OCR:
- app/ocr.py: validate the upload with Pillow (JPG/PNG only, max 5 MB, verify it is really an image), process in memory only, convert to greyscale, auto-contrast, enlarge small images (target width about 1500 px, never above 4000 px), run pytesseract with lang="eng" (psm 3; if fewer than 20 characters come out, retry with psm 6). Read the Tesseract path from the TESSERACT_CMD environment variable if set. Return the text or a no_text_found error. Never save the image to disk.
- POST /api/ocr (multipart) with the rate limit.
- Two clear buttons: "Open camera" and "Import from device", plus a drag-and-drop zone and image preview.
- Camera: getUserMedia with facingMode "environment", the playsinline attribute, live preview, round capture button, Retake, Switch camera; stop all camera tracks when leaving the tab. If permission is denied or unsupported, show the exact message from the UI spec and highlight "Import from device". Send the captured frame as a JPEG blob to /api/ocr.
- Scanning-laser animation over the image while the text is read, then the editable "Text we read" box with the helper line from the UI spec, then Analyze.
- Tests for ocr.py with a small generated image containing text.
```
You check: import a real Instagram or WhatsApp screenshot; test the camera on the laptop now and on your phone over HTTPS after deployment.

#### P11. Result page
```
Build the Result page exactly in the order of 02_UI_UX_SPEC.md section 8:
1) verdict banner (Likely Fake / Likely Real / Uncertain with icon and text), confidence gauge with count-up, model name and "See the other model's result", "Why DAR says this" (fake words, real words, warning signs), the ad text with highlights;
2) the colour legend card "What the colours mean" with the rows listed in 8.2, placed directly below the result;
3) the "Help others: is this ad genuine or fake?" block with the thumbs up and thumbs down buttons, the counts line, the vote bar, the empty state and the login modal (voting is wired in a later prompt, so for now show the UI with counts 0 and disabled buttons marked TEMPORARY in code);
4) the rating form (UI spec 8.4, wired later), the "What to do next" checklist, buttons, and the disclaimer.
Until the database exists keep results in a small server-side dictionary clearly marked TEMPORARY (to be removed in P12). Animations: gauge sweep and verdict icon animation; all disabled under prefers-reduced-motion. The verdict must also be available as text for screen readers.
```
You check: gauge animates; legend colours match the page; works at 375 px.

### Stage 5: Accounts, community, home (Day 5)

#### P12. Database, accounts and same-ad matching
```
Add the database, accounts and matching following 03_TECHNICAL_DESIGN.md sections 5.4, 8 and 9:
- app/models.py: User, Ad, Vote, Rating exactly as in section 8 (Flask-SQLAlchemy). SQLite locally; DATABASE_URL (PostgreSQL) in production; convert a leading "postgres://" to "postgresql://". db.create_all() at start.
- Remove the TEMPORARY dictionary from P11: every analysis stores or updates an Ad (snippet, full_text, ai_label, ai_probability, model_used, check_count).
- app/matcher.py exactly as in section 5.4: exact SHA-256 match first, then TF-IDF cosine similarity with threshold 0.85 against an in-memory cache of the newest 5000 ads. Tests: exact copy matches, a copy with small OCR-like changes matches, a different ad does not.
- routes_auth.py with Flask-Login: register, login, logout, /auth/me. Password hashing, minimum 8 characters, lowercase unique email, secure cookies (Secure only when FLASK_ENV=production), CSRF, rate limits, redirect after login accepting ONLY relative paths.
- The /auth page exactly as in 02_UI_UX_SPEC.md 9.6 with dar-app-icon.svg; header shows Login/Sign up or the avatar menu.
- Tests: register, duplicate email, wrong password, login required behaviour.
```
You check: sign up, log out, log in; the password is not readable in the database; two screenshots of one ad open the same Result page.

#### P13. Thumbs verification, ratings and Community page
```
Implement community verification and ratings (01_PRD.md F8, F11, F13, F14; 02_UI_UX_SPEC.md 8.3, 8.4, 9.1):
- POST /api/ads/<ad_id>/vote (login required; one vote per account per ad; changeable; thumbs down = "fake", thumbs up = "genuine") and GET /api/ads/<ad_id>. Wire the thumbs buttons: selected state, counts "N users marked this ad as fake | M marked it as genuine", vote bar with percentages, empty state, login modal, amber disagreement note when the AI verdict and the majority of at least 3 votes differ. Counts update without reloading.
- POST /api/ads/<ad_id>/rating (login required; stars 1-5; optional comment up to 200 characters; one per account per ad; comments saved with approved=false). Wire the rating form.
- GET /api/community with filter (all, fake, genuine, disputed), search q, sort and page; Disputed = both sides have at least 3 votes and the smaller side at least 30%. Build the Community page with search, filter chips, ad cards, pagination and empty state.
- Tests: vote uniqueness and changing a vote, disputed logic, login required, ratings saved but not shown until approved.
```
You check: vote with two accounts; the same account cannot double vote.

#### P14. Home page
```
Build the Home page exactly in the order of 02_UI_UX_SPEC.md section 6: banner (headline, sub-text, animated shield/scan graphic, no button inside), the four proof boxes (6.3) filled from GET /api/home, the "Analyze Job Now" button under the boxes, How DAR works (4 steps), Why choose DAR (6 cards with the exact text), Ratings and what users say (average of ALL ratings with count, up to 6 approved 4-5 star comments, the empty state when none), and the footer.
Implement GET /api/home as in 03_TECHNICAL_DESIGN.md section 7: analyses_total = sum of ads.check_count; training_rows from model_config.json; accuracy, recall, precision of the default model from metrics.json; average rating over ALL ratings; reviews = approved comments with 4 or 5 stars, newest 6, first name only.
No number may be hard-coded; if data is missing show "n/a". Priority 1 animations from UI spec section 10 only; all respect prefers-reduced-motion. Do not add libraries except Chart.js.
```
You check: boxes show real values; with no ratings the empty message shows; approve a test comment with the SQL query in 03_TECHNICAL_DESIGN.md section 8 and see it appear.

### Stage 6: Remaining pages, quality, packaging (Day 6)

#### P15. Awareness, Performance, FAQ, About
```
1. Create app/static/data/india_stats.json with ONLY the statistics in 02_UI_UX_SPEC.md section 14, each with value, unit, period, source name and a checked_on date. Serve it at GET /api/stats. Add no other statistic.
2. Awareness page (UI spec 9.2): animated counters and charts from /api/stats (Chart.js), "Where the money goes" donut (only the share given in the data), tips carousel (10 tips from UI spec section 13), "If you have been scammed" steps, the visible note about what the figures cover, and an empty-state for "Job scam stories".
3. Model Performance page (UI spec 9.3): read models/metrics.json and model_config.json through /api/metrics; metrics table for both models, confusion matrix images, comparison chart, top-words chart, dataset and split sizes, external test results if present, and the note about why accuracy alone is misleading.
4. FAQ page (UI spec 9.4) using the exact questions and answers in section 12 of the UI spec, as an accessible accordion.
5. About page (UI spec 9.5) with the sections listed there; the limitations come from 03_TECHNICAL_DESIGN.md section 14; creator line "Created by Devansh Mittal".
```
You check: every number on screen matches the JSON files.

#### P16. Security, accessibility, responsive QA
```
Review the whole project against 01_PRD.md, 02_UI_UX_SPEC.md sections 11 and 15, and 03_TECHNICAL_DESIGN.md sections 9 and 10. Produce a checklist table (item, status, file), then fix every failure:
- security: password hashing, CSRF on every POST, rate limits, cookie flags, no secrets in code, URL fetch safety, upload checks, output escaping (try script text in the analyze box and in comments), no stack traces to users, ratings hidden until approved,
- accessibility: keyboard use of tabs, camera buttons, modal, accordion, carousel, thumbs buttons; labels; contrast; focus outlines; alt text; reduced motion,
- responsive: 375, 768 and 1280 px for all 10 pages, no horizontal scroll,
- check that no hard-coded statistic, rating, review or count exists anywhere in templates or JavaScript,
- run all pytest tests and fix failures, remove dead and temporary code.
Do not add features or libraries.
```

#### P17. Docker, configuration, README
```
Prepare deployment following 03_TECHNICAL_DESIGN.md section 11:
- Dockerfile: FROM python:3.11-slim; apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng and clean the apt cache; copy requirements.txt first and pip install --no-cache-dir; copy the project; run as a non-root user; start gunicorn "wsgi:app" bound to the PORT environment variable with 1 worker, 2 threads, timeout 120.
- .dockerignore (data/raw, data/processed, .git, .venv, __pycache__, tests).
- Pin exact versions in requirements.txt from my working environment (pip freeze, keep only packages we use and their dependencies). Check that the scikit-learn version equals the one in models/model_config.json.
- Production config: FLASK_ENV=production turns on Secure cookies; DATABASE_URL from the environment.
- README.md: what DAR is, features, tech stack, how to run locally (Windows and Mac/Linux commands), how to train the models, how to run tests, environment variables, how to deploy, dataset sources and licences, limitations, author "Devansh Mittal", placeholders [LIVE_URL] and [GITHUB_REPO_URL].
- If Docker is installed, build and run the image locally and tell me the commands; if not, say so.
```
You check: pinned versions; sklearn versions match; README complete. **Commit and push, then deploy (section 8).**

---

## 5. Fix-it prompts

**G1. Agent broke a rule**
```
Stop. You used something not allowed by 03_TECHNICAL_DESIGN.md section 3 (or changed the scope or the documents). Undo it, use only the allowed technologies, and list exactly which files you changed back. If you believe the allowed list is not enough, explain why and wait for my decision.
```
**G2. Models too big or server out of memory**
```
The model files are too large for GitHub or free hosting. Without changing the model type, reduce size: lower n_estimators and max_depth for the Random Forest and max_features of the TF-IDF vectorizer to sensible values, retrain with ml/train.py, re-run ml/evaluate.py, and show a before/after table of file sizes and test metrics. Keep each file under 50 MB. Update model_config.json and metrics.json.
```
**G3. Something fails**
```
This is failing: <paste the exact error or describe what you see>. Find the root cause first and explain it in two sentences, then fix it with the smallest change. Run the related tests and show they pass. Do not change unrelated files.
```
**G4. UI does not match**
```
The page <name> does not match docs/02_UI_UX_SPEC.md section <number>. Differences I see: <list>. Fix only these, keep the tokens from main.css, and check it at 375 px and 1280 px.
```
**G5. Explain code for viva**
```
Explain <file> to me like a first-year student: what each function does, the data flow, and the 5 questions an examiner might ask about it with short answers. Do not change the code.
```
**G6. Deployment error**
```
My Render deployment fails with this log: <paste the last 40 lines>. Explain the cause, then change only the files needed (Dockerfile, requirements.txt or config) and give me the exact commands to commit and push.
```

---

## 6. Order of dependencies (why the order matters)
Data (P3-P4) before training (P5), training before evaluation (P6), evaluation files before the Home accuracy box and Performance page, predictor (P7) before any analysis page, database (P12) before voting and ratings (P13), ratings before the Home ratings section (P14). Do not skip ahead.

---

## 7. GitHub steps

**First push (after P2)**, in the Antigravity terminal inside the project folder:
```
git init
git branch -M main
git add .
git status
git commit -m "chore: project scaffold"
git remote add origin https://github.com/<your-username>/dar-fake-job-detector.git
git push -u origin main
```
Before `git add .`, run `git status` and check that `data/raw`, `.env` and `.venv` are NOT listed. If asked to sign in, use GitHub; if it asks for a password, use a GitHub personal access token (GitHub > Settings > Developer settings > Personal access tokens).

**After every prompt that works:** `git add .` then `git commit -m "<message>"` then `git push`.
Suggested messages: `feat: eda plots`, `feat: dataset build and split`, `feat: train LR and RF`, `feat: evaluation and metrics`, `feat: predictor and rules`, `feat: flask base and design system`, `feat: analyze page text and link`, `feat: image ocr and camera`, `feat: result page`, `feat: accounts and matching`, `feat: voting ratings community`, `feat: home page`, `feat: awareness performance faq about`, `chore: security and qa`, `chore: docker and readme`.

**Model files:** the two `.joblib` files (each under 50 MB) are committed because the server needs them; raw data is not. If you retrain, commit the new model files with `model_config.json` and `metrics.json` together.

**Final:** `git tag v1.0` then `git push --tags`; put the live link and a one-line description in the GitHub repository "About" box; replace `[GITHUB_REPO_URL]` in the footer and README.

---

## 8. Hosting steps (Day 6)

1. **Neon:** neon.com > sign up > create a project named `dar` (region closest to India if offered) > copy the connection string (contains the password; keep it private).
2. **Render:** render.com > New > Web Service > connect GitHub > choose the repo > runtime **Docker** > instance type **Free**.
3. Environment variables: `SECRET_KEY` (generate: `python -c "import secrets; print(secrets.token_hex(32))"`), `DATABASE_URL` (Neon string), `FLASK_ENV=production`.
4. Advanced: health check path `/health`; auto-deploy on.
5. Create. The first build takes several minutes. When it says "Live", open the `.onrender.com` link. (Render's wording may differ slightly.)
6. Free-plan behaviour: sleeps after 15 minutes idle (about 1 minute to wake), no persistent disk (so the database is on Neon and models are inside the image), limited monthly instance hours. Open the link 5 minutes before any demo.
7. If it runs out of memory (restarts or errors on analysis): use G2, or deploy Logistic Regression only on the live site (keep Random Forest local) and explain it in viva.
8. After deploy, test everything in section 9, then update the README and the footer GitHub link.

---

## 9. Test on phone and laptop (Day 6 to 7)

Open the live link on your phone using mobile data (not home Wi-Fi) and on a laptop. Tick each:
- [ ] Home loads, animations play, four boxes show real values, "Analyze Job Now" works
- [ ] Footer: logo at left, Quick Links, Resources, phone and email links work
- [ ] Text analysis gives verdict, confidence, reasons, legend, thumbs
- [ ] Link analysis works on a real job page
- [ ] Import a screenshot of an Instagram or WhatsApp job ad: text appears, edit, analyze
- [ ] Open camera on the phone (allow permission), capture a printed poster, analyze
- [ ] Sign up, log in, thumbs down, change to thumbs up, counts update
- [ ] Analyze the same ad again from a second screenshot: the same community counts show
- [ ] Submit a rating; it is NOT on Home until you approve it in Neon; approve it; it appears
- [ ] Performance page numbers match `metrics.json`; FAQ and About pages open
- [ ] No sideways scrolling on the phone; 404 page shows the logo

If the phone camera does not open: the link must start with `https://`; allow camera permission in browser settings; or use "Import from device", which opens the phone camera app.

---

## 10. Demo script (5 minutes)

1. Open the live site (already awake): header and logo, banner, four boxes (explain the numbers are real and where they come from), click Analyze Job Now.
2. Paste a fake-looking ad (asks for a registration fee): show Likely Fake, confidence, top words, warning signs, then the colour legend.
3. Paste a genuine-looking ad: show Likely Real or Uncertain and explain Uncertain.
4. Import a screenshot you prepared from Instagram or WhatsApp: show the text DAR read, correct one word, analyze.
5. On your phone, open the camera and scan a printed poster.
6. Log in, give a thumbs down, show the counts; open the Community page.
7. Show the Performance page: explain precision, recall, F1 and why accuracy alone is misleading with about 5% fake ads; mention the external test.
8. Close with limitations and future scope (Hindi, more fake examples, better OCR).

Backup: a screen recording of this demo and the app running locally.

---

## 11. PPT outline (12 slides)

1. Title: DAR, Fake Job Detector (logo, your name)
2. The problem (fake job ads; use the sourced statistics from the Awareness page)
3. Objective and users
4. Features overview (screens)
5. System architecture diagram
6. Data: sources, sizes, class imbalance
7. Pipeline: cleaning, TF-IDF, split
8. Models: Logistic Regression and Random Forest
9. Results: accuracy, precision, recall, F1, confusion matrix, external test
10. Explainability and community verification
11. Live demo (screenshots plus link)
12. Limitations, future scope, thank you

---

## 12. Viva preparation checklist (be able to answer)

- Where did the data come from; how many rows; how many fake; the licence.
- How the train/test split was made and why the test set is used once.
- What TF-IDF is; what Logistic Regression and Random Forest do; why these two.
- Why accuracy alone is misleading here; what precision, recall, F1 and the confusion matrix mean.
- How class imbalance and the decision threshold were handled.
- What "Uncertain" means and how the verdict is decided.
- How OCR works in the app and what happens if it reads wrongly.
- How the same ad is recognised across screenshots (similarity) and its limits.
- How votes and ratings are stored; why login; why comments are approved by you.
- How the site is hosted and why it can be slow after idle.
- Limitations (Technical Design section 14) and future scope.
- Why the name DAR ("fear" in Hindi: fake ads should fear it).

---

## 13. Ready-to-start summary

You need: the four documents, the four logo files, the Kaggle CSV, free accounts (GitHub, Kaggle, Neon, Render), Python 3.11, Git, Tesseract, Antigravity. Then: open the folder, paste P0, send P1, read the plan, send P2, and follow the prompts in order, committing after each one.
