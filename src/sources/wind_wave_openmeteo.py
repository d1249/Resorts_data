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
    ) -> Tuple[pd.DataFrame, Dict[str, str]]:
        wind_df = _fetch_wind(location, start_date, end_date, cache, refresh)
        wave_df = _fetch_wave(location, start_date, end_date, cache, refresh)
        merged = pd.merge(wind_df, wave_df, on="date", how="outer")
        return merged, {"source": "open_meteo"}


def _fetch_wind(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> pd.DataFrame:
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "wind_speed_10m_max",
        "timezone": "UTC",
    }
    cache_key = f"wind:{location.location_id}:{params}"
    if not refresh:
        cached = cache.get("wind", cache_key)
        if cached:
            return _to_wind_dataframe(cached)

    response = requests.get(endpoint, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    cache.set("wind", cache_key, data)
    return _to_wind_dataframe(data)


def _fetch_wave(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool,
) -> pd.DataFrame:
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
    if not refresh:
        cached = cache.get("wave", cache_key)
        if cached:
            return _to_wave_dataframe(cached)

    response = requests.get(endpoint, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    cache.set("wave", cache_key, data)
    return _to_wave_dataframe(data)


def _to_wind_dataframe(payload: Dict[str, object]) -> pd.DataFrame:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    wind = daily.get("wind_speed_10m_max", [])
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
