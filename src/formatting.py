from __future__ import annotations

from typing import Any

import math


def format_decimal(value: Any, decimals: int = 1) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, (float, int)):
        fmt = f"{value:.{decimals}f}"
        return fmt.replace(".", ",")
    return str(value).replace(".", ",")


def format_with_flag(value: Any, flag: int, decimals: int = 1) -> str:
    formatted = format_decimal(value, decimals)
    if not formatted:
        return ""
    return f"+{formatted}" if flag else formatted
