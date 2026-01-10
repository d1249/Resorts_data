from __future__ import annotations

from datetime import date
from typing import Iterable, Optional, Union, Dict


def build_cache_key(
    source_name: str,
    source_version: str,
    location_id: str,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    variables: Union[str, Iterable[str]],
    units: str = "metric",
) -> str:
    if isinstance(variables, str):
        variables_part = variables
    else:
        variables_part = ",".join(variables)
    return (
        f"{source_name}:{source_version}:{location_id}:{lat}:{lon}:"
        f"{start_date.isoformat()}:{end_date.isoformat()}:{variables_part}:units={units}"
    )


def format_error(error: Optional[BaseException]) -> Optional[str]:
    if not error:
        return None
    message = str(error)
    if message:
        return f"{error.__class__.__name__}: {message}"
    return error.__class__.__name__


def build_source_meta(
    source_name: str,
    source_version: str,
    start_date: date,
    end_date: date,
    coordinates: Dict[str, float],
    cached: bool,
    cache_fallback: bool,
    error: Optional[BaseException] = None,
) -> Dict[str, object]:
    period_requested = {"start": start_date.isoformat(), "end": end_date.isoformat()}
    period_actual = {"start": start_date.isoformat(), "end": end_date.isoformat()}
    return {
        "source": source_name,
        "version": source_version,
        "period": {"requested": period_requested, "actual": period_actual},
        "requested_period": period_requested,
        "actual_period": period_actual,
        "coordinates": coordinates,
        "coverage": None,
        "cached": cached,
        "fallback_used": cache_fallback,
        "cache_fallback": cache_fallback,
        "error": format_error(error),
    }
