"""ml/build_dataset.py
Dataset builder and train/test splitter for DAR Fake Job Detector.

Following docs/03_TECHNICAL_DESIGN.md (sections 5.3, 5.5) and prompt P4:
1. Loads datasets listed in DATA_SOURCES.md (primary: data/raw/fake_job_postings.csv).
2. Maps each record to standard [text, label] columns.
3. Cleans text using ml.preprocess.clean_text.
4. Drops empty texts.
5. Drops exact duplicates across all datasets and prints removal counts.
6. Performs a single stratified 80/20 split with random_state=42.
7. Saves:
   - data/processed/train.csv
   - data/processed/test.csv
8. Prints row counts and class distribution for viva reporting.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path so 'from ml.preprocess import ...' works
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.preprocess import build_text, clean_text


def load_primary_dataset(filepath: str | Path = "data/raw/fake_job_postings.csv") -> pd.DataFrame:
    """Load primary dataset (D1) from CSV.

    Args:
        filepath: Path to fake_job_postings.csv.

    Returns:
        pd.DataFrame with 'text' and 'label' columns.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Primary dataset not found at {path.resolve()}")

    print(f"Loading primary dataset from: {path}")
    raw_df = pd.read_csv(path)
    print(f"Raw rows loaded: {len(raw_df):,}")

    # Build concatenated text from the 5 fields
    print("Building and cleaning text representations...")
    combined = raw_df.apply(build_text, axis=1)
    cleaned = combined.apply(clean_text)

    # Label: 1 = fake, 0 = real
    label = raw_df["fraudulent"].astype(int)

    return pd.DataFrame({"text": cleaned, "label": label})


def build_and_split(
    raw_path: str | Path = "data/raw/fake_job_postings.csv",
    output_dir: str | Path = "data/processed",
    test_size: float = 0.20,
    random_state: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute full data preparation pipeline and stratified train/test split.

    Args:
        raw_path: Path to raw primary CSV.
        output_dir: Folder to save train.csv and test.csv.
        test_size: Fraction reserved for final testing (0.20 = 20%).
        random_state: Fixed random seed for reproducibility (42).

    Returns:
        (train_df, test_df)
    """
    df = load_primary_dataset(raw_path)
    initial_count = len(df)

    # 1. Drop empty text entries
    empty_mask = df["text"].str.strip() == ""
    num_empty = empty_mask.sum()
    if num_empty > 0:
        df = df[~empty_mask].copy()
    print(f"Empty texts dropped: {num_empty:,} (remaining: {len(df):,})")

    # 2. Drop duplicate texts
    num_duplicates = df.duplicated(subset=["text"]).sum()
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    print(f"Duplicate texts dropped: {num_duplicates:,} (remaining: {len(df):,})")

    # 3. Stratified 80/20 train/test split
    print(f"\nPerforming stratified {int((1-test_size)*100)}/{int(test_size*100)} split (random_state={random_state})...")
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df["label"]
    )
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # 4. Save processed datasets
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    train_file = out_path / "train.csv"
    test_file = out_path / "test.csv"

    train_df.to_csv(train_file, index=False)
    test_df.to_csv(test_file, index=False)
    print(f"[Saved] Training set -> {train_file} ({len(train_df):,} rows)")
    print(f"[Saved] Testing set  -> {test_file} ({len(test_df):,} rows)")

    # 5. Print class distributions for viva
    print("\n" + "=" * 55)
    print("PROCESSED DATASET SPLIT SUMMARY")
    print("=" * 55)
    print(f"Total initial raw rows:    {initial_count:,}")
    print(f"Empty rows removed:        {num_empty:,}")
    print(f"Duplicate rows removed:    {num_duplicates:,}")
    print(f"Total clean unique rows:   {len(df):,}")

    train_counts = train_df["label"].value_counts()
    train_pct = train_df["label"].value_counts(normalize=True) * 100
    print(f"\nTrain set ({len(train_df):,} rows, {len(train_df)/len(df)*100:.1f}%):")
    print(f"  Real (0): {train_counts.get(0, 0):,} ({train_pct.get(0, 0):.2f}%)")
    print(f"  Fake (1): {train_counts.get(1, 0):,} ({train_pct.get(1, 0):.2f}%)")

    test_counts = test_df["label"].value_counts()
    test_pct = test_df["label"].value_counts(normalize=True) * 100
    print(f"\nTest set ({len(test_df):,} rows, {len(test_df)/len(df)*100:.1f}%):")
    print(f"  Real (0): {test_counts.get(0, 0):,} ({test_pct.get(0, 0):.2f}%)")
    print(f"  Fake (1): {test_counts.get(1, 0):,} ({test_pct.get(1, 0):.2f}%)")
    print("=" * 55 + "\n")

    return train_df, test_df


if __name__ == "__main__":
    build_and_split()
