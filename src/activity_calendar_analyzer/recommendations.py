from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _weighted_engagement_rate(group: pd.DataFrame) -> float | None:
    """Compute (sum(likes+comments+shares)/sum(reach)) for reach>0."""

    g = group.copy()
    mask = g["reach"].notna() & (pd.to_numeric(g["reach"], errors="coerce") > 0)
    g = g.loc[mask]
    if len(g) == 0:
        return None

    total_engagement = float((g["likes"] + g["comments"] + g["shares"]).sum())
    total_reach = float(g["reach"].sum())
    if total_reach <= 0:
        return None
    return total_engagement / total_reach


def recommend_optimal_post_times(
    df: pd.DataFrame,
    top_n: int = 5,
    min_posts: int = 3,
    by_platform: bool = True,
) -> list[dict[str, Any]]:
    """Recommend optimal hour-of-day slots based on weighted engagement rate."""

    if by_platform:
        platforms = sorted(df["platform"].unique().tolist())
        results: list[dict[str, Any]] = []
        for platform in platforms:
            dpf = df[df["platform"] == platform]
            results.extend(
                _recommend_hours_for_subset(
                    dpf,
                    platform=platform,
                    top_n=top_n,
                    min_posts=min_posts,
                )
            )
        return results

    return _recommend_hours_for_subset(df, platform=None, top_n=top_n, min_posts=min_posts)


def _recommend_hours_for_subset(
    df: pd.DataFrame,
    platform: str | None,
    top_n: int,
    min_posts: int,
) -> list[dict[str, Any]]:
    grouped = df.groupby("hour")
    rows: list[dict[str, Any]] = []

    for hour, g in grouped:
        n_posts = len(g)
        if n_posts < min_posts:
            continue

        wr = _weighted_engagement_rate(g)
        if wr is None:
            continue

        rows.append(
            {
                "platform": platform,
                "hour": int(hour),
                "weighted_engagement_rate": float(wr),
                "posts": int(n_posts),
            }
        )

    # Sort: higher engagement first, then more posts
    rows.sort(key=lambda r: (r["weighted_engagement_rate"], r["posts"]), reverse=True)
    return rows[:top_n]


def recommend_optimal_formats(
    df: pd.DataFrame,
    top_n: int = 5,
    min_posts: int = 3,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for fmt, g in df.groupby("format"):
        n_posts = len(g)
        if n_posts < min_posts:
            continue
        wr = _weighted_engagement_rate(g)
        if wr is None:
            continue
        results.append(
            {
                "format": str(fmt),
                "weighted_engagement_rate": float(wr),
                "posts": int(n_posts),
            }
        )

    results.sort(key=lambda r: (r["weighted_engagement_rate"], r["posts"]), reverse=True)
    return results[:top_n]


def recommend_optimal_platforms(
    df: pd.DataFrame,
    top_n: int = 5,
    min_posts: int = 3,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for platform, g in df.groupby("platform"):
        n_posts = len(g)
        if n_posts < min_posts:
            continue
        wr = _weighted_engagement_rate(g)
        if wr is None:
            continue
        results.append(
            {
                "platform": str(platform),
                "weighted_engagement_rate": float(wr),
                "posts": int(n_posts),
            }
        )

    results.sort(key=lambda r: (r["weighted_engagement_rate"], r["posts"]), reverse=True)
    return results[:top_n]
