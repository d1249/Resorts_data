import pytest

from src.score.comfort import compute_score


def test_clamp_score():
    params = {
        "score": {"clamp_min": 0, "clamp_max": 100},
        "thresholds": {
            "S0": 20.0,
            "S4": 30.0,
            "ColdAirT": 22.0,
            "HeatAirT": 33.0,
            "BreezeW0": 2.0,
            "BreezeW1": 6.0,
            "BreezeRamp": 2.0,
            "RainT1": 5.0,
            "RainT2": 15.0,
            "CalmWindT": 2.0,
            "BreathAirT": 30.0,
            "BreathRainT": 12.0,
            "BreathWindT": 3.0,
            "StrongWindT": 10.0,
            "WaveT1": 0.5,
            "WaveT2": 1.2,
            "WaveT3": 2.0,
        },
    }

    score, _ = compute_score(10, 5, 30, 20, 4, params)
    assert score == pytest.approx(0)


def test_reasonable_score():
    params = {
        "score": {"clamp_min": 0, "clamp_max": 100},
        "thresholds": {
            "S0": 20.0,
            "S4": 30.0,
            "ColdAirT": 22.0,
            "HeatAirT": 33.0,
            "BreezeW0": 2.0,
            "BreezeW1": 6.0,
            "BreezeRamp": 2.0,
            "RainT1": 5.0,
            "RainT2": 15.0,
            "CalmWindT": 2.0,
            "BreathAirT": 30.0,
            "BreathRainT": 12.0,
            "BreathWindT": 3.0,
            "StrongWindT": 10.0,
            "WaveT1": 0.5,
            "WaveT2": 1.2,
            "WaveT3": 2.0,
        },
    }

    score, components = compute_score(28, 27, 6, 4, 0.8, params)
    assert 40 <= score <= 100
    assert "SeaBase" in components
