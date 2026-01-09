from __future__ import annotations

import pandas as pd
import streamlit as st


def plot_scores(df: pd.DataFrame) -> None:
    chart_df = df.set_index("Month")["ComfortScore"]
    st.line_chart(chart_df)


def plot_metrics(df: pd.DataFrame) -> None:
    metrics = df.set_index("Month")[
        ["AirTempC_num", "SeaTempC_num", "RainDays_num", "Wind_ms_num", "WaveHs_m_num"]
    ]
    st.line_chart(metrics)


def plot_components(df: pd.DataFrame, month: int) -> None:
    row = df.loc[df["Month"] == month].iloc[0]
    comp = pd.Series(
        {
            "SeaBase": row["SeaBase"],
            "AirAdj": row["AirAdj"],
            "Breeze": row["Breeze"],
            "WarmForBreeze": row["WarmForBreeze"],
            "BreezeBonus": row["BreezeBonus"],
            "Cold": -row["Cold"],
            "WindExCold": -row["WindExCold"],
            "WetPen": -row["WetPen"],
            "RainPen": -row["RainPen"],
            "HeatPen": -row["HeatPen"],
            "BreathPen": -row["BreathPen"],
            "StrongWindPen": -row["StrongWindPen"],
            "WavePen": -row["WavePen"],
        }
    )
    st.bar_chart(comp)
