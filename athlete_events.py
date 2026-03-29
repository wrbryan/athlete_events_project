from __future__ import annotations

import argparse
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash

from components.callbacks import register_callbacks
from components.layout import build_layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the athlete events dashboard with modular components."
    )
    parser.add_argument(
        "--csv",
        default="athlete_events.csv",
        help="Path to the CSV file to load. Defaults to athlete_events.csv",
    )
    parser.add_argument(
        "--title",
        default="Athlete Events Dashboard",
        help="Dashboard title shown in the app header.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port for the Dash app. Defaults to 8050.",
    )
    return parser.parse_args()


def load_csv(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists() or not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Coerce numeric-like object columns while preserving text-heavy columns.
    for col in df.columns:
        if df[col].dtype == "object":
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() >= int(0.9 * max(len(df), 1)):
                df[col] = converted

    return df


def build_app(df: pd.DataFrame, title: str, csv_path: str) -> Dash:
    assets_dir = Path(__file__).resolve().parent / "assets"
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        assets_folder=str(assets_dir),
    )
    app.config.suppress_callback_exceptions = True

    # Layout comes from components folder.
    app.layout = build_layout(df, title, csv_path)
    # Callback registration comes from components folder.
    register_callbacks(app, df)

    return app


def main() -> None:
    args = parse_args()
    df = load_csv(args.csv)
    app = build_app(df, args.title, args.csv)
    app.run(debug=True, port=args.port)


if __name__ == "__main__":
    main()
