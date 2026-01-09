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
    source_name = "open_meteo_marine"
    source_version = "v1"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "sea_surface_temperature",
        "timezone": "UTC",
    }
    cache_key = (
        f"{source_name}:{source_version}:{location.location_id}:{location.lat}:{location.lon}:"
        f"{start_date.isoformat()}:{end_date.isoformat()}:{params['daily']}:units=metric"
    )
    cached = cache.get("sea_sst", cache_key)
    if cached and not refresh:
        return _to_dataframe(cached), {
            "source": source_name,
            "cached": True,
            "requested_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "actual_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    try:
        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        if cached:
            return _to_dataframe(cached), {
                "source": source_name,
                "cached": True,
                "fallback_cache": True,
                "requested_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "actual_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            }
        raise

    cache.set("sea_sst", cache_key, data)
    return _to_dataframe(data), {
        "source": source_name,
        "cached": False,
        "requested_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "actual_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
    }


def _to_dataframe(payload: Dict[str, object]) -> pd.DataFrame:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    sst = daily.get("sea_surface_temperature", [])
    frame = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "sst_c": pd.to_numeric(sst, errors="coerce"),
    })
    return frame
