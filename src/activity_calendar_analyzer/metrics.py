from __future__ import annotations

import numpy as np
import pandas as pd


def compute_engagement_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Compute engagement_rate = (likes+comments+shares)/reach.

    Adds a new column `engagement_rate`.
    - If reach is missing or <=0, engagement_rate is NaN.
    """

    out = df.copy()

    engagement = out["likes"] + out["comments"] + out["shares"]
    reach = out["reach"]

    mask = reach.notna() & (pd.to_numeric(reach, errors="coerce") > 0)
    out["engagement_rate"] = np.where(mask, engagement / reach, np.nan)
    return out


def _normalize_date_series(s: pd.Series) -> pd.Series:
    """Normalize arbitrary date values to Python `datetime.date`."""

    return pd.to_datetime(s, errors="coerce").dt.date


def compute_posts_per_day(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with columns: date (datetime.date), posts."""

    d = df.copy()
    d["date"] = _normalize_date_series(d["date"])

    # Drop rows with unparseable dates
    d = d.loc[d["date"].notna()].copy()

    ppd = d.groupby("date", as_index=False).size().rename(columns={"size": "posts"})
    return ppd.sort_values("date").reset_index(drop=True)


def detect_gaps(df: pd.DataFrame) -> dict:
    """Detect days with no posts across the inclusive observed date range."""

    if df.empty:
        return {"gap_days": [], "gap_streaks": [], "longest_gap_streak": 0}

    d = df.copy()
    d["date"] = _normalize_date_series(d["date"])
    d = d.loc[d["date"].notna()].copy()

    if d.empty:
        return {"gap_days": [], "gap_streaks": [], "longest_gap_streak": 0}

    start = pd.to_datetime(d["date"].min())
    end = pd.to_datetime(d["date"].max())
    all_days = pd.date_range(start, end, freq="D").date

    posts_by_day = compute_posts_per_day(d).set_index("date")["posts"].to_dict()

    gap_days = [day for day in all_days if posts_by_day.get(day, 0) == 0]

    gap_streaks: list[dict] = []
    if gap_days:
        streak_start = gap_days[0]
        prev = gap_days[0]
        for day in gap_days[1:]:
            if (pd.to_datetime(day) - pd.to_datetime(prev)).days == 1:
                prev = day
                continue

            length = (pd.to_datetime(prev) - pd.to_datetime(streak_start)).days + 1
            gap_streaks.append(
                {"start": str(streak_start), "end": str(prev), "length_days": length}
            )
            streak_start = day
            prev = day

        length = (pd.to_datetime(prev) - pd.to_datetime(streak_start)).days + 1
        gap_streaks.append(
            {"start": str(streak_start), "end": str(prev), "length_days": length}
        )

    longest = max((s["length_days"] for s in gap_streaks), default=0)

    return {
        "gap_days": [str(d) for d in gap_days],
        "gap_streaks": gap_streaks,
        "longest_gap_streak": int(longest),
    }


def detect_overloads(posts_per_day: pd.DataFrame, k: float = 1.0) -> dict:
    """Detect overloaded days using adaptive threshold.

    Overload threshold = mean(posts/day) + k * std(posts/day)
    """

    if posts_per_day.empty:
        return {"threshold": None, "overloaded_days": []}

    d = posts_per_day.copy()
    d["date"] = _normalize_date_series(d["date"])
    d = d.loc[d["date"].notna()].copy()

    values = d["posts"].astype(float).values

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=0))
    threshold = mean + k * std

    overloaded = d.loc[d["posts"] > threshold, "date"].tolist()

    return {
        "mean_posts_per_day": mean,
        "std_posts_per_day": std,
        "threshold": float(threshold),
        "overloaded_days": [str(d) for d in overloaded],
    }
