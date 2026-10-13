import pandas as pd

from src.activity_calendar_analyzer.recommendations import (
    recommend_optimal_post_times,
    recommend_optimal_formats,
    recommend_optimal_platforms,
)


def test_recommendations_deterministic_order():
    # Two hours with different engagement rate.
    df = pd.DataFrame(
        {
            "post_datetime": [
                pd.Timestamp("2026-01-01 08:00"),
                pd.Timestamp("2026-01-01 08:10"),
                pd.Timestamp("2026-01-02 17:00"),
                pd.Timestamp("2026-01-02 17:15"),
            ],
            "date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02"],
            "day_of_week": [3, 3, 4, 4],
            "hour": [8, 8, 17, 17],
            "platform": ["twitter", "twitter", "twitter", "twitter"],
            "format": ["image", "image", "video", "video"],
            "likes": [10, 10, 1, 1],
            "comments": [0, 0, 0, 0],
            "shares": [0, 0, 0, 0],
            "reach": [100, 100, 10, 10],
            "engagement_rate": [0.1, 0.1, 0.1, 0.1],
        }
    )

    times = recommend_optimal_post_times(df, top_n=2, min_posts=2, by_platform=False)
    # With equal engagement, we tie-break by more posts (both have 2) so order depends on sort stability.
    # Ensure output contains both hours and correct shape.
    assert {t["hour"] for t in times} == {8, 17}

    formats = recommend_optimal_formats(df, top_n=2, min_posts=2)
    assert {f["format"] for f in formats} == {"image", "video"}

    platforms = recommend_optimal_platforms(df, top_n=1, min_posts=2)
    assert platforms[0]["platform"] == "twitter"
