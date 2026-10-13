from __future__ import annotations

from typing import Any

import pandas as pd


def _weighted_engagement_by_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Weighted engagement rate = sum(likes+comments+shares) / sum(reach) for reach>0."""

    d = df.copy()
    d = d[d["reach"].notna()].copy()
    d["reach"] = pd.to_numeric(d["reach"], errors="coerce")
    d = d.loc[d["reach"] > 0]

    if d.empty:
        return pd.DataFrame(columns=[group_col, "weighted_engagement_rate"])

    agg = d.groupby(group_col, as_index=False).agg(
        likes_sum=("likes", "sum"),
        comments_sum=("comments", "sum"),
        shares_sum=("shares", "sum"),
        reach_sum=("reach", "sum"),
    )

    agg["weighted_engagement_rate"] = (
        agg["likes_sum"] + agg["comments_sum"] + agg["shares_sum"]
    ) / agg["reach_sum"]

    return agg[[group_col, "weighted_engagement_rate"]].sort_values(
        "weighted_engagement_rate", ascending=False
    )


def render_report_markdown(
    df: pd.DataFrame,
    posts_per_day: pd.DataFrame,
    analysis: dict[str, Any],
) -> str:
    """Create a Markdown report summarizing insights and recommendations."""

    gaps = analysis["gaps"]
    overloads = analysis["overloads"]
    rec = analysis["recommendations"]

    # Content mix (volume)
    top_platforms_by_volume = df.groupby("platform").size().sort_values(ascending=False).head(5)
    top_formats_by_volume = df.groupby("format").size().sort_values(ascending=False).head(5)

    # Engagement by group (weighted by reach)
    eng_by_platform = _weighted_engagement_by_group(df, "platform").head(5)
    eng_by_format = _weighted_engagement_by_group(df, "format").head(5)

    lines: list[str] = []
    lines.append("# Social Media Activity Calendar Analyzer Report\n")

    dr = analysis["date_range"]
    lines.append(f"**Date range:** {dr['start']} → {dr['end']}\n")
    lines.append(f"**Total posts:** {analysis['summary']['total_posts']}\n")

    avg_er = analysis["summary"]["avg_engagement_rate"]
    if avg_er is None:
        lines.append("**Average engagement rate:** (insufficient reach data)\n")
    else:
        lines.append(f"**Average engagement rate:** {avg_er:.6f}\n")

    lines.append("---\n")

    # Content mix
    lines.append("## Content mix (volume)\n")
    lines.append("**Top platforms (by post count):**\n")
    for platform, n in top_platforms_by_volume.items():
        lines.append(f"- {platform}: {int(n)}\n")

    lines.append("\n**Top formats (by post count):**\n")
    for fmt, n in top_formats_by_volume.items():
        lines.append(f"- {fmt}: {int(n)}\n")

    lines.append("---\n")

    # Engagement
    lines.append("## Engagement rate (weighted)\n")
    if eng_by_platform.empty and eng_by_format.empty:
        lines.append("- Not enough reach data to compute engagement rate.\n")
    else:
        if not eng_by_platform.empty:
            lines.append("**Top platforms (by weighted engagement):**\n")
            for _, r in eng_by_platform.iterrows():
                lines.append(f"- {r['platform']}: {r['weighted_engagement_rate']:.6f}\n")

        if not eng_by_format.empty:
            lines.append("\n**Top formats (by weighted engagement):**\n")
            for _, r in eng_by_format.iterrows():
                lines.append(f"- {r['format']}: {r['weighted_engagement_rate']:.6f}\n")

    lines.append("---\n")

    # Gaps
    lines.append("## Posting gaps\n")
    gap_days = gaps["gap_days"]
    lines.append(f"- Gap days (no posts): **{len(gap_days)}**\n")
    lines.append(f"- Longest gap streak: **{gaps['longest_gap_streak']} days**\n")
    if gap_days:
        preview = ", ".join(gap_days[:10])
        more = "" if len(gap_days) <= 10 else f" (+{len(gap_days) - 10} more)"
        lines.append(f"- Example gap dates: {preview}{more}\n")

    lines.append("---\n")

    # Overloads
    lines.append("## Posting overloads\n")
    thr = overloads["threshold"]
    if thr is None:
        lines.append("- Threshold: N/A\n")
        lines.append("- Overloaded days: 0\n")
    else:
        lines.append(f"- Threshold (mean + k*std): **{thr:.3f} posts/day**\n")
        lines.append(f"- Overloaded days: **{len(overloads['overloaded_days'])}**\n")
        if overloads["overloaded_days"]:
            preview = ", ".join(overloads["overloaded_days"][:10])
            more = "" if len(overloads["overloaded_days"]) <= 10 else f" (+{len(overloads['overloaded_days']) - 10} more)"
            lines.append(f"- Example overloaded dates: {preview}{more}\n")

    lines.append("---\n")

    # Recommendations
    lines.append("## Recommendations\n")

    lines.append("### Optimal posting times (hour-of-day)\n")
    times = rec["times"]
    if not times:
        lines.append("- No recommendations available (insufficient engagement data / samples).\n")
    else:
        by_p: dict[str, list[dict]] = {}
        for t in times:
            key = t.get("platform") or "overall"
            by_p.setdefault(key, []).append(t)

        for platform, items in sorted(by_p.items()):
            lines.append(f"**{platform}**\n")
            for it in items:
                lines.append(
                    f"- {it['hour']:02d}:00 — engagement/rec. reach = {it['weighted_engagement_rate']:.6f} (posts={it['posts']})\n"
                )
            lines.append("\n")

    lines.append("### Optimal content formats\n")
    formats = rec["formats"]
    if not formats:
        lines.append("- No format recommendations available.\n")
    else:
        for f in formats:
            lines.append(
                f"- {f['format']} — engagement/rec. reach = {f['weighted_engagement_rate']:.6f} (posts={f['posts']})\n"
            )

    lines.append("\n### Optimal platforms\n")
    platforms = rec["platforms"]
    if not platforms:
        lines.append("- No platform recommendations available.\n")
    else:
        for p in platforms:
            lines.append(
                f"- {p['platform']} — engagement/rec. reach = {p['weighted_engagement_rate']:.6f} (posts={p['posts']})\n"
            )

    lines.append("---\n")

    # Notes
    lines.append("## Notes\n")
    lines.append(
        "- Engagement rate uses **(likes + comments + shares) / reach**.\n"
        "- Overload detection flags days above **mean + k·std** of posts/day.\n"
        "- Recommendations apply a minimum sample-size guard and prefer groups with higher engagement rate and more posts.\n"
    )

    return "".join(lines)
