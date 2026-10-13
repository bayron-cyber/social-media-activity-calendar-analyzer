from __future__ import annotations

from calendar import monthrange

import pandas as pd
import plotly.graph_objects as go


def build_month_posts_matrix(df: pd.DataFrame, year: int, month: int) -> list[list[int]]:
    """Build a 6x7 matrix (weeks x weekdays) of posts counts.

    Weekday order is Monday-first.
    """

    # Filter to month
    mask = (df["post_datetime"].dt.year == year) & (df["post_datetime"].dt.month == month)
    dmf = df.loc[mask]

    days_in_month = monthrange(year, month)[1]

    # First day weekday: 0=Mon..6=Sun
    first_day = pd.Timestamp(year=year, month=month, day=1)
    first_weekday = int(first_day.dayofweek)

    weeks = 6  # enough for any month
    matrix = [[0 for _ in range(7)] for _ in range(weeks)]

    for day in range(1, days_in_month + 1):
        date = pd.Timestamp(year=year, month=month, day=day).date()
        count = int((dmf["date"] == date).sum())

        idx = first_weekday + (day - 1)
        w = idx // 7
        wd = idx % 7
        if w < weeks:
            matrix[w][wd] = count

    return matrix


def plot_month_posts_heatmap(df: pd.DataFrame, year: int, month: int) -> go.Figure:
    """Render month posting heatmap as a Plotly figure."""

    matrix = build_month_posts_matrix(df, year, month)

    weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    z = matrix

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=weekday_labels,
            y=["Wk1", "Wk2", "Wk3", "Wk4", "Wk5", "Wk6"],
            colorscale="Blues",
            showscale=True,
        )
    )

    fig.update_layout(
        title=f"Posting activity calendar heatmap: {year}-{month:02d}",
        xaxis_title="Weekday",
        yaxis_title="Week",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig
