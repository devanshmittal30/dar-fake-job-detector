# Data Sources

All datasets used by DAR, with sources, sizes and licences.

| ID | Dataset | URL | Rows | Fake | Licence | Date checked |
|-----|---------|-----|------|------|---------|-------------|
| D1 (primary) | Kaggle "Real / Fake Job Posting Prediction" (processed version of EMSCAD, Employment Scam Aegean Dataset, University of the Aegean). File: `fake_job_postings.csv` | https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction | 17,880 | 866 (under 5%) | See the licence text on the Kaggle dataset page (CC0 or as stated) — copy here after downloading | |
| D2 (optional) | _Not verified yet_ | | | | | |
| E1 (external test) | 30 fake + 30 real ads collected by the owner from official scam warnings / news (fake) and known company career pages (real). File: `data/external/external_test.csv`, columns `text,label` (1 = fake) | Owner-collected | 60 (target) | 30 (target) | Owner's own collection | |

## Rules

- Raw CSV files are **never committed** to GitHub (size and licence). See `data/README.md` for download instructions.
- Each dataset must have: a real/fake label made by someone else, job text, and a licence that allows academic use.
- The external test set (E1) is never used for training or tuning.
