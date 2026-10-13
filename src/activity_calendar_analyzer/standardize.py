from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StandardizeResult:
    df: pd.DataFrame
    warnings: list[str]


def _normalize_colnames(df: pd.DataFrame) -> dict[str, str]:
    """Return mapping from normalized -> original column name."""

    mapping: dict[str, str] = {}
    for c in df.columns:
        nc = str(c).strip().lower()
        mapping[nc] = c
    return mapping


def _pick_first(mapping: dict[str, str], candidates: list[str]) -> str | None:
    for cand in candidates:
        if cand in mapping:
            return mapping[cand]
    return None


def _clean_str_series(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .replace({"nan": None, "None": None})
        .fillna("")
        .map(lambda x: x.strip())
    )


def standardize_posts(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Parse and standardize a social posts dataset.

    Expected inputs (flexible column names):
    - date+time OR a single datetime-like column
    - platform and format strings
    - numeric: likes, comments, shares, reach (or impressions/views)

    Returns a DataFrame with at least:
    - post_datetime (datetime64[ns], timezone-naive)
    - date (datetime.date)
    - day_of_week (0=Mon..6=Sun)
    - hour (0..23)
    - platform, format
    - likes, comments, shares, reach
    """

    warnings: list[str] = []
    df = raw_df.copy()
    colmap = _normalize_colnames(df)

    # Datetime parsing
    date_col = _pick_first(colmap, ["date", "day", "posted_date"])
    time_col = _pick_first(colmap, ["time", "posted_time", "hour"])
    datetime_col = _pick_first(
        colmap,
        [
            "datetime",
            "timestamp",
            "posted_at",
            "post_datetime",
            "created_at",
            "published_at",
            "postedat",
            "createdat",
            "publishedat",
        ],
    )

    if date_col is not None and time_col is not None:
        combined = df[date_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip()
        post_dt = pd.to_datetime(combined, errors="coerce")
    elif datetime_col is not None:
        post_dt = pd.to_datetime(df[datetime_col], errors="coerce")
    else:
        raise ValueError(
            "Could not find datetime columns. Expected date+time or a datetime-like column."
        )

    if post_dt.isna().all():
        raise ValueError("Failed to parse any post datetimes from the provided CSV")

    parse_rate = float(post_dt.notna().mean())
    if parse_rate < 0.5:
        warnings.append(
            f"Low datetime parse success rate ({parse_rate:.0%}). Check your date/time formats."
        )

    df["post_datetime"] = post_dt

    # Drop unparseable rows
    df = df.loc[df["post_datetime"].notna()].copy()

    df["hour"] = df["post_datetime"].dt.hour.astype(int)
    df["day_of_week"] = df["post_datetime"].dt.dayofweek.astype(int)  # 0=Mon
    df["date"] = df["post_datetime"].dt.date

    # Platform
    platform_col = _pick_first(colmap, ["platform", "channel", "network", "source"])
    if platform_col is None:
        df["platform"] = "unknown"
        warnings.append("No platform column found; using 'unknown'.")
    else:
        df["platform"] = _clean_str_series(df[platform_col]).replace({"": "unknown"}).map(str.lower)

    # Format
    format_col = _pick_first(colmap, ["format", "content_format", "type", "post_type", "post_format"])
    if format_col is None:
        df["format"] = "unspecified"
        warnings.append("No format column found; using 'unspecified'.")
    else:
        df["format"] = _clean_str_series(df[format_col]).replace({"": "unspecified"}).map(str.lower)

    def coerce_numeric(col: str) -> pd.Series:
        if col not in df.columns:
            raise KeyError(col)
        return pd.to_numeric(df[col], errors="coerce")

    likes_col = _pick_first(colmap, ["likes", "like_count", "like", "favorites"])
    comments_col = _pick_first(colmap, ["comments", "comment_count", "comment"])
    shares_col = _pick_first(colmap, ["shares", "share_count", "share", "reposts", "retweets"])
    reach_col = _pick_first(colmap, ["reach", "impressions", "views", "audience_reach"])

    df["likes"] = coerce_numeric(likes_col) if likes_col is not None else 0
    df["comments"] = coerce_numeric(comments_col) if comments_col is not None else 0
    df["shares"] = coerce_numeric(shares_col) if shares_col is not None else 0

    df["likes"] = df["likes"].fillna(0).clip(lower=0)
    df["comments"] = df["comments"].fillna(0).clip(lower=0)
    df["shares"] = df["shares"].fillna(0).clip(lower=0)

    if reach_col is not None:
        reach = coerce_numeric(reach_col)
        reach = reach.where(reach > 0)  # <=0 treated as missing
        df["reach"] = reach
    else:
        df["reach"] = pd.NA
        warnings.append("No reach/impressions/views column found; engagement rate will be mostly missing.")

    df = df[
        [
            "post_datetime",
            "date",
            "day_of_week",
            "hour",
            "platform",
            "format",
            "likes",
            "comments",
            "shares",
            "reach",
        ]
    ].reset_index(drop=True)

    df.attrs["standardize_warnings"] = warnings
    return df
