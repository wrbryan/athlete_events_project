from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Input, Output

from components.callback_common import empty_figure

SCATTER_MAX_POINTS = 10000
BOX_MAX_CATEGORIES = 20


def register_explorer_callbacks(app, df: pd.DataFrame) -> None:
    @app.callback(
        Output("explorer-main-chart", "figure"),
        Input("explorer-chart-type", "value"),
        Input("explorer-x-column", "value"),
        Input("explorer-y-column", "value"),
        Input("explorer-color-column", "value"),
    )
    def update_explorer(
        chart_type: str,
        x_col: str,
        y_col: str | None,
        color_col: str,
    ):
        if x_col not in df.columns:
            return empty_figure("Selected X column is not available")

        selected_color = color_col if color_col else None

        if chart_type == "histogram":
            if df[x_col].dropna().empty:
                return empty_figure("Selected X column has no values")
            return px.histogram(
                df,
                x=x_col,
                color=selected_color,
                title=f"Histogram of {x_col}",
            )

        if chart_type == "bar":
            counts = (
                df[x_col]
                .astype(str)
                .fillna("<NA>")
                .to_frame(name="category")
                .groupby("category", dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
                .head(30)
            )
            return px.bar(
                counts,
                x="category",
                y="count",
                title=f"Top Values for {x_col}",
                labels={"category": x_col, "count": "Count"},
            )

        if chart_type == "scatter":
            if y_col is None:
                return empty_figure("Select a Y column for scatter plots")
            if y_col not in df.columns:
                return empty_figure("Selected Y column is not available")
            if not pd.api.types.is_numeric_dtype(df[y_col]):
                return empty_figure("Y column must be numeric for scatter plots")

            scatter_df = df[[x_col, y_col] + ([selected_color] if selected_color else [])].copy()
            scatter_df = scatter_df.dropna(subset=[x_col, y_col])
            if scatter_df.empty:
                return empty_figure("No valid points for selected scatter columns")
            if len(scatter_df) > SCATTER_MAX_POINTS:
                scatter_df = scatter_df.sample(n=SCATTER_MAX_POINTS, random_state=42)

            return px.scatter(
                scatter_df,
                x=x_col,
                y=y_col,
                color=selected_color,
                title=f"{y_col} vs {x_col}",
            )

        if y_col is None:
            return empty_figure("Select a Y column for box plots")
        if y_col not in df.columns:
            return empty_figure("Selected Y column is not available")
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            return empty_figure("Y column must be numeric for box plots")

        box_df = df[[x_col, y_col] + ([selected_color] if selected_color else [])].copy()
        box_df = box_df.dropna(subset=[x_col, y_col])
        if box_df.empty:
            return empty_figure("No valid rows for selected box columns")

        x_as_str = box_df[x_col].astype(str)
        top_categories = x_as_str.value_counts().head(BOX_MAX_CATEGORIES).index
        box_df["_x_bucket"] = x_as_str.where(x_as_str.isin(top_categories), "Other")

        return px.box(
            box_df,
            x="_x_bucket",
            y=y_col,
            color=selected_color,
            title=f"Box Plot: {y_col} by {x_col}",
            labels={"_x_bucket": x_col},
        )
