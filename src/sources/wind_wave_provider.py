from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, Tuple

import pandas as pd

from src.cache import DiskCache
from src.models import Location


class WindWaveProvider(ABC):
    @abstractmethod
    def fetch(
        self,
        location: Location,
        start_date: date,
        end_date: date,
        cache: DiskCache,
        refresh: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, object]]:
        raise NotImplementedError
