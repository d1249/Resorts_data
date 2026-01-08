from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class WavePoint:
    mode: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Location:
    location_id: str
    country: str
    resort: str
    area: str
    lat: float
    lon: float
    wave_point: WavePoint
    timezone: str = "UTC"
    tags: Optional[list[str]] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        wave = data.get("wave_point", {})
        return cls(
            location_id=data["location_id"],
            country=data["country"],
            resort=data["resort"],
            area=data["area"],
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            wave_point=WavePoint(
                mode=wave.get("mode", "offshore"),
                lat=float(wave.get("lat", data["lat"])),
                lon=float(wave.get("lon", data["lon"])),
            ),
            timezone=data.get("timezone", "UTC"),
            tags=data.get("tags"),
            notes=data.get("notes"),
        )


@dataclass(frozen=True)
class Params:
    score: Dict[str, Any]
    thresholds: Dict[str, Any]
