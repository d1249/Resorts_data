from __future__ import annotations

from calendar import monthrange
from typing import Tuple

import pandas as pd


def monthly_mean_from_daily(
    df: pd.DataFrame,
    value_col: str,
    min_coverage: float,
) -> Tuple[pd.Series, pd.Series]:
    df = df.copy()
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    grouped = df.groupby(["year", "month"])[value_col]
    monthly_mean = grouped.mean().reset_index()

    coverage_rows = []
    for (year, month), values in grouped:
        total_days = monthrange(year, month)[1]
        valid_days = values.notna().sum()
        coverage_rows.append({"year": year, "month": month, "coverage": valid_days / total_days})
    coverage = pd.DataFrame(coverage_rows)

    merged = monthly_mean.merge(coverage, on=["year", "month"])
    month_stats = merged.groupby("month").agg({value_col: "mean", "coverage": "mean"})
    month_stats["coverage_ok"] = month_stats["coverage"] >= min_coverage

    months = pd.Index(range(1, 13), name="month")
    month_stats = month_stats.reindex(months)
    month_stats["coverage_ok"] = month_stats["coverage_ok"].fillna(False)
    return month_stats[value_col], month_stats["coverage_ok"]
