from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

import pandas as pd
import requests

from src.cache import DiskCache
from src.models import Location


def fetch_sea_surface_temperature(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Fetch daily sea surface temperature via Open-Meteo marine API."""
    endpoint = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "sea_surface_temperature",
        "timezone": "UTC",
    }
    cache_key = f"sea_sst:{location.location_id}:{params}"
    cached = cache.get("sea_sst", cache_key)
    if cached and not refresh:
        return _to_dataframe(cached), {"source": "open_meteo_marine", "cached": True}

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        if cached:
            return _to_dataframe(cached), {
                "source": "open_meteo_marine",
                "cached": True,
                "fallback_cache": True,
            }
        raise

    cache.set("sea_sst", cache_key, data)
    return _to_dataframe(data), {"source": "open_meteo_marine", "cached": False}


def _to_dataframe(payload: Dict[str, object]) -> pd.DataFrame:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    sst = daily.get("sea_surface_temperature", [])
    frame = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "sst_c": pd.to_numeric(sst, errors="coerce"),
    })
    return frame
