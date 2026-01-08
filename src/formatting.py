from __future__ import annotations

from typing import Any


def format_decimal(value: Any, decimals: int = 1) -> str:
    if value is None:
        return ""
    fmt = f"{value:.{decimals}f}" if isinstance(value, (float, int)) else str(value)
    return fmt.replace(".", ",")


def format_with_flag(value: Any, flag: int, decimals: int = 1) -> str:
    formatted = format_decimal(value, decimals)
    return f"+{formatted}" if flag else formatted
