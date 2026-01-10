from __future__ import annotations

import pandas as pd
import streamlit as st

METRIC_OPTIONS = {
    "Air": "AirTempC_num",
    "Sea": "SeaTempC_num",
    "Rain": "RainDays_num",
    "Wind": "Wind_ms_num",
    "Wave": "WaveHs_m_num",
}

COMPONENT_COLUMNS = [
    "SeaBase",
    "AirAdj",
    "Breeze",
    "WarmForBreeze",
    "BreezeBonus",
    "Cold",
    "WindExCold",
    "WetPen",
    "RainPen",
    "HeatPen",
    "BreathPen",
    "StrongWindPen",
    "WavePen",
]


def plot_scores(df: pd.DataFrame) -> None:
    chart_df = df.set_index("Month")["ComfortScore"]
    st.line_chart(chart_df)


def plot_metric(df: pd.DataFrame, metric_key: str) -> None:
    metric_col = METRIC_OPTIONS[metric_key]
    chart_df = df.set_index("Month")[metric_col]
    st.line_chart(chart_df)


def _components_frame(df: pd.DataFrame) -> pd.DataFrame:
    comp = df[["Month", *COMPONENT_COLUMNS]].copy()
    for col in [
        "Cold",
        "WindExCold",
        "WetPen",
        "RainPen",
        "HeatPen",
        "BreathPen",
        "StrongWindPen",
        "WavePen",
    ]:
        comp[col] = -comp[col]
    return comp.set_index("Month")


def plot_components_overview(df: pd.DataFrame) -> None:
    st.bar_chart(_components_frame(df))


def plot_components_month(df: pd.DataFrame, month: int) -> None:
    comp = _components_frame(df).loc[month]
    st.bar_chart(comp)
