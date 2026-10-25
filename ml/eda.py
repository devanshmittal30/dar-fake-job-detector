"""ml/eda.py
Exploratory Data Analysis for DAR Fake Job Detector.

Loads raw job postings data and generates:
1. Console summary: shape, columns, missing values.
2. Plots saved to app/static/img/plots/:
   - eda_class_balance.png: Count and % of fake vs real ads.
   - eda_text_length_distribution.png: Word count distribution for fake vs real ads.
   - eda_top_words.png: Top 20 most frequent words in fake vs real ads.
   - eda_categorical_fraud_rates.png: Fraud rate by company logo, employment type, and experience.

No machine learning models are trained in this script.
"""

from pathlib import Path
import matplotlib
# Use Agg backend for non-interactive server/script plot generation
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer


# Palette matching DAR design spec (docs/02_UI_UX_SPEC.md)
COLOR_REAL = "#16A34A"  # Green
COLOR_FAKE = "#DC2626"  # Red
COLOR_PRIMARY = "#0284C7"  # Brand blue/teal
COLOR_TEXT = "#0F172A"  # Dark slate for headings/labels


def load_dataset(filepath: str | Path) -> pd.DataFrame:
    """Load the job postings CSV dataset.

    Args:
        filepath: Path to the CSV file.

    Returns:
        pd.DataFrame containing the dataset.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path.resolve()}")
    return pd.read_csv(path)


def print_dataset_overview(df: pd.DataFrame) -> None:
    """Print dataset shape, column names, and missing value counts to the console.

    Args:
        df: Input DataFrame.
    """
    print("\n" + "=" * 60)
    print("DAR DATASET EXPLORATORY ANALYSIS OVERVIEW")
    print("=" * 60)

    # 1. Shape
    print(f"\n1. Dataset Dimensions:")
    print(f"   Total rows:    {df.shape[0]:,}")
    print(f"   Total columns: {df.shape[1]}")

    # 2. Columns
    print(f"\n2. Columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns, start=1):
        print(f"   {i:2d}. {col} ({df[col].dtype})")

    # 3. Missing values
    print("\n3. Missing Values per Column:")
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df)) * 100
    missing_table = pd.DataFrame({
        "Missing Rows": missing_count,
        "Percentage (%)": missing_pct.round(2)
    })
    # Show columns sorted by most missing first
    missing_table = missing_table.sort_values(by="Missing Rows", ascending=False)
    print(missing_table.to_string())

    # 4. Class balance summary
    if "fraudulent" in df.columns:
        counts = df["fraudulent"].value_counts()
        pcts = df["fraudulent"].value_counts(normalize=True) * 100
        print("\n4. Class Distribution ('fraudulent'):")
        print(f"   Real ads (0): {counts.get(0, 0):,} ({pcts.get(0, 0):.2f}%)")
        print(f"   Fake ads (1): {counts.get(1, 0):,} ({pcts.get(1, 0):.2f}%)")
    print("=" * 60 + "\n")


def plot_class_balance(df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot and save class balance (count and percentage) of fraudulent (0/1).

    Args:
        df: Input DataFrame containing 'fraudulent' column.
        output_path: Destination image path.
    """
    plt.figure(figsize=(8, 6), dpi=200)

    counts = df["fraudulent"].value_counts().sort_index()
    total = len(df)
    labels = ["Real (0)", "Fake (1)"]
    palette = [COLOR_REAL, COLOR_FAKE]

    ax = sns.barplot(x=labels, y=counts.values, palette=palette, hue=labels, legend=False)

    plt.title("Class Balance: Real vs Fake Job Postings", fontsize=15, fontweight="bold", color=COLOR_TEXT, pad=15)
    plt.xlabel("Job Posting Status", fontsize=12, labelpad=10)
    plt.ylabel("Number of Postings", fontsize=12, labelpad=10)
    plt.ylim(0, max(counts.values) * 1.15)
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    # Annotate counts and percentages on top of each bar
    for i, count in enumerate(counts.values):
        pct = (count / total) * 100
        ax.text(
            i,
            count + (max(counts.values) * 0.02),
            f"{count:,}\n({pct:.2f}%)",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            color=COLOR_TEXT
        )

    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Class balance plot -> {output_path}")


def get_combined_text(df: pd.DataFrame) -> pd.Series:
    """Combine the 5 text fields into a single text series, filling missing with empty string.

    Matches 03_TECHNICAL_DESIGN.md section 5.3:
    title + company_profile + description + requirements + benefits.
    """
    text_cols = ["title", "company_profile", "description", "requirements", "benefits"]
    available_cols = [c for c in text_cols if c in df.columns]

    combined = df[available_cols[0]].fillna("").astype(str)
    for col in available_cols[1:]:
        combined = combined + " " + df[col].fillna("").astype(str)
    return combined


def plot_text_length_distribution(df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot word count distribution comparing fake and real job postings.

    Args:
        df: Input DataFrame.
        output_path: Destination image path.
    """
    combined_text = get_combined_text(df)
    word_counts = combined_text.apply(lambda x: len(x.split()))

    plot_df = pd.DataFrame({
        "word_count": word_counts,
        "fraudulent": df["fraudulent"].map({0: "Real", 1: "Fake"})
    })

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=200)

    # 1. Boxplot (shows median, IQR, and outliers)
    sns.boxplot(
        data=plot_df,
        x="fraudulent",
        y="word_count",
        hue="fraudulent",
        palette={"Real": COLOR_REAL, "Fake": COLOR_FAKE},
        legend=False,
        ax=axes[0],
        showfliers=False  # Hide extreme outliers for readability
    )
    axes[0].set_title("Word Count Boxplot (Outliers Hidden)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Job Posting Status", fontsize=11)
    axes[0].set_ylabel("Number of Words", fontsize=11)
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)

    # 2. KDE Distribution (capped at 99th percentile for clean visualisation)
    p99 = np.percentile(word_counts, 99)
    filtered = plot_df[plot_df["word_count"] <= p99]

    real_subset = filtered[filtered["fraudulent"] == "Real"]
    fake_subset = filtered[filtered["fraudulent"] == "Fake"]

    if len(real_subset) > 0:
        sns.kdeplot(
            data=real_subset,
            x="word_count",
            color=COLOR_REAL,
            label="Real (0)",
            fill=True,
            alpha=0.3,
            warn_singular=False,
            ax=axes[1]
        )
    if len(fake_subset) > 0:
        sns.kdeplot(
            data=fake_subset,
            x="word_count",
            color=COLOR_FAKE,
            label="Fake (1)",
            fill=True,
            alpha=0.3,
            warn_singular=False,
            ax=axes[1]
        )
    axes[1].set_title(f"Word Count Density Distribution (Capped at 99th percentile: {int(p99)})", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Number of Words", fontsize=11)
    axes[1].set_ylabel("Density", fontsize=11)
    handles, labels = axes[1].get_legend_handles_labels()
    if handles:
        axes[1].legend(handles, labels, loc="upper right")
    axes[1].grid(axis="x", linestyle="--", alpha=0.3)

    plt.suptitle("Text Length (Word Count) Distribution: Fake vs Real", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Text length distribution plot -> {output_path}")


def plot_top_words(df: pd.DataFrame, output_path: str | Path, n_words: int = 20) -> None:
    """Extract and plot top N most common words in fake and real ads using CountVectorizer.

    Args:
        df: Input DataFrame.
        output_path: Destination image path.
        n_words: Number of top words to display (default 20).
    """
    combined_text = get_combined_text(df)

    real_text = combined_text[df["fraudulent"] == 0]
    fake_text = combined_text[df["fraudulent"] == 1]

    # CountVectorizer with English stop words and minimum 2 letters
    # token_pattern removes lone digits or punctuation artifacts
    vectorizer_kwargs = {
        "stop_words": "english",
        "token_pattern": r"(?u)\b[a-zA-Z]{2,}\b",
        "max_features": 5000
    }

    # Vectorize Real Ads
    vec_real = CountVectorizer(**vectorizer_kwargs)
    X_real = vec_real.fit_transform(real_text)
    real_counts = np.asarray(X_real.sum(axis=0)).ravel()
    real_words = vec_real.get_feature_names_out()
    top_real_idx = np.argsort(real_counts)[::-1][:n_words]
    top_real_df = pd.DataFrame({
        "word": real_words[top_real_idx],
        "count": real_counts[top_real_idx]
    })

    # Vectorize Fake Ads
    vec_fake = CountVectorizer(**vectorizer_kwargs)
    X_fake = vec_fake.fit_transform(fake_text)
    fake_counts = np.asarray(X_fake.sum(axis=0)).ravel()
    fake_words = vec_fake.get_feature_names_out()
    top_fake_idx = np.argsort(fake_counts)[::-1][:n_words]
    top_fake_df = pd.DataFrame({
        "word": fake_words[top_fake_idx],
        "count": fake_counts[top_fake_idx]
    })

    # Create horizontal bar plot comparison
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), dpi=200)

    # Real words
    sns.barplot(
        data=top_real_df,
        y="word",
        x="count",
        color=COLOR_REAL,
        ax=axes[0]
    )
    axes[0].set_title(f"Top {n_words} Most Common Words in Real Ads", fontsize=13, fontweight="bold", color=COLOR_TEXT)
    axes[0].set_xlabel("Frequency Count", fontsize=11)
    axes[0].set_ylabel("Word", fontsize=11)
    axes[0].grid(axis="x", linestyle="--", alpha=0.3)

    # Fake words
    sns.barplot(
        data=top_fake_df,
        y="word",
        x="count",
        color=COLOR_FAKE,
        ax=axes[1]
    )
    axes[1].set_title(f"Top {n_words} Most Common Words in Fake Ads", fontsize=13, fontweight="bold", color=COLOR_TEXT)
    axes[1].set_xlabel("Frequency Count", fontsize=11)
    axes[1].set_ylabel("Word", fontsize=11)
    axes[1].grid(axis="x", linestyle="--", alpha=0.3)

    plt.suptitle(f"Top {n_words} Most Frequent Words: Real vs Fake Postings (CountVectorizer)", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Top words plot -> {output_path}")


def plot_categorical_fraud_rates(df: pd.DataFrame, output_path: str | Path) -> None:
    """Plot percentage of fake ads across categorical columns:
    - has_company_logo
    - employment_type
    - required_experience

    Note: These columns are analyzed for EDA understanding only;
    they are NOT features in the model (model uses text only).
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=200)

    # 1. Company Logo
    logo_group = df.groupby("has_company_logo", dropna=False)["fraudulent"].agg(["count", "mean"]).reset_index()
    logo_group["fraud_pct"] = logo_group["mean"] * 100
    logo_group["label"] = logo_group["has_company_logo"].map({1: "Logo Present (1)", 0: "No Logo (0)"})

    sns.barplot(
        data=logo_group,
        x="label",
        y="fraud_pct",
        color=COLOR_PRIMARY,
        ax=axes[0]
    )
    axes[0].set_title("Fraud Rate by Company Logo Presence", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Company Logo", fontsize=11)
    axes[0].set_ylabel("Fraud Rate (%)", fontsize=11)
    axes[0].set_ylim(0, max(logo_group["fraud_pct"]) * 1.25)
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)
    for i, row in logo_group.iterrows():
        axes[0].text(
            i,
            row["fraud_pct"] + 0.5,
            f"{row['fraud_pct']:.1f}%\n(n={int(row['count']):,})",
            ha="center",
            va="bottom",
            fontsize=10
        )

    # 2. Employment Type
    emp_df = df.copy()
    emp_df["employment_type"] = emp_df["employment_type"].fillna("Unspecified")
    emp_group = emp_df.groupby("employment_type")["fraudulent"].agg(["count", "mean"]).reset_index()
    emp_group["fraud_pct"] = emp_group["mean"] * 100
    emp_group = emp_group.sort_values(by="fraud_pct", ascending=False)

    sns.barplot(
        data=emp_group,
        x="employment_type",
        y="fraud_pct",
        color=COLOR_PRIMARY,
        ax=axes[1]
    )
    axes[1].set_title("Fraud Rate by Employment Type", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Employment Type", fontsize=11)
    axes[1].set_ylabel("Fraud Rate (%)", fontsize=11)
    axes[1].set_ylim(0, max(emp_group["fraud_pct"]) * 1.25)
    axes[1].tick_params(axis="x", rotation=30)
    axes[1].grid(axis="y", linestyle="--", alpha=0.3)
    for i, row in emp_group.reset_index(drop=True).iterrows():
        axes[1].text(
            i,
            row["fraud_pct"] + 0.3,
            f"{row['fraud_pct']:.1f}%\n(n={int(row['count']):,})",
            ha="center",
            va="bottom",
            fontsize=9
        )

    # 3. Required Experience
    exp_df = df.copy()
    exp_df["required_experience"] = exp_df["required_experience"].fillna("Unspecified")
    exp_group = exp_df.groupby("required_experience")["fraudulent"].agg(["count", "mean"]).reset_index()
    exp_group["fraud_pct"] = exp_group["mean"] * 100
    exp_group = exp_group.sort_values(by="fraud_pct", ascending=False)

    sns.barplot(
        data=exp_group,
        x="required_experience",
        y="fraud_pct",
        color=COLOR_PRIMARY,
        ax=axes[2]
    )
    axes[2].set_title("Fraud Rate by Required Experience", fontsize=12, fontweight="bold")
    axes[2].set_xlabel("Experience Level", fontsize=11)
    axes[2].set_ylabel("Fraud Rate (%)", fontsize=11)
    axes[2].set_ylim(0, max(exp_group["fraud_pct"]) * 1.25)
    axes[2].tick_params(axis="x", rotation=40)
    axes[2].grid(axis="y", linestyle="--", alpha=0.3)
    for i, row in exp_group.reset_index(drop=True).iterrows():
        axes[2].text(
            i,
            row["fraud_pct"] + 0.3,
            f"{row['fraud_pct']:.1f}%\n(n={int(row['count']):,})",
            ha="center",
            va="bottom",
            fontsize=8.5
        )

    plt.suptitle("Fraud Rate Across Job Metadata (Understanding Only — Text Only Used for Model)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[Saved] Categorical fraud rates plot -> {output_path}")


def run_eda(
    dataset_path: str = "data/raw/fake_job_postings.csv",
    plots_dir: str = "app/static/img/plots"
) -> None:
    """Execute all EDA steps: print summaries and save all 4 plots.

    Args:
        dataset_path: Path to raw dataset CSV.
        plots_dir: Directory where generated plots are saved.
    """
    print(f"Loading dataset from: {dataset_path}")
    df = load_dataset(dataset_path)

    # 1. Print summary table
    print_dataset_overview(df)

    plots_path = Path(plots_dir)
    plots_path.mkdir(parents=True, exist_ok=True)

    # 2. Class balance plot
    plot_class_balance(df, plots_path / "eda_class_balance.png")

    # 3. Text length distribution plot
    plot_text_length_distribution(df, plots_path / "eda_text_length_distribution.png")

    # 4. Top 20 common words plot
    plot_top_words(df, plots_path / "eda_top_words.png", n_words=20)

    # 5. Metadata fraud rate comparison plot
    plot_categorical_fraud_rates(df, plots_path / "eda_categorical_fraud_rates.png")

    print("\nEDA completed successfully! All plots saved to:", plots_path.resolve())


if __name__ == "__main__":
    run_eda()
