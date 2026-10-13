from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from .calendar_view import plot_month_posts_heatmap


def _hourly_day_heatmap(df: pd.DataFrame, platform: str | None = None) -> go.Figure:
    if platform is not None:
        d = df[df["platform"] == platform]
    else:
        d = df

    counts = (
        d.groupby(["day_of_week", "hour"], as_index=False)
        .size()
        .rename(columns={"size": "posts"})
    )

    z = [[0 for _ in range(24)] for _ in range(7)]
    for _, r in counts.iterrows():
        z[int(r["day_of_week"])][int(r["hour"])] = int(r["posts"])

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=list(range(24)),
            y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            colorscale="Viridis",
            colorbar_title="Posts",
        )
    )

    fig.update_layout(
        title=f"Posts by day/hour" + (f" ({platform})" if platform else " (All platforms)"),
        xaxis_title="Hour of day",
        yaxis_title="Day of week",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig


def _weighted_engagement_by_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Compute weighted engagement = sum(likes+comments+shares) / sum(reach)."""

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
    agg["weighted_engagement_rate"] = (agg["likes_sum"] + agg["comments_sum"] + agg["shares_sum"]) / agg[
        "reach_sum"
    ]
    return agg[[group_col, "weighted_engagement_rate"]].sort_values("weighted_engagement_rate", ascending=False)


def render_dashboard_html(df: pd.DataFrame, output_path: str, title: str | None = None) -> None:
    """Render an interactive Plotly dashboard as a single HTML file."""

    if df.empty:
        raise ValueError("No data to visualize")

    output_file = Path(output_path)
    dashboard_title = title or "Social Media Activity Calendar Analyzer"

    fig_overall = _hourly_day_heatmap(df)

    platforms = sorted(df["platform"].unique().tolist())
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    heatmaps = []
    for p in platforms:
        counts = (
            df[df["platform"] == p]
            .groupby(["day_of_week", "hour"], as_index=False)
            .size()
            .rename(columns={"size": "posts"})
        )
        z = [[0 for _ in range(24)] for _ in range(7)]
        for _, r in counts.iterrows():
            z[int(r["day_of_week"])][int(r["hour"])] = int(r["posts"])

        heatmaps.append(
            go.Heatmap(z=z, x=list(range(24)), y=day_labels, colorscale="Viridis", name=p)
        )

    fig_platform = go.Figure(data=heatmaps)
    visibility = [False] * len(platforms)
    if platforms:
        visibility[0] = True
    for i, vis in enumerate(visibility):
        fig_platform.data[i].visible = vis

    buttons = []
    for i, p in enumerate(platforms):
        vis = [False] * len(platforms)
        vis[i] = True
        buttons.append({"label": p, "method": "update", "args": [{"visible": vis}]})

    fig_platform.update_layout(
        title="Posts by day/hour (platform selector)",
        xaxis_title="Hour of day",
        yaxis_title="Day of week",
        updatemenus=[{"buttons": buttons, "direction": "down", "showactive": True}],
        margin=dict(l=40, r=20, t=60, b=40),
    )

    # Pick the month with the most posts for the calendar view.
    df_tmp = df.copy()
    df_tmp["year"] = df_tmp["post_datetime"].dt.year
    df_tmp["month"] = df_tmp["post_datetime"].dt.month
    month_counts = df_tmp.groupby(["year", "month"]).size().reset_index(name="posts")
    top_row = month_counts.sort_values("posts", ascending=False).iloc[0]
    year = int(top_row["year"])
    month = int(top_row["month"])
    fig_month = plot_month_posts_heatmap(df, year=year, month=month)

    by_platform_posts = df.groupby("platform", as_index=False).size().rename(columns={"size": "posts"})
    fig_platform_dist = go.Figure(
        data=go.Bar(x=by_platform_posts["platform"], y=by_platform_posts["posts"], marker_color="#4c78a8")
    )
    fig_platform_dist.update_layout(
        title="Posts by platform",
        xaxis_title="Platform",
        yaxis_title="Posts",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    by_format_posts = df.groupby("format", as_index=False).size().rename(columns={"size": "posts"})
    fig_format_dist = go.Figure(
        data=go.Bar(x=by_format_posts["format"], y=by_format_posts["posts"], marker_color="#54a24b")
    )
    fig_format_dist.update_layout(
        title="Posts by format",
        xaxis_title="Format",
        yaxis_title="Posts",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    # Engagement by format & platform.
    by_format_eng = _weighted_engagement_by_group(df, "format")
    if by_format_eng.empty:
        fig_engagement_format = go.Figure()
        fig_engagement_format.update_layout(title="Weighted engagement rate by format")
    else:
        fig_engagement_format = go.Figure(
            data=go.Bar(
                x=by_format_eng["format"],
                y=by_format_eng["weighted_engagement_rate"],
                marker_color="#f58518",
            )
        )
        fig_engagement_format.update_layout(
            title="Weighted engagement rate by format",
            xaxis_title="Format",
            yaxis_title="Engagement / Reach",
            margin=dict(l=40, r=20, t=60, b=40),
        )

    by_platform_eng = _weighted_engagement_by_group(df, "platform")
    if by_platform_eng.empty:
        fig_engagement_platform = go.Figure()
        fig_engagement_platform.update_layout(title="Weighted engagement rate by platform")
    else:
        fig_engagement_platform = go.Figure(
            data=go.Bar(
                x=by_platform_eng["platform"],
                y=by_platform_eng["weighted_engagement_rate"],
                marker_color="#e45756",
            )
        )
        fig_engagement_platform.update_layout(
            title="Weighted engagement rate by platform",
            xaxis_title="Platform",
            yaxis_title="Engagement / Reach",
            margin=dict(l=40, r=20, t=60, b=40),
        )

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>{dashboard_title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .section {{ margin-bottom: 40px; }}
    .section h2 {{ margin-bottom: 10px; }}
  </style>
</head>
<body>
  <h1>{dashboard_title}</h1>

  <div class=\"section\"> <h2>1) Posting activity (overall)</h2>
    {pio.to_html(fig_overall, include_plotlyjs='cdn', full_html=False)}
  </div>

  <div class=\"section\"> <h2>2) Posting activity (platform selector)</h2>
    {pio.to_html(fig_platform, include_plotlyjs='cdn', full_html=False)}
  </div>

  <div class=\"section\"> <h2>3) Posting activity calendar (month heatmap)</h2>
    {pio.to_html(fig_month, include_plotlyjs='cdn', full_html=False)}
  </div>

  <div class=\"section\"> <h2>4) Content mix (volume)</h2>
    {pio.to_html(fig_platform_dist, include_plotlyjs='cdn', full_html=False)}
    {pio.to_html(fig_format_dist, include_plotlyjs='cdn', full_html=False)}
  </div>

  <div class=\"section\"> <h2>5) Engagement rate (weighted)</h2>
    {pio.to_html(fig_engagement_platform, include_plotlyjs='cdn', full_html=False)}
    {pio.to_html(fig_engagement_format, include_plotlyjs='cdn', full_html=False)}
  </div>

</body>
</html>
"""

    output_file.write_text(html, encoding="utf-8")
