from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_md(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    md = df.to_markdown(index=False)
    path.write_text(md, encoding="utf-8")
