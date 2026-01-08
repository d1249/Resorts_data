from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import yaml
import json

from src.cache import DiskCache
from src.compute.aggregate import monthly_mean_from_daily
from src.compute.quality import apply_coverage_flags
from src.models import Location, Params
from src.report.export_csv import export_csv
from src.report.export_md import export_md
from src.score.comfort import compute_score
from src.sources.air_rain_meteostat import fetch_air_rain_daily
from src.sources.sea_sst_erddap import fetch_sea_surface_temperature
from src.sources.wind_wave_openmeteo import OpenMeteoWindWave


def load_locations(path: Path) -> list[Location]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Location.from_dict(item) for item in data.get("locations", [])]


def load_params(path: Path) -> Params:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Params(score=data["score"], thresholds=data["thresholds"])


def load_sources(path: Path) -> Dict[str, Dict[str, object]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_monthly_table(
    location: Location,
    sources_cfg: Dict[str, Dict[str, object]],
    params: Params,
    cache_dir: Path,
    outputs_dir: Path,
    refresh: bool = False,
    export_md: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, object], Path]:
    period = sources_cfg["period"]
    start_date = date(int(period["start_year"]), 1, 1)
    end_date = date(int(period["end_year"]), 12, 31)
    min_coverage = float(sources_cfg["coverage"]["min_coverage"])

    cache = DiskCache(cache_dir, ttl_days=int(sources_cfg["cache"]["ttl_days"]))

    air_df, air_meta = fetch_air_rain_daily(location, start_date, end_date, cache, refresh)
    sea_df, sea_meta = fetch_sea_surface_temperature(location, start_date, end_date, cache, refresh)
    wind_wave_df, wind_meta = OpenMeteoWindWave().fetch(location, start_date, end_date, cache, refresh)

    air_mean, air_cov = monthly_mean_from_daily(air_df, "tmax_c", min_coverage)
    rain_indicator = air_df.copy()
    rain_indicator["rain_day"] = (rain_indicator["prcp_mm"] >= 1.0).astype(float)
    rain_mean, rain_cov = monthly_mean_from_daily(rain_indicator, "rain_day", min_coverage)
    rain_days = rain_mean * _average_days_per_month(start_date.year, end_date.year)

    sea_mean, sea_cov = monthly_mean_from_daily(sea_df, "sst_c", min_coverage)
    wind_mean, wind_cov = monthly_mean_from_daily(wind_wave_df, "wind_ms", min_coverage)
    wave_mean, wave_cov = monthly_mean_from_daily(wind_wave_df, "wave_hs_m", min_coverage)

    air = apply_coverage_flags(air_mean, air_cov)
    rain = apply_coverage_flags(rain_days, rain_cov)
    sea = apply_coverage_flags(sea_mean, sea_cov)
    wind = apply_coverage_flags(wind_mean, wind_cov)
    wave = apply_coverage_flags(wave_mean, wave_cov)

    months = pd.Index(range(1, 13), name="Month")
    df = pd.DataFrame(index=months)
    df["AirTempC_avgHigh"] = air["value"]
    df["SeaTempC"] = sea["value"]
    df["RainDays_ge1mm"] = rain["value"]
    df["Wind_ms_10m"] = wind["value"]
    df["WaveHeightHs_m"] = wave["value"]

    df["flag_air"] = air["flag"]
    df["flag_sea"] = sea["flag"]
    df["flag_rain"] = rain["flag"]
    df["flag_wind"] = wind["flag"]
    df["flag_wave"] = wave["flag"]

    scores = []
    components_rows = []
    for month, row in df.iterrows():
        score, components = compute_score(
            row["AirTempC_avgHigh"],
            row["SeaTempC"],
            row["RainDays_ge1mm"],
            row["Wind_ms_10m"],
            row["WaveHeightHs_m"],
            {"score": params.score, "thresholds": params.thresholds},
        )
        scores.append(score)
        components_rows.append(components)

    components_df = pd.DataFrame(components_rows, index=months)
    df = pd.concat([df, components_df], axis=1)

    rounding = float(params.score.get("rounding", 0.1))
    df["ComfortScore"] = (pd.Series(scores, index=months) / rounding).round() * rounding

    df = df.reset_index()
    df.insert(0, "Area", location.area)
    df.insert(0, "Resort", location.resort)
    df.insert(0, "Country", location.country)

    df["sources_summary"] = ", ".join(
        [air_meta["source"], sea_meta["source"], wind_meta["source"]]
    )

    csv_path = outputs_dir / f"{location.location_id}_monthly.csv"
    export_csv(df, csv_path)
    if export_md:
        export_md_path = outputs_dir / f"{location.location_id}_monthly.md"
        export_md(df, export_md_path)

    provenance = {
        "location_id": location.location_id,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "sources": {
            "air_rain": air_meta,
            "sea": sea_meta,
            "wind_wave": wind_meta,
        },
        "coordinates": {
            "air": {"lat": location.lat, "lon": location.lon},
            "wave": {"lat": location.wave_point.lat, "lon": location.wave_point.lon, "mode": location.wave_point.mode},
        },
        "coverage": {
            "air": air_cov.to_dict(),
            "rain": rain_cov.to_dict(),
            "sea": sea_cov.to_dict(),
            "wind": wind_cov.to_dict(),
            "wave": wave_cov.to_dict(),
        },
    }
    prov_path = outputs_dir / f"{location.location_id}_provenance.json"
    prov_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")

    return df, provenance, csv_path


def _average_days_per_month(start_year: int, end_year: int) -> pd.Series:
    days = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            days.append({"year": year, "month": month, "days": pd.Period(f"{year}-{month}").days_in_month})
    days_df = pd.DataFrame(days)
    avg_days = days_df.groupby("month")["days"].mean()
    return avg_days
