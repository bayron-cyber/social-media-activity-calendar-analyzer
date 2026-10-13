import argparse
from pathlib import Path

import pandas as pd

from .dashboard import render_dashboard_html
from .io import load_posts_csv
from .metrics import compute_engagement_rate, compute_posts_per_day, detect_gaps, detect_overloads
from .recommendations import (
    recommend_optimal_formats,
    recommend_optimal_post_times,
    recommend_optimal_platforms,
)
from .report import render_report_markdown
from .standardize import standardize_posts


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Social Media Activity Calendar Analyzer (CSV -> dashboard + report).")
    p.add_argument("--input", required=True, help="Path to input CSV of social posts")
    p.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (dashboard.html, report.md)",
    )
    p.add_argument(
        "--overload-k",
        type=float,
        default=1.0,
        help="Overload threshold: mean(posts/day) + k*std(posts/day)",
    )
    p.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Top N hours/formats/platforms to recommend",
    )
    p.add_argument(
        "--min-samples",
        type=int,
        default=2,
        help="Minimum posts per group to be considered in recommendations",
    )
    p.add_argument("--start-date", default=None, help="Optional filter start date (YYYY-MM-DD)")
    p.add_argument("--end-date", default=None, help="Optional filter end date (YYYY-MM-DD)")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_df = load_posts_csv(input_path)
    df = standardize_posts(raw_df)

    if args.start_date is not None:
        start = pd.to_datetime(args.start_date).date()
        df = df[df["date"] >= start]

    if args.end_date is not None:
        end = pd.to_datetime(args.end_date).date()
        df = df[df["date"] <= end]

    df = compute_engagement_rate(df)

    posts_per_day = compute_posts_per_day(df)
    gaps = detect_gaps(df)
    overloads = detect_overloads(posts_per_day, k=args.overload_k)

    rec_times = recommend_optimal_post_times(df, top_n=args.top_n, min_posts=args.min_samples, by_platform=True)
    rec_formats = recommend_optimal_formats(df, top_n=args.top_n, min_posts=args.min_samples)
    rec_platforms = recommend_optimal_platforms(df, top_n=args.top_n, min_posts=args.min_samples)

    analysis = {
        "date_range": {"start": str(df["date"].min()), "end": str(df["date"].max())},
        "summary": {
            "total_posts": int(len(df)),
            "total_reach_known": int(df["reach"].notna().sum()),
            "avg_engagement_rate": float(df["engagement_rate"].mean(skipna=True))
            if df["engagement_rate"].notna().any()
            else None,
        },
        "gaps": gaps,
        "overloads": overloads,
        "recommendations": {"times": rec_times, "formats": rec_formats, "platforms": rec_platforms},
    }

    render_dashboard_html(df, output_dir / "dashboard.html")
    report_md = render_report_markdown(df, posts_per_day, analysis)
    (output_dir / "report.md").write_text(report_md, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
