from __future__ import annotations

from datetime import date
from typing import Dict, Tuple

import pandas as pd

from src.cache import DiskCache
from src.models import Location
from src.sources.wind_wave_provider import WindWaveProvider


class Era5WindWave(WindWaveProvider):
    def fetch(
        self,
        location: Location,
        start_date: date,
        end_date: date,
        cache: DiskCache,
        refresh: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, object]]:
        raise NotImplementedError("ERA5 provider requires credentials/configuration.")
