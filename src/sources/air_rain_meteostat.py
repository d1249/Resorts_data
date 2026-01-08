from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

import pandas as pd
import requests

from src.cache import DiskCache
from src.models import Location


def fetch_air_rain_daily(
    location: Location,
    start_date: date,
    end_date: date,
    cache: DiskCache,
    refresh: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Fetch daily Tmax and precipitation using Open-Meteo archive."""
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_max,precipitation_sum",
        "timezone": "UTC",
    }
    cache_key = f"air_rain:{location.location_id}:{params}"
    if not refresh:
        cached = cache.get("air_rain", cache_key)
        if cached:
            return _to_dataframe(cached), {"source": "open_meteo_archive"}

    response = requests.get(endpoint, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    cache.set("air_rain", cache_key, data)
    return _to_dataframe(data), {"source": "open_meteo_archive"}


def _to_dataframe(payload: Dict[str, object]) -> pd.DataFrame:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    prcp = daily.get("precipitation_sum", [])
    frame = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "tmax_c": pd.to_numeric(tmax, errors="coerce"),
        "prcp_mm": pd.to_numeric(prcp, errors="coerce"),
    })
    return frame
