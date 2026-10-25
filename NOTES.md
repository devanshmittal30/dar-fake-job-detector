# Notes (viva preparation and development log)

Use this file to record: final metrics, dataset details, problems encountered,
similarity-threshold tuning result, and anything you need for the viva.

## Final Metrics

Evaluation conducted on test set (3,150 ads: 3,008 real, 142 fake, evaluated once after P5 training):

| Metric | Logistic Regression (Default Model) | Random Forest | Notes for Viva |
|---|---|---|---|
| **Decision Threshold ($T$)** | **0.6200** | **0.4900** | Selected via 5-fold CV to maximize fake class $F_1$ |
| **Accuracy** | **98.48%** | 97.56% | Imbalanced dataset baseline (95.49% if always predicting real) |
| **Precision (Fake Class)** | **87.30%** | 78.26% | Out of 126 flagged fake ads by LR, 110 were true fake scams |
| **Recall (Fake Class)** | **77.46%** | 63.38% | Caught 110 out of 142 total fake ads in the test set |
| **$F_1$ Score (Fake Class)** | **82.09%** | 70.04% | Primary metric; LR outperforms RF by +12.05% |
| **ROC-AUC** | **0.9860** | 0.9675 | Ranking discrimination capability across all thresholds |
| **PR-AUC (Average Precision)**| **0.9004** | 0.7810 | High precision maintained across recall levels |
| **Confusion Matrix** | TN: 2,992, FP: 16<br>FN: 32, TP: 110 | TN: 2,983, FP: 25<br>FN: 52, TP: 90 | LR achieved lower false positives and fewer missed fakes |

**Default Model:** Logistic Regression (`lr`) chosen because of superior test $F_1$ (82.09% vs 70.04%).

**External Test Note (Domain Shift):** When evaluated on modern social-media job scam postings (Telegram/WhatsApp task scams), models trained on older EMSCAD data show domain shift. In viva, explain that real-world deployment requires continuous monitoring and user-reported feedback (community voting) to adapt to new scam formats.

## Similarity Threshold Tuning

_To be filled: test result showing the 0.85 threshold works (same-ad pairs match, different ads don't)._

## Problems and Decisions

_Log issues and decisions as you go._
