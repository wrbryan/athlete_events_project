from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Input, Output

from components.layout import (
    demographics_container,
    explorer_container,
    has_columns,
    medals_container,
    overview_container,
)


def empty_figure(title: str):
    fig = px.scatter(title=title)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(annotations=[])
    return fig


def register_callbacks(app, df: pd.DataFrame) -> None:
    @app.callback(
        Output("analysis-view-container", "children"),
        Input("analysis-tabs", "value"),
    )
    def render_tab(tab_value: str):
        tab_to_container = {
            "overview": overview_container,
            "demographics": demographics_container,
            "medals": medals_container,
            "explorer": explorer_container,
        }
        selected_container = tab_to_container.get(tab_value, overview_container)
        return selected_container(df)

    @app.callback(
        Output("overview-events-by-year", "figure"),
        Output("overview-top-sports", "figure"),
        Input("analysis-tabs", "value"),
    )
    def update_overview(_: str):
        if has_columns(df, ["Year"]):
            yearly = (
                df.groupby("Year")
                .size()
                .reset_index(name="Entries")
                .sort_values("Year")
            )
            fig_year = px.line(
                yearly,
                x="Year",
                y="Entries",
                title="Olympic Entries by Year",
            )
        else:
            fig_year = empty_figure("Year column not found")

        if has_columns(df, ["Sport"]):
            sports = df["Sport"].astype(str).value_counts().head(15).reset_index(name="Entries")
            sports.columns = ["Sport", "Entries"]
            fig_sport = px.bar(sports, x="Sport", y="Entries", title="Top Sports")
            fig_sport.update_layout(xaxis_tickangle=-35)
        else:
            fig_sport = empty_figure("Sport column not found")

        return fig_year, fig_sport

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

    @app.callback(
        Output("medals-by-country", "figure"),
        Output("medals-by-year", "figure"),
        Input("medals-year-range", "value"),
        Input("medals-medal-type", "value"),
        Input("medals-season", "value"),
        Input("medals-top-n", "value"),
    )
    def update_medals(
        year_range: list[int],
        medal_type: str,
        season_value: str,
        top_n: int,
    ):
        if not has_columns(df, ["Medal", "NOC", "Year"]):
            return (
                empty_figure("Required medal columns not found"),
                empty_figure("Required medal columns not found"),
            )

        medal_df = df[df["Medal"].notna()].copy()
        medal_df = medal_df[
            (medal_df["Year"] >= year_range[0]) & (medal_df["Year"] <= year_range[1])
        ]
        if medal_type != "ALL":
            medal_df = medal_df[medal_df["Medal"] == medal_type]
        if season_value != "ALL" and "Season" in medal_df.columns:
            medal_df = medal_df[medal_df["Season"] == season_value]

        if medal_df.empty:
            return (
                empty_figure("No medals in selected year range"),
                empty_figure("No medals in selected year range"),
            )

        country_counts = medal_df["NOC"].value_counts().head(top_n).reset_index()
        country_counts.columns = ["NOC", "Medals"]
        country_fig = px.bar(
            country_counts,
            x="NOC",
            y="Medals",
            title=f"Top {top_n} Countries by Medals",
        )

        year_medals = medal_df.groupby(["Year", "Medal"]).size().reset_index(name="Count")
        year_fig = px.bar(
            year_medals,
            x="Year",
            y="Count",
            color="Medal",
            title="Medals by Year and Type",
        )

        return country_fig, year_fig

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
        selected_color = color_col if color_col else None

        if chart_type == "histogram":
            return px.histogram(
                df,
                x=x_col,
                color=selected_color,
                title=f"Histogram of {x_col}",
            )

        if chart_type == "bar":
            value_counts = (
                df[x_col]
                .astype(str)
                .value_counts(dropna=False)
                .reset_index()
                .rename(columns={"index": x_col, x_col: "count"})
                .head(30)
            )
            return px.bar(
                value_counts,
                x=x_col,
                y="count",
                title=f"Top Values for {x_col}",
            )

        if chart_type == "scatter":
            if y_col is None:
                return empty_figure("Select a Y column for scatter plots")
            return px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=selected_color,
                title=f"{y_col} vs {x_col}",
            )

        if y_col is None:
            return empty_figure("Select a Y column for box plots")

        return px.box(
            df,
            x=x_col,
            y=y_col,
            color=selected_color,
            title=f"Box Plot: {y_col} by {x_col}",
        )
