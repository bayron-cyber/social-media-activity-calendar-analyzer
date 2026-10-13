import pandas as pd

from src.activity_calendar_analyzer.metrics import (
    compute_posts_per_day,
    detect_gaps,
    detect_overloads,
    compute_engagement_rate,
)


def test_compute_posts_per_day_and_gaps():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-03"],
            "platform": ["a", "a", "a"],
            "format": ["x", "x", "x"],
            "post_datetime": [
                pd.Timestamp("2026-01-01 08:00"),
                pd.Timestamp("2026-01-01 12:00"),
                pd.Timestamp("2026-01-03 09:00"),
            ],
            "hour": [8, 12, 9],
            "day_of_week": [3, 3, 5],
            "likes": [1, 2, 3],
            "comments": [0, 0, 0],
            "shares": [0, 0, 0],
            "reach": [10, 10, 10],
        }
    )

    posts_per_day = compute_posts_per_day(df)
    d1 = pd.to_datetime("2026-01-01").date()
    d3 = pd.to_datetime("2026-01-03").date()

    assert posts_per_day.loc[posts_per_day["date"] == d1, "posts"].iloc[0] == 2
    assert posts_per_day.loc[posts_per_day["date"] == d3, "posts"].iloc[0] == 1

    gaps = detect_gaps(df)
    assert "2026-01-02" in gaps["gap_days"]
    assert gaps["longest_gap_streak"] == 1


def test_compute_engagement_rate():
    df = pd.DataFrame(
        {
            "likes": [10, 5],
            "comments": [0, 2],
            "shares": [0, 1],
            "reach": [20, None],
        }
    )

    out = compute_engagement_rate(df)
    assert out.loc[0, "engagement_rate"] == (10 + 0 + 0) / 20
    assert pd.isna(out.loc[1, "engagement_rate"])


def test_detect_overloads_adaptive_mean_std():
    posts_per_day = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "posts": [1, 1, 5],
        }
    )

    res = detect_overloads(posts_per_day, k=1.0)
    assert res["overloaded_days"] == ["2026-01-03"]
    assert res["threshold"] > 0
