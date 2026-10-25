"""tests/test_eda.py
Unit tests for ml/eda.py (Exploratory Data Analysis).
"""

from pathlib import Path
import pandas as pd
import pytest

from ml.eda import (
    load_dataset,
    get_combined_text,
    plot_class_balance,
    plot_text_length_distribution,
    plot_top_words,
    plot_categorical_fraud_rates,
)


@pytest.fixture
def sample_df():
    """Create a minimal test DataFrame mimicking fake_job_postings.csv."""
    return pd.DataFrame({
        "job_id": [1, 2, 3, 4],
        "title": ["Real Software Engineer", "Fake Data Entry", "Real Marketing Lead", "Fake Assistant"],
        "company_profile": ["Tech firm", None, "Media corp", ""],
        "description": ["Build backend services with Python", "Earn quick cash now", "Lead digital campaigns", "Work from home easy"],
        "requirements": ["Degree in CS", "None", "5 years experience", "No experience"],
        "benefits": ["Health insurance", None, "Gym allowance", None],
        "telecommuting": [0, 1, 0, 1],
        "has_company_logo": [1, 0, 1, 0],
        "has_questions": [1, 0, 1, 0],
        "employment_type": ["Full-time", "Part-time", "Full-time", None],
        "required_experience": ["Mid-Senior level", "Entry level", "Executive", None],
        "required_education": ["Bachelor's", None, "Master's", None],
        "industry": ["Technology", "Administrative", "Marketing", None],
        "function": ["Engineering", "Administrative", "Marketing", None],
        "fraudulent": [0, 1, 0, 1]
    })


def test_load_dataset_success():
    """Verify load_dataset successfully loads the primary raw CSV."""
    csv_path = Path("data/raw/fake_job_postings.csv")
    if not csv_path.exists():
        pytest.skip("Raw dataset not found at data/raw/fake_job_postings.csv")

    df = load_dataset(csv_path)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 17880
    assert "fraudulent" in df.columns
    assert "description" in df.columns


def test_load_dataset_missing_file():
    """Verify load_dataset raises FileNotFoundError for nonexistent paths."""
    with pytest.raises(FileNotFoundError):
        load_dataset("data/raw/nonexistent_dataset.csv")


def test_get_combined_text(sample_df):
    """Verify get_combined_text joins title, company_profile, description, requirements, benefits."""
    combined = get_combined_text(sample_df)
    assert len(combined) == 4
    # First row check
    assert "Real Software Engineer" in combined.iloc[0]
    assert "Tech firm" in combined.iloc[0]
    assert "Build backend services with Python" in combined.iloc[0]
    # Check that None/NaN are replaced without throwing or outputting 'nan' string
    assert "None" not in combined.iloc[1] or "Data Entry" in combined.iloc[1]


def test_plot_generation(sample_df, tmp_path):
    """Verify that all 4 plot functions save valid image files without error."""
    # 1. Class balance
    p1 = tmp_path / "test_balance.png"
    plot_class_balance(sample_df, p1)
    assert p1.exists()
    assert p1.stat().st_size > 1000

    # 2. Text length distribution
    p2 = tmp_path / "test_lengths.png"
    plot_text_length_distribution(sample_df, p2)
    assert p2.exists()
    assert p2.stat().st_size > 1000

    # 3. Top words
    p3 = tmp_path / "test_words.png"
    plot_top_words(sample_df, p3, n_words=5)
    assert p3.exists()
    assert p3.stat().st_size > 1000

    # 4. Categorical fraud rates
    p4 = tmp_path / "test_categorical.png"
    plot_categorical_fraud_rates(sample_df, p4)
    assert p4.exists()
    assert p4.stat().st_size > 1000


def test_eda_artifacts_exist():
    """Verify that all 4 required EDA plot images exist in app/static/img/plots/."""
    plots_dir = Path("app/static/img/plots")
    required_plots = [
        "eda_class_balance.png",
        "eda_text_length_distribution.png",
        "eda_top_words.png",
        "eda_categorical_fraud_rates.png",
    ]
    for plot_name in required_plots:
        plot_file = plots_dir / plot_name
        assert plot_file.exists(), f"Missing required plot: {plot_name}"
        assert plot_file.stat().st_size > 0, f"Plot file is empty: {plot_name}"
