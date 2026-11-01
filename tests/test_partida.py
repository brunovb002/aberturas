import pytest

from aberturas import esperado_brancas, faixa, nomes, ritmo


@pytest.mark.parametrize(
    "tc, esperado",
    [
        ("15+0", "ultraBullet"),
        ("60+0", "bullet"),
        ("120+1", "bullet"),  # 120 + 40 = 160
        ("180+0", "blitz"),
        ("180+2", "blitz"),  # 260
        ("300+5", "rapid"),  # 500
        ("600+0", "rapid"),
        ("900+15", "classical"),  # 1500
        ("1800+0", "classical"),
        ("-", "correspondence"),
        ("abc", None),
    ],
)
def test_ritmo(tc, esperado):
    assert ritmo(tc) == esperado


def test_faixa():
    assert faixa(1500, 1500) == 1400
    assert faixa(1599, 1601) == 1600
    assert faixa(700, 900) == 800
    assert faixa(400, 500) == 800  # tudo abaixo de 1000 fica na primeira faixa
    assert faixa(2700, 2900) == 2400


def test_esperado_elo():
    assert esperado_brancas(1500, 1500) == 0.5
    # 400 pontos de diferença: chance de 10 para 1
    assert esperado_brancas(1900, 1500) == pytest.approx(10 / 11)
    assert esperado_brancas(1500, 1900) == pytest.approx(1 / 11)
    assert esperado_brancas(1600, 1500) + esperado_brancas(1500, 1600) == pytest.approx(1)


def test_nomes():
    assert nomes("Sicilian Defense: Najdorf Variation, English Attack") == (
        "Sicilian Defense",
        "Sicilian Defense: Najdorf Variation",
    )
    assert nomes("Sicilian Defense: Najdorf Variation") == (
        "Sicilian Defense",
        "Sicilian Defense: Najdorf Variation",
    )
    assert nomes("Elephant Gambit") == ("Elephant Gambit", None)
