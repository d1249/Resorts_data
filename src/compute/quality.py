from __future__ import annotations

import pandas as pd


def apply_coverage_flags(
    series: pd.Series,
    coverage_ok: pd.Series,
    estimated: pd.Series | None = None,
) -> pd.DataFrame:
    months = pd.Index(range(1, 13), name="month")
    aligned_series = series.reindex(months)
    aligned_coverage = coverage_ok.reindex(months).fillna(False)
    flags = (~aligned_coverage) | aligned_series.isna()
    if estimated is not None:
        aligned_estimated = estimated.reindex(months).fillna(False)
        flags = flags | aligned_estimated
    return pd.DataFrame({"value": aligned_series, "flag": flags.astype(int)})
