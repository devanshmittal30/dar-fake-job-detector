# Data Directory

This folder holds the datasets used by DAR. **Raw and processed CSVs are NOT committed to Git** (see `.gitignore`).

## How to set up the data

### 1. Primary dataset (D1) — required

1. Go to: https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction
2. Sign in with a free Kaggle account.
3. Download `fake_job_postings.csv`.
4. Place it in `data/raw/fake_job_postings.csv`.

### 2. External test set (E1) — recommended

1. Collect 30 fake job ads (from official scam warnings or news reports) and 30 real ads (from known company career pages).
2. Save as `data/external/external_test.csv` with columns: `text,label` (1 = fake, 0 = real).
3. Do NOT write or AI-generate fake ads yourself.

### 3. Optional extra datasets (D2+)

Only add datasets that have:
- A real/fake label made by someone else
- Job text
- A licence allowing academic use

Record each in `DATA_SOURCES.md` at the project root.

## Folder structure

```
data/
├── README.md           (this file)
├── raw/                (Kaggle CSV goes here — NOT in git)
├── processed/          (train.csv and test.csv created by ml/build_dataset.py — NOT in git)
└── external/
    └── external_test.csv   (owner-collected test ads)
```
