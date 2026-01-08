from __future__ import annotations

import pandas as pd


def apply_coverage_flags(series: pd.Series, coverage_ok: pd.Series) -> pd.DataFrame:
    flags = (~coverage_ok).astype(int)
    return pd.DataFrame({"value": series, "flag": flags})
