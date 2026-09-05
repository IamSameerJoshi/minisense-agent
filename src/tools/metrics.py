import polars as pl
from pathlib import Path
from typing import Optional, List, Dict
from src.schemas import DataAgentResult, ThemeFrequency

# Default path to our synthetic dataset
DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "survey_data.json"

def load_survey_dataframe(path: Optional[Path] = None) -> pl.DataFrame:
    target_path = path or DATA_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Survey data not found at {target_path}")
    
    # Polars reads nested JSON quickly
    raw_df = pl.read_json(str(target_path))
    # Explode the list of survey objects into rows
    df = raw_df.select(pl.col("responses")).explode("responses").unnest("responses")
    # Cast date string to actual Date type for filtering
    df = df.with_columns(pl.col("date").str.to_date("%Y-%m-%d"))
    return df

def compute_survey_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    business_id: Optional[str] = None,
    df: Optional[pl.DataFrame] = None
) -> DataAgentResult:
    """
    Deterministic tool that filters surveys and calculates exact CSAT,
    average rating, distribution, and complaint/praise themes.
    """
    if df is None:
        df = load_survey_dataframe()

    # Apply date filters if provided
    if start_date:
        df = df.filter(pl.col("date") >= pl.lit(start_date).str.to_date("%Y-%m-%d"))
    if end_date:
        df = df.filter(pl.col("date") <= pl.lit(end_date).str.to_date("%Y-%m-%d"))
    if business_id:
        df = df.filter(pl.col("business_id") == business_id)

    total_responses = df.height
    if total_responses == 0:
        return DataAgentResult(
            total_responses=0,
            csat_score=0.0,
            average_rating=0.0,
            rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            top_themes=[]
        )

    # CSAT formula: Average rating on 1-5 scale (or % of 4 & 5 stars)
    # GreenLeaf FAQ specifies a target on 1-5 scale (e.g., target 4.5+ out of 5)
    avg_rating = round(float(df.select(pl.col("rating").mean()).item()), 2)
    
    # Also calculate percentage of satisfied responses (ratings 4 and 5)
    satisfied_count = df.filter(pl.col("rating") >= 4).height
    csat_percentage = round((satisfied_count / total_responses) * 100, 2)

    # Compute rating distribution (count of 1s, 2s, 3s, 4s, 5s)
    dist_df = df.group_by("rating").len().sort("rating")
    dist_map = {int(row["rating"]): int(row["len"]) for row in dist_df.iter_rows(named=True)}
    for r in range(1, 6):
        dist_map.setdefault(r, 0)

    # Extract themes deterministically based on key phrase occurrences
    text_corpus = df.select("free_text").to_series()
    
    wait_count = text_corpus.filter(text_corpus.str.contains("(?i)wait|delay|minute")).len()
    food_quality_count = text_corpus.filter(text_corpus.str.contains("(?i)avocado|bowl|fresh|cold")).len()
    cleanliness_count = text_corpus.filter(text_corpus.str.contains("(?i)clean|bussing")).len()

    top_themes = [
        ThemeFrequency(theme="Wait Time / Delays", count=wait_count, sentiment="negative"),
        ThemeFrequency(theme="Food & Drink Quality", count=food_quality_count, sentiment="positive"),
        ThemeFrequency(theme="Cleanliness & Ambience", count=cleanliness_count, sentiment="neutral"),
    ]

    return DataAgentResult(
        total_responses=total_responses,
        csat_score=avg_rating,  # Represents the 1.0 - 5.0 score cited in the FAQ
        average_rating=avg_rating,
        rating_distribution=dist_map,
        top_themes=top_themes
    )