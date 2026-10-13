import pandas as pd
import pytest

from src.activity_calendar_analyzer.standardize import standardize_posts


def test_standardize_date_time_columns():
    raw = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "time": ["08:30", "17:45"],
            "platform": ["twitter", "instagram"],
            "format": ["image", "video"],
            "likes": [10, "5"],
            "comments": [2, 1],
            "shares": [1, 0],
            "reach": [100, 200],
        }
    )

    df = standardize_posts(raw)

    assert "post_datetime" in df.columns
    assert df["post_datetime"].notna().all()
    assert df.loc[0, "hour"] == 8
    assert df.loc[1, "hour"] == 17
    assert df.loc[0, "platform"] == "twitter"
    assert df.loc[1, "format"] == "video"


def test_standardize_datetime_column():
    raw = pd.DataFrame(
        {
            "posted_at": ["2026-01-01T01:02:03", "2026-01-01T05:00:00"],
            "platform": ["x", "x"],
            "likes": [3, 4],
            "comments": [0, 1],
            "shares": [0, 0],
            "reach": [10, 10],
        }
    )

    df = standardize_posts(raw)
    assert df["post_datetime"].notna().all()
    assert df.loc[0, "hour"] == 1
    assert df.loc[1, "hour"] == 5


def test_reach_invalid_results_in_missing_engagement():
    raw = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "time": ["08:30"],
            "platform": ["twitter"],
            "format": ["image"],
            "likes": [10],
            "comments": [2],
            "shares": [1],
            "reach": [0],
        }
    )

    df = standardize_posts(raw)
    assert pd.isna(df.loc[0, "reach"])
