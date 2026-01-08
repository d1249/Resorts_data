from src.utils import ft_to_m, k_to_c, mph_to_ms


def test_mph_to_ms():
    assert round(mph_to_ms(10), 4) == 4.4704


def test_ft_to_m():
    assert round(ft_to_m(3.28084), 4) == 1.0


def test_k_to_c():
    assert round(k_to_c(273.15), 2) == 0.0
