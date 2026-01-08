from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

import pandas as pd
import requests

from src.cache import DiskCache
from src.models import Location
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
        return merged, {"source": "open_meteo", "wind": wind_meta, "wave": wave_meta}


def _fetch_wind(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "wind_speed_10m_mean",
        "timezone": "UTC",
    }
    cache_key = f"wind:{location.location_id}:{params}"
    cached = cache.get("wind", cache_key)
    if cached and not refresh:
        return _to_wind_dataframe(cached), {"source": "open_meteo_archive", "cached": True}

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        if cached:
            return _to_wind_dataframe(cached), {
                "source": "open_meteo_archive",
                "cached": True,
                "fallback_cache": True,
            }
        raise

    cache.set("wind", cache_key, data)
    return _to_wind_dataframe(data), {"source": "open_meteo_archive", "cached": False}


def _fetch_wave(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    endpoint = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": location.wave_point.lat,
        "longitude": location.wave_point.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "wave_height_mean",
        "timezone": "UTC",
    }
    cache_key = f"wave:{location.location_id}:{params}"
    cached = cache.get("wave", cache_key)
    if cached and not refresh:
        return _to_wave_dataframe(cached), {"source": "open_meteo_marine", "cached": True}

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        if cached:
            return _to_wave_dataframe(cached), {
                "source": "open_meteo_marine",
                "cached": True,
                "fallback_cache": True,
            }
        raise

    cache.set("wave", cache_key, data)
    return _to_wave_dataframe(data), {"source": "open_meteo_marine", "cached": False}


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
