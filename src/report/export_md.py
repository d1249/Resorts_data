from __future__ import annotations

from pathlib import Path

import pandas as pd


DISPLAY_COLUMNS = [
    "Country",
    "Resort",
    "Area",
    "Month",
    "AirTempC",
    "SeaTempC",
    "RainDays",
    "Wind_ms",
    "WaveHs_m",
    "ComfortScore",
]


def export_md(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_columns = [column for column in DISPLAY_COLUMNS if column in df.columns]
    md = df[existing_columns].to_markdown(index=False)
    path.write_text(md, encoding="utf-8")
