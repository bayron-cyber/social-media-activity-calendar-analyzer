"""Social Media Activity Calendar Analyzer package."""

__all__ = ["standardize_posts", "main"]

from .standardize import standardize_posts

# Keep package imports lightweight: CLI/plotly imports happen only when needed.
from .cli import main
