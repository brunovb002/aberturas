"""Como cada partida é classificada: ritmo, faixa de rating, abertura e resultado esperado."""

RITMOS = ("bullet", "blitz", "rapid", "classical")

# Faixas pela média de rating dos dois jogadores, de 200 em 200.
# A primeira junta tudo abaixo de 1000 e a última tudo de 2400 para cima.
FAIXAS = tuple(range(800, 2401, 200))

# Posição de cada resultado na contagem [brancas, empates, pretas].
RESULTADOS = {"1-0": 0, "1/2-1/2": 1, "0-1": 2}


def ritmo(time_control: str) -> str | None:
    """Mesma regra do Lichess: tempo estimado = base + 40 × incremento, em segundos."""
    if time_control == "-":
        return "correspondence"
    base, _, incremento = time_control.partition("+")
    try:
        estimado = int(base) + 40 * int(incremento or 0)
    except ValueError:
        return None
    if estimado < 30:
        return "ultraBullet"
    if estimado < 180:
        return "bullet"
    if estimado < 480:
        return "blitz"
    if estimado < 1500:
        return "rapid"
    return "classical"


def faixa(elo_brancas: int, elo_pretas: int) -> int:
    media = (elo_brancas + elo_pretas) / 2
    return min(max(int(media // 200) * 200, FAIXAS[0]), FAIXAS[-1])


def esperado_brancas(elo_brancas: int, elo_pretas: int) -> float:
    """Pontuação esperada das brancas pela fórmula do Elo (vitória 1, empate 0,5)."""
    return 1 / (1 + 10 ** ((elo_pretas - elo_brancas) / 400))


def nomes(abertura: str) -> tuple[str, str | None]:
    """Separa "Sicilian Defense: Najdorf Variation, English Attack" em família e variante.

    A variante vai só até a primeira vírgula; as subvariantes ficam dentro dela.
    Aberturas sem dois-pontos (como "Elephant Gambit") não têm variante.
    """
    familia, sep, _ = abertura.partition(":")
    if not sep:
        return abertura, None
    return familia, abertura.split(",")[0]
