from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

import pandas as pd
import requests

from src.cache import DiskCache
from src.models import Location
from src.sources.utils import build_cache_key, build_source_meta
from src.sources.wind_wave_provider import WindWaveProvider


class OpenMeteoWindWave(WindWaveProvider):
    def fetch(
        self,
        location: Location,
        start_date: date,
        end_date: date,
        cache: DiskCache,
        refresh: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, object]]:
        wind_df, wind_meta = _fetch_wind(location, start_date, end_date, cache, refresh)
        wave_df, wave_meta = _fetch_wave(location, start_date, end_date, cache, refresh)
        merged = pd.merge(wind_df, wave_df, on="date", how="outer")
        fallback_used = bool(wind_meta.get("fallback_used") or wave_meta.get("fallback_used"))
        cache_fallback = bool(wind_meta.get("cache_fallback") or wave_meta.get("cache_fallback"))
        errors = [err for err in (wind_meta.get("error"), wave_meta.get("error")) if err]
        combined_meta = {
            "source": "open_meteo",
            "version": "v1",
            "period": wind_meta.get("period"),
            "requested_period": wind_meta.get("requested_period"),
            "actual_period": wind_meta.get("actual_period"),
            "coordinates": {
                "wind": wind_meta.get("coordinates"),
                "wave": wave_meta.get("coordinates"),
            },
            "coverage": None,
            "cached": bool(wind_meta.get("cached") and wave_meta.get("cached")),
            "fallback_used": fallback_used,
            "cache_fallback": cache_fallback,
            "error": errors or None,
            "components": {"wind": wind_meta, "wave": wave_meta},
        }
        return merged, combined_meta


def _fetch_wind(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    source_name = "open_meteo_archive"
    source_version = "v1"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "wind_speed_10m_mean",
        "timezone": "UTC",
    }
    cache_key = build_cache_key(
        source_name,
        source_version,
        location.location_id,
        location.lat,
        location.lon,
        start_date,
        end_date,
        params["daily"],
    )
    cached = cache.get("wind", cache_key)
    if cached and not refresh:
        return _to_wind_dataframe(cached), build_source_meta(
            source_name,
            source_version,
            start_date,
            end_date,
            {"lat": location.lat, "lon": location.lon},
            cached=True,
            cache_fallback=False,
        )

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        if cached:
            return _to_wind_dataframe(cached), build_source_meta(
                source_name,
                source_version,
                start_date,
                end_date,
                {"lat": location.lat, "lon": location.lon},
                cached=True,
                cache_fallback=True,
                error=exc,
            )
        raise

    cache.set("wind", cache_key, data)
    return _to_wind_dataframe(data), build_source_meta(
        source_name,
        source_version,
        start_date,
        end_date,
        {"lat": location.lat, "lon": location.lon},
        cached=False,
        cache_fallback=False,
    )


def _fetch_wave(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    endpoint = "https://marine-api.open-meteo.com/v1/marine"
    source_name = "open_meteo_marine"
    source_version = "v1"
    params = {
        "latitude": location.wave_point.lat,
        "longitude": location.wave_point.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "wave_height_mean",
        "timezone": "UTC",
    }
    cache_key = build_cache_key(
        source_name,
        source_version,
        location.location_id,
        location.wave_point.lat,
        location.wave_point.lon,
        start_date,
        end_date,
        params["daily"],
    )
    cached = cache.get("wave", cache_key)
    if cached and not refresh:
        return _to_wave_dataframe(cached), build_source_meta(
            source_name,
            source_version,
            start_date,
            end_date,
            {"lat": location.wave_point.lat, "lon": location.wave_point.lon},
            cached=True,
            cache_fallback=False,
        )

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        if cached:
            return _to_wave_dataframe(cached), build_source_meta(
                source_name,
                source_version,
                start_date,
                end_date,
                {"lat": location.wave_point.lat, "lon": location.wave_point.lon},
                cached=True,
                cache_fallback=True,
                error=exc,
            )
        raise

    cache.set("wave", cache_key, data)
    return _to_wave_dataframe(data), build_source_meta(
        source_name,
        source_version,
        start_date,
        end_date,
        {"lat": location.wave_point.lat, "lon": location.wave_point.lon},
        cached=False,
        cache_fallback=False,
    )


def _to_wind_dataframe(payload: Dict[str, object]) -> pd.DataFrame:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    wind = daily.get("wind_speed_10m_mean", [])
    frame = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "wind_ms": pd.to_numeric(wind, errors="coerce"),
    })
    return frame


def _to_wave_dataframe(payload: Dict[str, object]) -> pd.DataFrame:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    wave = daily.get("wave_height_mean", [])
    frame = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "wave_hs_m": pd.to_numeric(wave, errors="coerce"),
    })
    return frame
