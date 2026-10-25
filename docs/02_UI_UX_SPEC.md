# Document 2: UI / UX Specification

**Product:** DAR (Fake Job Detector) | **Creator shown on site:** Devansh Mittal
**Style:** clean, light, professional, mobile first. Works on phone, tablet and laptop.
Antigravity must follow this file exactly. Do not change colours, fonts, copy, order of sections or logo rules without the owner's approval.

---

## 1. Design tokens

### 1.1 Colours (define as CSS variables on `:root`)

| Token | Hex | Use |
|---|---|---|
| `--primary` | #1D4ED8 | Buttons, links, active tab, highlights |
| `--primary-dark` | #1E40AF | Button hover |
| `--accent` | #0D9488 | Teal accent, icons, positive highlights |
| `--bg` | #F8FAFC | Page background |
| `--surface` | #FFFFFF | Cards, forms |
| `--text` | #0F172A | Headings, body text; also dark footer background |
| `--text-muted` | #475569 | Captions and helper text |
| `--border` | #E2E8F0 | Borders, dividers |
| `--primary-soft` | #DBEAFE | Soft blue backgrounds |
| `--real` | #16A34A | Likely Real, genuine votes |
| `--real-soft` | #DCFCE7 | Real badge background |
| `--fake` | #DC2626 | Likely Fake, fake votes |
| `--fake-soft` | #FEE2E2 | Fake badge background |
| `--warn` | #F59E0B | Uncertain, warning flags |
| `--warn-soft` | #FEF3C7 | Uncertain badge background |

Rules: text on `--primary` is white; meaning is never given by colour alone (always an icon and a label); text contrast at least 4.5:1 (for amber use dark text `#78350F` on `--warn-soft`, never white on amber).

### 1.2 Typography (Google Fonts)
- Headings: **Plus Jakarta Sans** 600 and 700 (800 for the hero headline).
- Body: **Inter** 400 and 500.
- Sizes: H1 44 px (phone 32), H2 32 (phone 24), H3 20, body 16, caption 13. Line height 1.5 for body.

### 1.3 Shape, spacing, shadow
Card radius 16 px, button radius 12 px, input radius 10 px, chip radius 999 px. Shadow `0 4px 20px rgba(15,23,42,0.06)`. 8 px spacing scale. Content max width 1140 px. 16 px side padding on phones. Section vertical spacing 64 px desktop, 40 px phone.

### 1.4 Icons
One set only: Lucide (use inline SVG files stored in the project, not a CDN). Icons: shield, scan-search, camera, image, link, file-text, users, thumbs-up, thumbs-down, alert-triangle, check-circle, star, phone, mail, map-pin, globe, clock, menu, x.

### 1.5 Buttons
- **Primary:** `--primary` background, white text, 48 px high, 12 px radius, hover `--primary-dark` + slight lift.
- **Secondary:** white background, `--primary` border and text.
- **Ghost:** no border, `--primary` text.
- **Danger:** `--fake` (only for destructive actions).
- Disabled and loading states (spinner and text "Analyzing...").
- Touch targets at least 44 px.

---

## 2. Logo and brand

**Files** (copy to `app/static/img/`): `dar-logo.svg` (light backgrounds), `dar-logo-white.svg` (dark backgrounds), `dar-app-icon.svg`, `favicon.svg` (browser tab only). The logo is the letters D, A, R with a teal check mark as the crossbar of the A.

| Place | File | Size |
|---|---|---|
| Header (top of every page) | `dar-logo.svg` | 40 px high desktop, 32 px phone, links to `/` |
| Footer (left column, dark background) | `dar-logo-white.svg` | 44 px high |
| Login / Sign up page | `dar-app-icon.svg` | 64 px, centred above the heading |
| Loading screen | `dar-logo.svg` | 160 px wide; the teal check draws itself (1.2 s loop) |
| Error pages | `dar-logo.svg` | 160 px wide |
| Browser tab | `favicon.svg` (letter D with teal check) | tab only, never shown on pages |
| Link previews (WhatsApp, LinkedIn) | `og-image.png` generated from the logo | 1200x630 |

Rules: clear space around the logo of at least 25% of its height; minimum height 24 px; do not recolour, stretch, rotate, outline, add shadows; do not put the colour logo on blue (use the white one). Every `<img>` has `alt="DAR"`. Generate PNGs (`favicon-32.png`, `apple-touch-icon.png` 180 px, `icon-192.png`, `icon-512.png`, `og-image.png`) from the SVGs.

Head tags for every page:
```html
<link rel="icon" type="image/svg+xml" href="/static/img/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/static/img/favicon-32.png">
<link rel="apple-touch-icon" href="/static/img/apple-touch-icon.png">
<meta name="theme-color" content="#1D4ED8">
<meta property="og:image" content="/static/img/og-image.png">
<title>DAR | Check before you apply</title>
```

---

## 3. Site map and navigation

Pages: Home `/`, Analyze Job `/analyze`, Result `/result/<ad_id>`, Community `/community`, Scam Awareness `/awareness`, Model Performance `/performance`, FAQ `/faq`, About `/about`, Login / Sign up `/auth`, Error page.

**Header (all pages, sticky, white, shadow on scroll):**
- Left: `dar-logo.svg` and, next to it in muted text, the descriptor "Fake Job Detector" (this shows the name and the logo as requested).
- Centre (desktop): Home, Analyze Job, Community, Awareness, Performance, FAQ, About.
- Right: "Login" (ghost) and "Sign up" (secondary). After login: avatar circle with the user's initial and a menu: "My votes" (optional), "Log out".
- Phone: logo left, hamburger right opens a full-height menu with the same links and a primary "Analyze Job" button.
- Mobile bottom bar (phones only, fixed): Home, Analyze (centre, highlighted), Community, FAQ.

---

## 4. Components to build once and reuse

Header, MobileMenu, BottomNav, Footer, Logo (props: light/white/icon, height), PageLoader, Button, Chip, Badge (fake/real/uncertain/disputed), Card, StatBox, Tabs, TextArea (with counter), TextInput, FileDropZone, CameraCapture, ImagePreviewWithScan, EditableTextBox, SegmentedControl, Spinner, SkeletonLoader, Toast, Modal (login required), Accordion, Carousel, StarRating (input and display), RatingSummary, ReviewCard, ConfidenceGauge, ReasonList, HighlightedText, ColourLegend, ThumbsVote, VoteBar, AdCard, FilterChips, SearchBox, Pagination, EmptyState, ErrorState, StepCard, FeatureCard.

---

## 5. Global layout

### 5.1 Header: see section 3.

### 5.2 Footer (dark `--text` background, white text, all pages)
Four columns on desktop (two columns on tablet, stacked on phone). Logo at the left.

| Column | Content |
|---|---|
| **Left: brand** | `dar-logo-white.svg` (44 px). Under it: "Check before you apply." and "Your safety is our priority." |
| **Quick Links** | Home, Analyze Job, Community, Scam Awareness, Model Performance, FAQ, About |
| **Resources** | "Report cyber fraud" (https://cybercrime.gov.in, opens in a new tab); "Cyber fraud helpline: 1930" (tel:1930); "GitHub repository" (`[GITHUB_REPO_URL]`, opens in a new tab) |
| **Contact Us** | Phone: 9412494909 (link `tel:+919412494909`); Email: devanshmittal051@gmail.com (link `mailto:devanshmittal051@gmail.com`); Location: Chandigarh, India (map-pin icon) |

Bottom bar (thin divider above): "© 2026 DAR. Created by Devansh Mittal." and on the right the disclaimer "DAR is a decision-support tool and can be wrong. Never pay money to get a job."

---

## 6. Home page (`/`), top to bottom

### 6.1 Header (section 3)

### 6.2 Banner (hero)
Background: `--primary-soft` fading to `--bg`. Two columns on desktop (text left, graphic right); on phones text first, graphic below.
- Small chip: "AI + Community powered"
- H1: **Is this job real? Check before you apply.**
- Sub-text: "Paste an ad, upload a screenshot or scan a poster with your camera. DAR tells you if it looks fake, why, and what other people say about it."
- Right graphic (animated): a job-ad card with a blue scan line moving over it; a shield with a teal tick pops in at the end; small tags ("Fee demanded", "No company info") float around it.
- No button inside the banner (the main button is placed after the four boxes, as specified). The header always has the "Analyze Job" link.

### 6.3 Four proof boxes (directly below the banner; 4 across on desktop, 2x2 on tablet, stacked on phone)
Each box: white card, icon in a soft circle, big animated number or text, small label, small supporting lines. Numbers count up when the box scrolls into view. Hover: lift and shadow.

| # | Icon | Big text | Label | Small lines |
|---|---|---|---|---|
| 1 | shield-check | Live count (from database), e.g. "128" | **Jobs analyzed** | "Trained on {N} job ads" (N from `model_config.json`) |
| 2 | target | Accuracy % from `metrics.json` (test set) | **Detection accuracy** | "Catches {recall}% of fake ads" and "{precision}% precision" (from `metrics.json`); footnote "Measured on test data the model never saw" |
| 3 | smartphone | "Works everywhere" | **Platform support** | Line 1: "Phone, tablet and laptop browsers" Line 2: "Reads screenshots from Instagram, WhatsApp, LinkedIn" |
| 4 | clock | "24/7" | **Available any time** | "Check any job ad, any time" and "Your safety is our priority" |

Rules: no number is hard-coded; if the database count is 0, show 0; if metrics are missing, show "n/a", never a made-up number. Box 3 text means screenshots from any app can be uploaded; DAR is not connected to those apps, so do not say "integrated".

### 6.4 Main call to action
Centred under the boxes: large primary button **"Analyze Job Now"** (with a scan icon) that links to `/analyze`. Under it a small line: "Free. No payment. Never share your bank details with a recruiter." Subtle pulse animation on the button (stops under reduced motion).

### 6.5 How it works
Heading "How DAR works". Four step cards in a row (stacked on phones) with numbers 1 to 4 and a thin connecting line that draws in on scroll:
1. **Add the job ad** - "Paste the text, upload a screenshot, open your camera or paste a job link."
2. **DAR reads it** - "For images, DAR reads the text on the picture. You can correct the text before checking."
3. **The model checks it** - "A model trained on thousands of real and fake job ads scores the wording and looks for warning signs such as fee demands."
4. **See the result and verify** - "Get a verdict, a confidence score and the reasons. Then tell others whether the ad was genuine or fake."

### 6.6 Why choose DAR
Heading "Why choose DAR". Six feature cards (3x2 on desktop). Only these statements (all true by design):
1. **Explains its answer** - "See the exact words and warning signs behind every verdict."
2. **Works with screenshots and photos** - "Check ads from Instagram, WhatsApp or a printed poster."
3. **Community verified** - "See how many users marked the same ad as fake or genuine."
4. **Honest about accuracy** - "Our accuracy, precision and recall are published openly on the Performance page."
5. **Private by design** - "Uploaded images are never stored."
6. **Free to use** - "No payment, ever. Real employers never ask you to pay either."

### 6.7 Ratings and what users say
Heading "What users say about DAR".
- Left/top: **RatingSummary**: average stars of ALL ratings (one decimal, e.g. 4.3 / 5), the star icons and "Based on {count} ratings". Optional small bar chart of the 1 to 5 star distribution.
- Right/below: up to 6 **ReviewCards** (stars, comment, first name, date), only comments with 4 or 5 stars that the owner approved. Carousel on phones.
- Empty state (no ratings yet): "No ratings yet. Analyze a job ad and be the first to rate DAR." (no placeholder reviews, ever).
- Note under the section: "Ratings come only from users who have analyzed an ad. Comments are reviewed before they appear."

### 6.8 Footer (section 5.2)

(There is no separate FAQ, statistics or community block on the home page; those live on their own pages.)

### 6.9 Home wireframe
```
[logo DAR  Fake Job Detector]  Home Analyze Community Awareness Performance FAQ About   [Login][Sign up]
------------------------------------------------------------------------------------------------
 (AI + Community powered)                               +------------------------+
 Is this job real?                                      |  job ad card           |
 Check before you apply.                                |  ~~ scan line ~~       |
 Paste an ad, upload a screenshot...                    |  [shield tick]         |
                                                        +------------------------+
------------------------------------------------------------------------------------------------
 [ Jobs analyzed ] [ Detection accuracy ] [ Platform support ] [ Available any time ]
------------------------------------------------------------------------------------------------
                          [  Analyze Job Now  ]
                  Free. No payment. Never share your bank details...
------------------------------------------------------------------------------------------------
 How DAR works:   (1)--(2)--(3)--(4)
------------------------------------------------------------------------------------------------
 Why choose DAR:  [card][card][card] / [card][card][card]
------------------------------------------------------------------------------------------------
 What users say:  [4.3 / 5 stars, N ratings]   [review] [review] [review]
------------------------------------------------------------------------------------------------
 FOOTER: [logo]       Quick Links      Resources         Contact Us
         tagline      Home ...         Report fraud...   9412494909 ...
------------------------------------------------------------------------------------------------
```

---

## 7. Analyze Job page (`/analyze`)

Heading "Analyze a job ad". Sub-text "Choose how you want to add the ad." A privacy note: "Do not include personal details in what you submit."
A tab bar with three tabs (icons and labels): **Text** | **Image** | **Link**. Below the tabs, the active panel inside one card. Under the card: model selector (segmented control: "Logistic Regression" | "Random Forest", default Logistic Regression) and the large primary button **"Analyze"**.

### 7.1 Text tab
Large text area (at least 10 rows), placeholder "Paste the full job ad here (title, company, description, contact details, salary)". Live word counter. "Clear" link. Validation: fewer than 50 words shows "Please paste the full ad (at least 50 words)."

### 7.2 Image tab
Two clear option buttons side by side (stacked on phones), then the drop zone:
- **Open camera** (camera icon): opens a live camera preview inside the card with a round capture button, "Retake" and "Switch camera" (rear camera first). The camera stops when the user captures, switches tab or leaves. If permission is denied or not supported: message "We couldn't open the camera. Allow camera access in your browser settings, or import a photo instead." and the **Import from device** button highlights.
- **Import from device** (image icon): opens the file picker (JPG/PNG up to 5 MB). On a phone the system picker offers the camera or gallery.
- Drop zone text: "Drag an image here, or use the buttons above."
- After an image is chosen or captured: image preview, a scanning-laser animation over the image while the text is read, then an editable box **"Text we read"** with the helper line "Looks wrong? Edit it before analyzing." If no text is found: "We couldn't read any text. Try a clearer photo or paste the text instead."

### 7.3 Link tab
URL input and "Fetch ad" button. The fetched text appears in the same editable box. Error: "We couldn't read that page (it may need a login). Paste the text instead."

### 7.4 States
Empty (button disabled until there is enough text), loading ("Analyzing..." with spinner and the logo-check animation), error (red-soft box with a clear message and what to do), success (go to the Result page).

---

## 8. Result page (`/result/<ad_id>`)

Order from top to bottom, in one centred column (max width 860 px) on all screen sizes:

### 8.1 Result block
1. **Verdict banner**: full-width coloured card with icon + text, never colour alone:
   - Likely Fake: `--fake-soft` background, red icon (alert-triangle), text "Likely FAKE"
   - Likely Real: `--real-soft`, green icon (check-circle), text "Likely REAL"
   - Uncertain: `--warn-soft`, amber icon, text "UNCERTAIN: please verify"
2. **Confidence gauge**: semicircle that sweeps to the percentage with a counting number. Label "Chance this ad is fake: 92%". Under it: "Model used: Logistic Regression" and a "See the other model's result" button.
3. **Why DAR says this**:
   - "Words that pushed towards FAKE" (up to 8 chips with small weight bars, red-soft)
   - "Words that pushed towards REAL" (up to 5 chips, green-soft)
   - "Warning signs found" (list with amber icon: asks for money or fee; asks for bank, Aadhaar, PAN or OTP; contact only on WhatsApp or Telegram; free email address as company contact; "no interview" or "instant joining"; unrealistic pay; urgency pressure; no company name). Shown only when triggered; if none: "No warning signs found in the text."
4. **The ad text** with highlights: red-soft highlight = words that pushed towards fake; amber-soft highlight = words that triggered a warning sign.

### 8.2 Colour legend (directly below the result, as requested)
Heading "What the colours mean". A card with rows, each a colour swatch, the label and one line:

| Swatch | Label | Meaning |
|---|---|---|
| Red | Likely Fake | The model thinks this ad is probably fraudulent. Do not pay or share personal details. |
| Green | Likely Real | The model found no strong signs of fraud. Still verify the company yourself. |
| Amber | Uncertain / Warning | The model is not sure, or a warning sign was found. Check the company's official website. |
| Red highlight | Fake-leaning words | Words in the ad that pushed the score towards fake. |
| Amber highlight | Warning signs | Phrases that match common scam tricks (for example asking for a fee). |
| Green bar | Marked genuine | Share of users who marked this ad as genuine. |
| Red bar | Marked fake | Share of users who marked this ad as fake. |

### 8.3 Verify this ad (directly below the legend, as requested)
Heading "Help others: is this ad genuine or fake?" Two large buttons with icons and labels:
- **Thumbs up: "This ad is genuine"** (green outline, `--real`)
- **Thumbs down: "This ad is fake"** (red outline, `--fake`)

Under the buttons:
- Counts line (always shown): "**{N}** users marked this ad as fake | **{M}** users marked it as genuine".
- VoteBar: stacked red/green bar with percentages and total votes.
- If no votes: "No community votes yet. Be the first to verify this ad."
- Logged out: clicking opens a Modal "Log in to verify this ad" with Login and Sign up buttons (returns to this page afterwards).
- Selected state: the user's chosen button is filled; text "You marked this ad as fake. You can change your vote."
- Disagreement note (amber, when the AI verdict and the majority of at least 3 votes differ): "The AI and the community disagree. Verify the company on its official website."
- Counts update without reloading the page.

### 8.4 Rate your experience (after verifying)
Heading "How was this analysis?" StarRating (1 to 5), optional comment box (200 characters max, counter), button "Submit rating". Logged-out: "Log in to rate DAR". After submitting: "Thank you. Comments are reviewed before they appear on our home page."

### 8.5 What to do next
Checklist: verify the company on its official website; never pay a fee for a job; search the company name with the word "scam"; report fraud at cybercrime.gov.in or call 1930. Buttons: "Analyze another ad" and "Copy link".

### 8.6 Disclaimer (always visible)
"DAR is a decision-support tool. It can be wrong. Never pay money to get a job."

---

## 9. Other pages

### 9.1 Community (`/community`)
Heading "Community reports". Search box, filter chips (All, Marked fake, Marked genuine, Disputed), sort (Newest, Most votes). Grid of AdCards: first 120 characters of the ad, AI verdict badge, VoteBar and counts, time ago. Click opens the Result page. Pagination. Empty state "No reports yet. Analyze an ad to start the community board."

### 9.2 Scam Awareness (`/awareness`)
Heading "Job and online fraud in India". Sections:
1. **Animated counters** (count up when visible) and a yearly bar chart from `india_stats.json` (see section 14 for the data).
2. **Where the money goes**: donut chart of the share of losses by scam type (only the figure given in the data file).
3. **Tips carousel** (10 tips, section 13).
4. **If you have been scammed**: steps: stop paying; save screenshots and receipts; call 1930; file a complaint at cybercrime.gov.in; tell your bank immediately.
5. **Job scam stories**: shows an empty-state message until the owner adds verified stories with source links.
Visible note: "These figures cover all online financial fraud in India unless a card says 'job scams'. Source and date are shown under every number."

### 9.3 Model Performance (`/performance`)
Heading "How well does DAR work?" Metrics table for both models (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC), confusion matrix images, comparison bar chart, top-words chart, dataset and split sizes, external test results if available. A note: "Only about 5% of ads in the training data are fake, so accuracy alone can look high. Precision and recall show how well fake ads are caught." All values from `metrics.json`.

### 9.4 FAQ (`/faq`)
Heading "Frequently asked questions". Accordion (one open at a time, keyboard accessible). Questions and answers in section 12.

### 9.5 About (`/about`)
Heading "About DAR". Sections: What DAR is; How it works (steps: Input, Read text, Clean text, TF-IDF, Model, Explanation, Community verification); Data sources (names, sizes, licences from `DATA_SOURCES.md`); Limitations (section 14 of the tech doc, in plain words); The name ("Dar" means fear in Hindi: fake job ads should fear this model); Creator: "Created by Devansh Mittal". Logo (120 px) next to the first paragraph.

### 9.6 Login / Sign up (`/auth`)
`dar-app-icon.svg` (64 px) centred, two tabs (Login | Sign up). Sign up: name, email, password (minimum 8 characters, show/hide), confirm password. Login: email, password. Clear error messages ("Email already registered", "Wrong email or password"). After login, return to the previous page (only relative paths).

### 9.7 Error pages (404, 500)
Logo (160 px), friendly message ("This page could not be found" / "Something went wrong on our side"), button "Go to Home". No technical details.

---

## 10. Animations (all must respect `prefers-reduced-motion`: replace with no or simple fade)

**Priority 1 (build):**
1. Hero scan line over the job-ad card and shield tick pop.
2. Count-up numbers in the four boxes and statistics (once, when visible).
3. Confidence gauge sweep with counting number.
4. Scanning laser over the uploaded or captured image while text is read.
5. Scroll reveal (fade and slide up) for sections.
6. Chart draw-in (bars grow, lines draw) when visible.
7. How-it-works connecting line draws in.
8. Button hover lift and pulse on "Analyze Job Now".

**Priority 2 (only if time):**
9. Words highlighted one by one in the ad text.
10. Verdict icon animation (gentle shake for Fake, tick draw for Real).
11. Vote bar animates when counts change; thumbs "pop" on click.
12. Floating tags around the hero card.
13. Skeleton loaders; tab underline slide.
14. Tips carousel auto-slide with progress bar and pause on hover.

Never: sound, flashing, full-screen blocking animations, anything over 5 seconds that cannot be skipped.

---

## 11. Responsive and accessibility rules

- Breakpoints: phone up to 640 px, tablet 641 to 1024 px, desktop above 1024 px. No horizontal scroll at 375 px.
- Keyboard: all tabs, modal, accordion, carousel and buttons usable with Tab, Enter, Space, Escape; visible focus outline (2 px `--primary`, 2 px offset); skip-to-content link; focus trap in the Modal.
- Every input has a label; errors are announced (`aria-live="polite"`); images have alt text; icon-only buttons have `aria-label`.
- The verdict is announced as text ("Likely fake, 92 percent").
- Colour is never the only signal (icons and labels always present).
- Respect `prefers-reduced-motion` and `prefers-color-scheme` is not used (light theme only).

---

## 12. FAQ content (final text for the FAQ page)

1. **Is DAR 100% accurate?** No. DAR is a decision-support tool. Our measured accuracy, precision and recall are on the Performance page. Always verify a company on its official website.
2. **What does "Uncertain" mean?** The model is not confident either way. Check the company's official website and never pay anything.
3. **How does DAR decide?** It compares the words in the ad with thousands of real and fake job ads it learned from, and also looks for common scam signs such as asking for a fee.
4. **Which data was the model trained on?** A public research dataset of job postings (Kaggle "Real / Fake Job Posting Prediction", based on the EMSCAD dataset from the University of the Aegean) and any extra datasets listed on the About page. The exact sizes are on the Performance page.
5. **Do you store my screenshots or photos?** No. Images are read in memory and deleted. The text that DAR reads is stored so that votes can be matched to the same ad.
6. **How do thumbs up and thumbs down work?** Thumbs up means you believe the ad is genuine. Thumbs down means you believe it is fake. You need an account, you get one vote per ad, and you can change it.
7. **Does the community vote change DAR's verdict?** No. The AI verdict and the community votes are shown separately.
8. **Why do I need an account?** To stop one person voting many times. We store your name, email and a hashed password only.
9. **Why is the first page load slow sometimes?** DAR runs on free hosting that goes to sleep after 15 minutes without visitors and takes up to a minute to wake up.
10. **Can DAR read ads in Hindi?** Not yet. DAR works with English text only.
11. **What should I do if I already paid a scammer?** Stop paying, keep all screenshots and receipts, call the cyber fraud helpline 1930 immediately and file a complaint at cybercrime.gov.in. Tell your bank.
12. **How are ratings shown on the home page?** The star average counts every rating. Written comments appear only after they are reviewed.
13. **Who made DAR?** DAR was created by Devansh Mittal.

---

## 13. Tips content (carousel)

1. Real employers never ask for money: registration, training, kit or security deposit fees are a scam sign.
2. Too good to be true: very high pay for simple work from home.
3. Contact only on WhatsApp or Telegram, with no official company email or website.
4. Offers from free email addresses (gmail, yahoo) instead of a company domain.
5. No interview, instant offer: hired without a proper selection process.
6. Asks for bank details, Aadhaar, PAN or OTP: never share these to get a job.
7. Urgency pressure: "Pay today or lose the seat."
8. Check the company: search its name on the official website and LinkedIn.
9. Typos and vague details: missing address, job role or company name.
10. Already paid? Call 1930 and report at cybercrime.gov.in.

---

## 14. Statistics data for the Awareness page (`app/static/data/india_stats.json`)

Use ONLY these values, each with source, period and `checked_on` date. All are for ALL online financial fraud in India unless stated. The owner must re-check each number on the official source before the demo (cybercrime.gov.in / Ministry of Home Affairs replies in Parliament / NCRB).

| Statistic | Value | Source as reported |
|---|---|---|
| Losses reported, 2023 | about Rs 7,465 crore | I4C data, reported by IANS (Jan 2026) |
| Losses reported, 2024 | about Rs 22,845 crore (about 36.4 lakh complaints, NCRP + CFCFRMS) | Ministry of Home Affairs reply in Parliament, reported July 2025 |
| Losses reported, 2025 | about Rs 22,495 crore | National Cyber Crime Reporting Portal data, reported by Free Press Journal |
| Losses reported, Jan to Jun 2026 | over Rs 10,178 crore (about 12.71 lakh complaints) | MHA-chaired meeting data as reported by a secondary source: verify |
| Total over six years | over Rs 52,976 crore | I4C, reported by IANS (Jan 2026) |
| Share of 2025 losses from fake investment schemes | 76% | I4C data tabled in Parliament, reported by MoneyLife and CyberPeace |
| Share of money recovered in 2025 | about 24% | MoneyLife citing MHA data |
| Cyber crime cases registered by police (NCRB) | 2021: 52,974; 2022: 65,893; 2023: 86,420 (about 69% fraud) | NCRB "Crime in India 2023" |
| Indians rescued from fake-job / cyber-scam rackets in Southeast Asia | over 6,700 (reported Dec 2025) | Business Standard |

Notes: different outlets give slightly different totals for the same year (for example 2025 appears as Rs 19,813 crore in one I4C-based report); show one source per number and be ready to explain this. No official figure for "percentage of people trapped by fake job ads" was found, so none may be shown.

---

## 15. Final UI checklist for Antigravity

- [ ] Header with logo and descriptor on every page; footer with logo at left, Quick Links, Resources, Contact Us (phone 9412494909, email devanshmittal051@gmail.com, Chandigarh, India)
- [ ] Home order: banner, four boxes, "Analyze Job Now", How it works, Why choose DAR, Ratings, Footer
- [ ] Analyze page: Text, Image (Open camera, Import from device), Link
- [ ] Result order: verdict and reasons, colour legend, thumbs verification with counts, rating, next steps
- [ ] FAQ page, About page, Awareness, Performance, Community, Login, Error pages
- [ ] Palette and fonts exactly as section 1; logo rules exactly as section 2
- [ ] No fake numbers, ratings, reviews or claims anywhere
