from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "Country",
    "Resort",
    "Area",
    "Month",
    "AirTempC",
    "SeaTempC",
    "RainDays",
    "Wind_ms",
    "WaveHs_m",
    "AirTempC_num",
    "SeaTempC_num",
    "RainDays_num",
    "Wind_ms_num",
    "WaveHs_m_num",
    "Score",
    "ComfortScore",
    "Score_raw",
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
    "mark_air",
    "mark_sea",
    "mark_rain",
    "mark_wind",
    "mark_wave",
    "sources_summary",
]


def export_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_df = df.copy()
    for column in REQUIRED_COLUMNS:
        if column not in ordered_df.columns:
            ordered_df[column] = ""
    optional_columns = [column for column in ordered_df.columns if column not in REQUIRED_COLUMNS]
    ordered_df = ordered_df[REQUIRED_COLUMNS + optional_columns]
    ordered_df.to_csv(path, index=False, sep=";", encoding="utf-8-sig", decimal=",")
