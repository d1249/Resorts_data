from __future__ import annotations

from typing import Dict, Tuple


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _interp(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    if x <= x0:
        return y0
    if x >= x1:
        return y1
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def compute_score(
    air_c: float,
    sea_c: float,
    rain_days: float,
    wind_ms: float,
    wave_hs_m: float,
    params: Dict[str, Dict[str, float]],
) -> Tuple[float, Dict[str, float]]:
    thresholds = params["thresholds"]
    clamp_min = params["score"]["clamp_min"]
    clamp_max = params["score"]["clamp_max"]

    sea_base = _interp(sea_c, thresholds["S0"], thresholds["S4"], 0, 100)
    sea_base = _clamp(sea_base, 0, 100)

    air_adj = -abs(air_c - sea_c) * thresholds["dS"]

    breeze = _interp(wind_ms, 0, thresholds["BreezeW0"], 0, 5)

    warm_for_breeze = 0.0
    if air_c > thresholds["HeatAirT"]:
        warm_for_breeze = _interp(
            air_c,
            thresholds["HeatAirT"],
            thresholds["HeatAirT"] + thresholds["dS"],
            0,
            5,
        )

    breeze_bonus = 0.0
    if thresholds["BreezeW0"] < wind_ms < thresholds["BreezeW1"]:
        breeze_bonus = (wind_ms - thresholds["BreezeW0"]) * thresholds["BreezeRamp"]

    cold = 0.0
    if air_c < thresholds["ColdAirT"]:
        cold = (thresholds["ColdAirT"] - air_c) * 2

    wind_ex_cold = 0.0
    if air_c < thresholds["ColdAirT"] and wind_ms > thresholds["WindColdT"]:
        wind_ex_cold = (wind_ms - thresholds["WindColdT"]) * 1.5

    rain_pen = _interp(rain_days, thresholds["RainT1"], thresholds["RainT2"], 0, 20)
    rain_pen = _clamp(rain_pen, 0, 20)

    wet_pen = 0.0
    if rain_days > thresholds["RainT2"]:
        wet_pen = (rain_days - thresholds["RainT2"]) * 0.5

    heat_pen = 0.0
    if air_c > thresholds["HeatAirT"] and wind_ms < thresholds["CalmWindT"]:
        heat_pen = (air_c - thresholds["HeatAirT"]) * 1.5

    breath_pen = 0.0
    if (
        air_c > thresholds["BreathAirT"]
        and rain_days > thresholds["BreathRainT"]
        and wind_ms < thresholds["BreathWindT"]
    ):
        breath_pen = 10.0

    strong_wind_pen = 0.0
    if wind_ms > thresholds["StrongWindT"]:
        strong_wind_pen = (wind_ms - thresholds["StrongWindT"]) * 1.5

    wave_pen = 0.0
    if wave_hs_m > thresholds["WaveT1"]:
        if wave_hs_m <= thresholds["WaveT2"]:
            wave_pen = _interp(
                wave_hs_m,
                thresholds["WaveT1"],
                thresholds["WaveT2"],
                0,
                7.5,
            )
        else:
            wave_pen = _interp(
                wave_hs_m,
                thresholds["WaveT2"],
                thresholds["WaveT3"],
                7.5,
                15,
            )
    wave_pen = _clamp(wave_pen, 0, 15)

    score_raw = (
        sea_base
        + air_adj
        + breeze
        + warm_for_breeze
        + breeze_bonus
        - cold
        - wind_ex_cold
        - wet_pen
        - rain_pen
        - heat_pen
        - breath_pen
        - strong_wind_pen
        - wave_pen
    )

    score = _clamp(score_raw, clamp_min, clamp_max)

    components = {
        "SeaBase": sea_base,
        "AirAdj": air_adj,
        "Breeze": breeze,
        "WarmForBreeze": warm_for_breeze,
        "BreezeBonus": breeze_bonus,
        "Cold": cold,
        "WindExCold": wind_ex_cold,
        "WetPen": wet_pen,
        "RainPen": rain_pen,
        "HeatPen": heat_pen,
        "BreathPen": breath_pen,
        "StrongWindPen": strong_wind_pen,
        "WavePen": wave_pen,
        "Score_raw": score_raw,
    }
    return score, components
