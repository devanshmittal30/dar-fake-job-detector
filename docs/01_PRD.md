# Document 1: Product Requirements Document (PRD)

**Product:** DAR, Fake Job Posting Detector with community verification
**Tagline:** "Check before you apply."
**Creator:** Devansh Mittal
**Project type:** Individual college project (AI Application Lab, 1st semester, Topic 53 "Fake Job Posting Detection")
**Build tool:** Antigravity (vibe coding) | **Timeline:** 7 days | **Version:** 2.0 (final)

## 0. The document set (give all four to Antigravity)

| File | What it contains |
|---|---|
| `docs/01_PRD.md` (this file) | What the product is, every feature, rules and acceptance criteria |
| `docs/02_UI_UX_SPEC.md` | Every page, component, colour, font, animation, logo placement, exact copy |
| `docs/03_TECHNICAL_DESIGN.md` | Languages, libraries, data sources, ML design, API, database, security, hosting |
| `docs/04_DEVELOPMENT_ROADMAP.md` | Day-by-day plan, setup, how to start in Antigravity, all prompts, GitHub, hosting, tips |
| `dar-brand/` | Logo files (SVG) |

**Rule for Antigravity:** these documents are the only source of truth. If something is not written in them, ask the owner; do not guess, invent, or add technologies, features, statistics or claims.

---

## 1. Overview

DAR is a website that tells a user whether a job advertisement looks fake. The user enters the ad as **text**, as an **image** (open the camera or import a screenshot or photo from the device) or as a **job link**. A machine learning model trained on a public labelled dataset of job postings gives a verdict (Likely Fake, Likely Real or Uncertain), a confidence percentage and the reasons. Below the result the site explains the colours, and the user can give a thumbs up (ad is genuine) or thumbs down (ad is fake). The site shows how many users have marked the same ad as fake or genuine. After an analysis users can rate DAR; the owner approves good comments, and only those appear on the home page.

The name: "Dar" (डर) means fear in Hindi. The idea is that fake job ads should fear this model.

## 2. Problem and users

- **Problem:** fake job ads take money and personal data from job seekers. Students and first-time job seekers are common targets, and many fake ads appear on social media as images or posters, not on job portals.
- **Users:** students and job seekers who want to check an ad before applying.
- **Value:** a fast second opinion with reasons, plus what other people say about the same ad.
- **Outcome from the topic sheet:** helps job portals prevent fraud.

## 3. Goals, non-goals, success criteria

### 3.1 Goals
1. Train and compare exactly two models: Logistic Regression and Random Forest, on TF-IDF features of job-ad text (topic sheet requirement).
2. Report Accuracy, Precision and Recall (required) plus F1, ROC-AUC, PR-AUC and the confusion matrix.
3. Accept three input types (text, image, job link) that all use the same model.
4. Explain every prediction (top words and rule-based warning flags).
5. Community verification: thumbs up / thumbs down with counts per ad; login required.
6. After-analysis ratings with owner-approved comments shown on the home page.
7. Show sourced, animated scam statistics for India.
8. Work on phone and laptop, hosted on a public HTTPS link, code on GitHub.
9. Everything explainable by the owner in viva.

### 3.2 Non-goals (do NOT build)
- Deep learning, transformers, any model other than Logistic Regression and Random Forest.
- Languages other than English.
- Retraining the model from votes or user submissions.
- Payments, email/SMS notifications, an admin dashboard, social login, chat, a mobile app.
- Storing uploaded images (they are processed in memory and discarded).
- Any statistic, rating, review, count or claim that is not real and sourced.

### 3.3 Success criteria
- All three input types work on the live URL on one phone and one laptop (including camera on the phone).
- Both models evaluated once on a held-out test set; all numbers shown on the site come from `metrics.json`.
- Voting works: one vote per account per ad, counts update, logged-out users are asked to log in.
- Ratings work and only owner-approved 4 or 5 star comments appear on the home page.
- Code on GitHub with README; site deployed from that repository.
- Owner can answer the viva questions about data, model, metrics and code.

## 4. Pages in scope (10)

| # | Page | URL |
|---|---|---|
| 1 | Home | `/` |
| 2 | Analyze Job | `/analyze` |
| 3 | Result | `/result/<ad_id>` |
| 4 | Community | `/community` |
| 5 | Scam Awareness | `/awareness` |
| 6 | Model Performance | `/performance` |
| 7 | FAQ | `/faq` |
| 8 | About | `/about` |
| 9 | Login / Sign up | `/auth` |
| 10 | Error (404, 500) | any bad URL |

## 5. Features (what, how it works, acceptance)

| ID | Feature | How it works | Acceptance criteria |
|---|---|---|---|
| F1 | Text input | User pastes the job ad text on the Analyze page; text is cleaned and sent to the model | Fewer than 50 words shows "Please paste the full ad (at least 50 words)"; valid text gives a result in under 3 seconds when the server is awake |
| F2 | Image input: import from device | User picks or drags a JPG/PNG (max 5 MB); server reads the text with OCR; the text appears in an editable box; user presses Analyze | Image never saved; "no text found" message when OCR fails; user can correct the text before analysis |
| F3 | Image input: open camera | Browser opens the camera (rear camera on phones), user captures a photo of a poster or screen; same OCR flow as F2. If the camera is blocked or unavailable, the page offers a file input that opens the phone camera app | Works on one Android or iPhone over HTTPS; camera stops when the user leaves the tab |
| F4 | Link input | User pastes a job page URL; server fetches the page safely and extracts visible text into an editable box; user presses Analyze | Unreadable or login-protected pages show "Paste the text instead"; private/internal addresses are refused |
| F5 | Prediction | Model returns probability of fake; verdict by the rule in section 6.1 | Result shows verdict, confidence %, model used, reasons |
| F6 | Explanation | Top words pushing towards Fake and towards Real (from Logistic Regression), plus rule-based warning flags; matched words are highlighted in the ad text | At least the top words and any triggered flags are listed; highlights are safely escaped |
| F7 | Colour legend | Section on the Result page under the result explaining what each colour means | Legend matches the colours used on the page (see UI spec 8.2) |
| F8 | Thumbs up / thumbs down | Logged-in user marks the ad: thumbs up = "I think this ad is genuine", thumbs down = "I think this ad is fake". Counts shown: "N users marked this fake, M marked genuine" | One vote per account per ad; user can change the vote; counts update without page reload; if no votes: "No community votes yet. Be the first." |
| F9 | Same-ad matching | If a new analysis is nearly identical to an ad already analysed (same text, or similar OCR text of the same ad), it uses the same ad record so votes are shared | Exact copies always match; near copies match above a similarity threshold (see tech doc 5.4); tested with two different screenshots of the same ad |
| F10 | Accounts | Sign up and log in with email + password; log out | Passwords hashed; minimum 8 characters; duplicate email refused |
| F11 | Ratings and comments | After a result, a logged-in user can give 1 to 5 stars and an optional comment (max 200 characters) | One rating per account per ad; comments are hidden until the owner approves them |
| F12 | Home page proof boxes | Four boxes under the banner: jobs analyzed, detection accuracy, platform support, available 24/7 (see UI spec 6.3) | Numbers come from the database and `metrics.json`; nothing hard-coded |
| F13 | Home ratings section | Shows the average of ALL ratings and the number of ratings, plus up to 6 approved comments with 4 or 5 stars | If there are no ratings yet, shows an honest empty message |
| F14 | Community page | List of analysed ads with AI verdict, vote counts, filters (All, Marked fake, Marked genuine, Disputed), search, pagination | Filters work; "Disputed" = both sides have at least 3 votes and the smaller side is at least 30% |
| F15 | Scam Awareness page | Animated statistics and tips for India from `india_stats.json`, each with source and date checked | Every number has a source; page says the figures are for all online financial fraud unless marked as job scams |
| F16 | Model Performance page | Metrics, confusion matrices and charts from `metrics.json` | Values identical to `metrics.json` |
| F17 | FAQ page | Questions and answers (UI spec 12) | Accordion works with keyboard |
| F18 | About page | What DAR is, how it works, data sources, limitations, name meaning, creator | Matches this PRD |
| F19 | Footer | Logo at left, Quick Links, Resources, Contact Us (UI spec 5.2) | Phone and email are clickable; links work |
| F20 | Model switch | Small control on the Result page to see the result from the other model | Model name always shown |

## 6. Business rules

### 6.1 Verdict
The model gives `p` = probability that the ad is fake. Each model has a decision threshold `T` saved in `model_config.json`.
- **Likely Fake** if `p >= T + 0.10`
- **Likely Real** if `p <= T - 0.10`
- **Uncertain** otherwise (the user should verify the ad on the company's official website)

The AI verdict and the community votes are always shown separately. Votes never change the model output. If the AI verdict and the majority of votes disagree (and there are at least 3 votes), show an amber note: "The AI and the community disagree. Verify the company on its official website."

### 6.2 Ad identity
Each analysed ad has one record. The identifier is the SHA-256 hash of the normalised text of the first copy stored. A new analysis is matched to an existing record using the rule in the technical design (exact match first, then similarity).

### 6.3 Votes
One vote per account per ad (fake or genuine), changeable. Only logged-in users can vote. Counts come only from the votes table.

### 6.4 Ratings
- 1 to 5 stars, optional comment up to 200 characters, one rating per account per ad, login required.
- **Home average** = average of ALL ratings (so it cannot be inflated by hiding low ratings), shown with the total number of ratings.
- **Home comments** = only comments with 4 or 5 stars that the owner has approved. The owner approves by setting `approved = true` in the database (no admin page is built). Author shown as first name only.

### 6.5 Statistics shown on the home boxes
- **Jobs analyzed** = total number of analyses done on the site (database count). Starts from the real count. Test analyses made during development count unless the owner clears the data before launch.
- **Training data line** = number of ads in the training data, read from `model_config.json`, labelled "Trained on N job ads".
- **Detection accuracy** = accuracy of the default model on the held-out test set from `metrics.json`, with recall and precision in small text.
- Never display a number that was not produced by the code or the database.

## 7. Data and model (summary; full detail in document 3)

- **Task:** binary text classification (fake = 1, real = 0).
- **Primary data:** Kaggle "Real / Fake Job Posting Prediction" (EMSCAD, University of the Aegean): 17,880 ads, 866 fake (under 5%).
- **Extra data:** only datasets the owner has verified (label, text, licence); each recorded in `DATA_SOURCES.md`.
- **Features:** text only (title, company profile, description, requirements, benefits), because images give text only.
- **Pipeline:** clean text, TF-IDF (1 to 2 word n-grams), then Logistic Regression and Random Forest with class weights.
- **Split:** stratified 80% train / 20% test, fixed seed, test set used once.
- **Metrics:** Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, confusion matrix; plus an owner-collected external test set to measure real-world (social media) performance.

## 8. Non-functional requirements

- **Performance:** text analysis under 3 s; image analysis under 15 s; the free host may need about a minute to wake after 15 minutes idle (explained in the FAQ).
- **Responsive:** works at 375 px, 768 px and 1280 px widths.
- **Browsers:** current Chrome, Edge, Firefox, Safari (desktop and iOS), Chrome on Android.
- **Accessibility:** keyboard usable, visible focus, contrast at least 4.5:1, labels on inputs, alt text, meaning never by colour alone, reduced-motion respected.
- **Reliability:** friendly error pages, no stack traces shown.
- **Maintainability:** small modules, simple comments.

## 9. Security and privacy (summary; detail in document 3)

Hashed passwords, CSRF protection, rate limits, secure cookies, safe URL fetching (no internal addresses), image validation, no image storage, escaped output, secrets only in environment variables. Stored data: name, email, password hash, analysed ad text, votes, ratings. A note on the Analyze page: "Do not include personal details in what you submit."

## 10. Constraints and assumptions

- Free tools only. Hosting: Render free web service (Docker) and Neon free Postgres. Render free services sleep after 15 minutes idle (about 1 minute to wake), have no persistent disk, and have a monthly instance-hours limit. Render's free-instance RAM was not stated on the page checked; confirm before deploying.
- Public labelled fake-job data is limited (under 900 fake ads in the main dataset). More real ads do not add fake examples. "Huge data" is therefore limited by the number of fake examples available.
- Browser camera access needs HTTPS (provided by the host).
- Statistics are copied from public reports and must be re-checked on the official source before the demo.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Few fake examples, low recall | Class weights, tuned threshold, honest reporting, external test |
| OCR errors | Editable text, image preprocessing, retake |
| Same ad does not match across screenshots | Similarity matching (F9), tested |
| Free host sleeps or runs out of RAM | Small models, 1 worker, open the site before the demo, fallback plan in the roadmap |
| Spam votes or ratings | Login required, one per account per ad, rate limits, owner approval of comments |
| Wrong statistics | Every number has source and date; labelled as all online fraud |
| Scope too big for 7 days | Build order in the roadmap; cut optional items first |
| Dataset licence | Raw data not committed; licences recorded |

## 12. Deliverables

- [ ] GitHub repository with README
- [ ] Live website link working on phone and laptop
- [ ] These four documents, `DATA_SOURCES.md`, `NOTES.md` (metrics and issues)
- [ ] Trained models, `metrics.json`, plots
- [ ] PPT, demo script, backup screen recording
- [ ] Viva preparation notes

## 13. Owner placeholders still to fill

| Placeholder | Where used |
|---|---|
| `[GITHUB_REPO_URL]` | Footer Resources link, README |
| `[LIVE_URL]` | README, PPT |
| Extra dataset names and licences | `DATA_SOURCES.md` |
| 60 external test ads (30 fake, 30 real) collected by the owner | `data/external/external_test.csv` |
| Job scam stories (optional, owner-verified with source links) | Awareness page |
