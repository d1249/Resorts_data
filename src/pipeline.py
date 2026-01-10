from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Tuple, Optional, Callable, Iterable, List

import pandas as pd
import yaml
import json

from src.cache import DiskCache
from src.compute.aggregate import monthly_mean_from_daily
from src.compute.quality import apply_coverage_flags
from src.models import Location, Params
from src.formatting import format_with_flag
from src.report.export_csv import export_csv
from src.report.export_md import export_md
from src.score.comfort import compute_score
from src.sources.air_rain_meteostat import fetch_air_rain_daily
from src.sources.sea_sst_erddap import fetch_sea_surface_temperature
from src.sources.wind_wave_openmeteo import OpenMeteoWindWave
from src.sources.wind_wave_era5 import Era5WindWave
from src.sources.utils import format_error


AIR_RAIN_PROVIDERS: Dict[str, Callable[..., Tuple[pd.DataFrame, Dict[str, object]]]] = {
    "open_meteo_archive": fetch_air_rain_daily,
}
SEA_PROVIDERS: Dict[str, Callable[..., Tuple[pd.DataFrame, Dict[str, object]]]] = {
    "open_meteo_marine": fetch_sea_surface_temperature,
}
WIND_WAVE_PROVIDERS: Dict[str, Callable[[], OpenMeteoWindWave]] = {
    "open_meteo": OpenMeteoWindWave,
    "era5": Era5WindWave,
}


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
) -> Tuple[pd.DataFrame, Dict[str, object], Path, Optional[Path]]:
    period = sources_cfg["period"]
    start_date = date(int(period["start_year"]), 1, 1)
    end_date = date(int(period["end_year"]), 12, 31)
    min_coverage = float(sources_cfg["coverage"]["min_coverage"])
    fallbacks = sources_cfg.get("fallbacks", {})
    allow_estimated_rain_days = bool(fallbacks.get("allow_estimated_rain_days", False))
    allow_last_resort = bool(fallbacks.get("allow_last_resort", False))
    mm_per_rain_day_proxy = float(fallbacks.get("mm_per_rain_day_proxy", 5.0))

    cache = DiskCache(cache_dir, ttl_days=int(sources_cfg["cache"]["ttl_days"]))

    air_df, air_meta = _fetch_with_fallbacks(
        "air_rain",
        sources_cfg["sources"]["air_rain"]["primary"],
        sources_cfg["sources"]["air_rain"].get("fallbacks", []),
        location,
        start_date,
        end_date,
        cache,
        refresh,
    )
    sea_df, sea_meta = _fetch_with_fallbacks(
        "sea_temp",
        sources_cfg["sources"]["sea_temp"]["primary"],
        sources_cfg["sources"]["sea_temp"].get("fallbacks", []),
        location,
        start_date,
        end_date,
        cache,
        refresh,
    )
    wind_wave_df, wind_meta = _fetch_with_fallbacks(
        "wind_wave",
        sources_cfg["sources"]["wind_wave"]["primary"],
        sources_cfg["sources"]["wind_wave"].get("fallbacks", []),
        location,
        start_date,
        end_date,
        cache,
        refresh,
    )

    air_mean, air_cov = monthly_mean_from_daily(
        air_df,
        "tmax_c",
        min_coverage,
        start_year=start_date.year,
        end_year=end_date.year,
    )
    rain_days, rain_cov, rain_estimated = _build_rain_days(
        air_df,
        start_date.year,
        end_date.year,
        min_coverage,
        allow_estimated_rain_days,
        mm_per_rain_day_proxy,
    )

    sea_mean, sea_cov = monthly_mean_from_daily(
        sea_df,
        "sst_c",
        min_coverage,
        start_year=start_date.year,
        end_year=end_date.year,
    )
    wind_mean, wind_cov = monthly_mean_from_daily(
        wind_wave_df,
        "wind_ms",
        min_coverage,
        start_year=start_date.year,
        end_year=end_date.year,
    )
    wave_mean, wave_cov = monthly_mean_from_daily(
        wind_wave_df,
        "wave_hs_m",
        min_coverage,
        start_year=start_date.year,
        end_year=end_date.year,
    )

    air_meta["coverage"] = air_cov.to_dict()
    sea_meta["coverage"] = sea_cov.to_dict()
    wind_meta["coverage"] = {"wind": wind_cov.to_dict(), "wave": wave_cov.to_dict()}
    if "components" in wind_meta:
        wind_meta["components"]["wind"]["coverage"] = wind_cov.to_dict()
        wind_meta["components"]["wave"]["coverage"] = wave_cov.to_dict()

    air = apply_coverage_flags(air_mean, air_cov)
    rain = apply_coverage_flags(rain_days, rain_cov, estimated=rain_estimated)
    sea = apply_coverage_flags(sea_mean, sea_cov)
    wind = apply_coverage_flags(wind_mean, wind_cov)
    wave = apply_coverage_flags(wave_mean, wave_cov)

    months = pd.Index(range(1, 13), name="Month")
    df = pd.DataFrame(index=months)
    df["AirTempC_num"] = air["value"]
    df["SeaTempC_num"] = sea["value"]
    df["RainDays_num"] = rain["value"]
    df["Wind_ms_num"] = wind["value"]
    df["WaveHs_m_num"] = wave["value"]

    df["mark_air"] = air["flag"]
    df["mark_sea"] = sea["flag"]
    df["mark_rain"] = rain["flag"]
    df["mark_wind"] = wind["flag"]
    df["mark_wave"] = wave["flag"]

    scores = []
    components_rows = []
    for month, row in df.iterrows():
        score, components = compute_score(
            row["AirTempC_num"],
            row["SeaTempC_num"],
            row["RainDays_num"],
            row["Wind_ms_num"],
            row["WaveHs_m_num"],
            {"score": params.score, "thresholds": params.thresholds},
        )
        scores.append(score)
        components_rows.append(components)

    components_df = pd.DataFrame(components_rows, index=months)
    df = pd.concat([df, components_df], axis=1)

    score_series = pd.Series(scores, index=months)
    rounding = float(params.score.get("rounding", 0.1))
    df["Score"] = score_series
    df["ComfortScore"] = (score_series / rounding).round() * rounding

    df = df.reset_index()
    df.insert(0, "Area", location.area)
    df.insert(0, "Resort", location.resort)
    df.insert(0, "Country", location.country)

    wind_source = wind_meta["components"]["wind"]["source"]
    wave_source = wind_meta["components"]["wave"]["source"]
    df["sources_summary"] = ", ".join(
        [air_meta["source"], sea_meta["source"], wind_source, wave_source]
    )
    df["air_source"] = air_meta["source"]
    df["sea_source"] = sea_meta["source"]
    df["wind_source"] = wind_source
    df["wave_source"] = wave_source

    df["AirTempC"] = [
        format_with_flag(val, flag) for val, flag in zip(df["AirTempC_num"], df["mark_air"])
    ]
    df["SeaTempC"] = [
        format_with_flag(val, flag) for val, flag in zip(df["SeaTempC_num"], df["mark_sea"])
    ]
    df["RainDays"] = [
        format_with_flag(val, flag, decimals=0)
        for val, flag in zip(df["RainDays_num"], df["mark_rain"])
    ]
    df["Wind_ms"] = [
        format_with_flag(val, flag) for val, flag in zip(df["Wind_ms_num"], df["mark_wind"])
    ]
    df["WaveHs_m"] = [
        format_with_flag(val, flag) for val, flag in zip(df["WaveHs_m_num"], df["mark_wave"])
    ]

    if not allow_last_resort:
        missing = df[
            [
                "AirTempC_num",
                "SeaTempC_num",
                "RainDays_num",
                "Wind_ms_num",
                "WaveHs_m_num",
            ]
        ].isna()
        if missing.any().any():
            raise ValueError("Missing monthly data; last-resort estimates are disabled.")

    period_label = f"{start_date.year}-{end_date.year}"
    csv_path = outputs_dir / f"{location.location_id}_{period_label}_monthly.csv"
    export_csv(df, csv_path)
    md_path: Optional[Path] = None
    if export_md:
        md_path = outputs_dir / f"{location.location_id}_{period_label}_monthly.md"
        export_md(df, md_path)

    marks_detail = _build_marks_detail(df, rain_estimated, min_coverage)
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
        "marks": marks_detail,
    }
    prov_path = outputs_dir / f"{location.location_id}_{period_label}_provenance.json"
    prov_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")

    return df, provenance, csv_path, md_path


def _average_days_per_month(start_year: int, end_year: int) -> pd.Series:
    days = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            days.append({"year": year, "month": month, "days": pd.Period(f"{year}-{month}").days_in_month})
    days_df = pd.DataFrame(days)
    avg_days = days_df.groupby("month")["days"].mean()
    return avg_days


def _build_rain_days(
    air_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    min_coverage: float,
    allow_estimated: bool,
    mm_per_rain_day_proxy: float,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    months = pd.Index(range(1, 13), name="month")
    rain_indicator = air_df.copy()
    rain_indicator["rain_day"] = (rain_indicator["prcp_mm"] >= 1.0).astype(float)
    rain_mean, rain_cov = monthly_mean_from_daily(
        rain_indicator,
        "rain_day",
        min_coverage,
        start_year=start_year,
        end_year=end_year,
    )
    rain_days = rain_mean * _average_days_per_month(start_year, end_year)
    rain_days = rain_days.reindex(months)
    rain_cov = rain_cov.reindex(months)
    estimated = pd.Series(False, index=months)

    if allow_estimated and rain_days.isna().any():
        totals = air_df.copy()
        totals["month"] = totals["date"].dt.month
        totals["year"] = totals["date"].dt.year
        monthly_total = totals.groupby(["year", "month"])["prcp_mm"].sum().reset_index()
        avg_total = monthly_total.groupby("month")["prcp_mm"].mean().reindex(months)
        estimated_values = avg_total / mm_per_rain_day_proxy
        needs_estimate = rain_days.isna() & estimated_values.notna()
        rain_days = rain_days.where(~needs_estimate, estimated_values)
        rain_cov = rain_cov.where(~needs_estimate, False)
        estimated = estimated | needs_estimate

    return rain_days, rain_cov, estimated


def _fetch_with_fallbacks(
    source_kind: str,
    primary: str,
    fallbacks: Iterable[str],
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    registry = _provider_registry(source_kind)
    errors: List[Tuple[str, BaseException]] = []
    for provider_name in [primary, *list(fallbacks)]:
        if provider_name not in registry:
            raise ValueError(f"Unknown provider '{provider_name}' for {source_kind}.")
        try:
            provider = registry[provider_name]
            if source_kind == "wind_wave":
                df, meta = provider().fetch(location, start_date, end_date, cache, refresh)
            else:
                df, meta = provider(location, start_date, end_date, cache, refresh)
        except Exception as exc:  # noqa: BLE001
            errors.append((provider_name, exc))
            continue
        if errors:
            meta = _annotate_fallback_meta(meta, errors, provider_name)
        return df, meta
    raise errors[-1][1]


def _provider_registry(source_kind: str) -> Dict[str, Callable[..., object]]:
    if source_kind == "air_rain":
        return AIR_RAIN_PROVIDERS
    if source_kind == "sea_temp":
        return SEA_PROVIDERS
    if source_kind == "wind_wave":
        return WIND_WAVE_PROVIDERS
    raise ValueError(f"Unknown source kind '{source_kind}'.")


def _annotate_fallback_meta(
    meta: Dict[str, object],
    errors: List[Tuple[str, BaseException]],
    provider_name: str,
) -> Dict[str, object]:
    meta = dict(meta)
    meta["fallback_used"] = True
    meta["fallback_provider"] = provider_name
    meta["fallbacks_tried"] = [
        {"source": name, "error": format_error(error)} for name, error in errors
    ]
    if meta.get("error") is None and errors:
        meta["error"] = format_error(errors[-1][1])
    return meta


def _build_marks_detail(
    df: pd.DataFrame,
    rain_estimated: pd.Series,
    min_coverage: float,
) -> Dict[str, object]:
    marks = {}
    for month, row in df.iterrows():
        month_marks = []
        if row["mark_air"]:
            month_marks.append({"metric": "AirTempC", "reason": f"coverage_below_{min_coverage}"})
        if row["mark_sea"]:
            month_marks.append({"metric": "SeaTempC", "reason": f"coverage_below_{min_coverage}"})
        if row["mark_rain"]:
            reason = f"coverage_below_{min_coverage}"
            if rain_estimated.loc[month]:
                reason = "estimated_from_total"
            month_marks.append({"metric": "RainDays", "reason": reason})
        if row["mark_wind"]:
            month_marks.append({"metric": "Wind_ms", "reason": f"coverage_below_{min_coverage}"})
        if row["mark_wave"]:
            month_marks.append({"metric": "WaveHs_m", "reason": f"coverage_below_{min_coverage}"})
        marks[str(month)] = month_marks
    return marks
