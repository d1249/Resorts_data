from __future__ import annotations

from calendar import monthrange
from typing import Tuple

import pandas as pd


def monthly_mean_from_daily(
    df: pd.DataFrame,
    value_col: str,
    min_coverage: float,
    start_year: int | None = None,
    end_year: int | None = None,
) -> Tuple[pd.Series, pd.Series]:
    df = df.copy()
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    grouped = df.groupby(["year", "month"])[value_col]
    monthly_mean = grouped.mean().rename(value_col).reset_index()

    if start_year is None:
        start_year = int(df["year"].min()) if not df.empty else None
    if end_year is None:
        end_year = int(df["year"].max()) if not df.empty else None

    coverage_rows = []
    if start_year is not None and end_year is not None:
        counts = grouped.count()
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                total_days = monthrange(year, month)[1]
                valid_days = float(counts.get((year, month), 0))
                coverage_rows.append(
                    {"year": year, "month": month, "coverage": valid_days / total_days}
                )
    else:
        for (year, month), values in grouped:
            total_days = monthrange(year, month)[1]
            valid_days = values.notna().sum()
            coverage_rows.append({"year": year, "month": month, "coverage": valid_days / total_days})
    coverage = pd.DataFrame(coverage_rows)

    month_stats = pd.DataFrame()
    if not monthly_mean.empty:
        month_stats[value_col] = monthly_mean.groupby("month")[value_col].mean()
    if not coverage.empty:
        month_stats["coverage"] = coverage.groupby("month")["coverage"].mean()
    if "coverage" not in month_stats:
        month_stats["coverage"] = pd.Series(dtype="float64")
    month_stats["coverage_ok"] = month_stats["coverage"] >= min_coverage

    months = pd.Index(range(1, 13), name="month")
    month_stats = month_stats.reindex(months)
    month_stats["coverage_ok"] = month_stats["coverage_ok"].fillna(False)
    return month_stats[value_col], month_stats["coverage_ok"]
