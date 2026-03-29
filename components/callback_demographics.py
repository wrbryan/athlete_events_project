from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Input, Output

from components.callback_common import empty_figure
from components.layout import has_columns


def register_demographics_callbacks(app, df: pd.DataFrame) -> None:
    @app.callback(
        Output("demographics-age-distribution", "figure"),
        Output("demographics-height-weight", "figure"),
        Input("demographics-sex", "value"),
        Input("demographics-season", "value"),
    )
    def update_demographics(sex_value: str, season_value: str):
        filtered = df.copy()
        if sex_value != "ALL" and "Sex" in filtered.columns:
            filtered = filtered[filtered["Sex"] == sex_value]
        if season_value != "ALL" and "Season" in filtered.columns:
            filtered = filtered[filtered["Season"] == season_value]

        if "Age" in filtered.columns:
            age_series = filtered["Age"].dropna()
            if age_series.empty:
                age_fig = empty_figure("No Age data for selected filters")
            else:
                age_fig = px.histogram(
                    filtered,
                    x="Age",
                    nbins=30,
                    title="Age Distribution",
                )
        else:
            age_fig = empty_figure("Age column not found")

        if has_columns(filtered, ["Height", "Weight"]):
            hw = filtered[["Height", "Weight"]].dropna()
            if hw.empty:
                hw_fig = empty_figure("No Height/Weight data for selected filters")
            else:
                scatter_color = "Sex" if "Sex" in filtered.columns else None
                hw_fig = px.scatter(
                    filtered,
                    x="Height",
                    y="Weight",
                    color=scatter_color,
                    title="Height vs Weight",
                )
        else:
            hw_fig = empty_figure("Height and Weight columns not found")

        return age_fig, hw_fig
