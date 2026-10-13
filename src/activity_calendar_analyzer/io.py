from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_posts_csv(path: str | Path) -> pd.DataFrame:
    """Load a posts CSV into a DataFrame.

    Notes:
    - We load everything as text where possible, then coerce numeric fields in
      `standardize_posts`.
    - This keeps parsing robust across messy exports.
    """

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    # Keep empty strings as NaN; let `standardize_posts` decide coercion.
    df = pd.read_csv(p, na_values=["", "NA", "NaN", "null", "NULL"], keep_default_na=True)
    if df.empty:
        raise ValueError("Input CSV is empty")
    return df
