# Social Media Activity Calendar Analyzer

Analyze a CSV of social media posts to produce:
- An interactive posting activity dashboard (HTML)
- A Markdown report with posting gaps, overload days, and recommended posting times/formats/platforms

## What the input CSV should contain
At minimum, the CSV should include:
- **date** and **time** columns (recommended), or a single datetime column
- **platform** (e.g., twitter, instagram, tiktok)
- **format** (e.g., image, video, carousel)
- **likes**, **comments**, **shares**, **reach** (numeric; reach > 0 required for engagement)

### Option A (recommended): separate date/time columns
- `date`: `YYYY-MM-DD`
- `time`: `HH:MM` (24h)

Example:
```csv
date,time,platform,format,likes,comments,shares,reach
2026-01-01,08:30,twitter,image,10,2,1,100
```

### Option B: single datetime column
Use one of: `datetime`, `timestamp`, `posted_at`, `created_at`, `published_at`.

Example:
```csv
datetime,platform,format,likes,comments,shares,reach
2026-01-01T01:02:03,twitter,image,10,2,1,100
```

## Engagement rate definition
Engagement rate per post is:

\[ (likes + comments + shares) / reach \]

If `reach` is missing or `reach <= 0`, engagement rate is treated as **missing** (NaN).

## Overload and gap detection
- **Gaps**: days with **zero** posts within the inclusive observed date range.
- **Overloads**: uses an adaptive threshold:
  - `threshold = mean(posts_per_day) + k * std(posts_per_day)`

You can control `k` via `--overload-k`.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python -m src.main --input path/to/posts.csv --output-dir output
```

### Common options
- `--overload-k 1.0` (default): overload threshold parameter
- `--top-n 5` (default): number of recommendations to show
- `--min-samples 2` (default): minimum posts per group to consider
- `--start-date YYYY-MM-DD` / `--end-date YYYY-MM-DD`: filter the dataset

## Example dataset
A small sample dataset is included:
- `data/sample_posts.csv`

Run the demo:
```bash
python -m src.main --input data/sample_posts.csv --output-dir output
```

Outputs:
- `output/dashboard.html`
- `output/report.md`

## Project layout
- `src/activity_calendar_analyzer/`: core modules
- `tests/`: unit tests for parsing, metrics, and recommendations
- `output/`: generated files
- `data/`: sample input(s)

## Running unit tests
```bash
python -m pytest -q
```

## Demo (generated outputs)
The repository includes a small sample dataset in `data/sample_posts.csv`.
Running the demo will generate:
- `output/dashboard.html`
- `output/report.md`
Running tests will validate core parsing + analytics logic.
Converted by the analyzer using the engagement formula `(likes + comments + shares) / reach`.

Please open `output/dashboard.html` in your browser to view the interactive charts.
