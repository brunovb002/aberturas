"""Capa do projeto: o tabuleiro depois da abertura mais jogada da amostra, com os lances em setas.

    python scripts/gerar_capa.py meses capa.png

Precisa do Pillow (pip install pillow). Gera 900x1200 (3:4), o formato dos cards do site.
A abertura vem dos dados; os lances de cada uma estão em LANCES, então se a mais jogada
mudar para uma que não está lá, é só acrescentar.
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 2  # desenha em 2x e reduz no fim, para as linhas ficarem suaves
W, H = 900 * S, 1200 * S
CASA = W // 8
VERDE = (47, 93, 80)
CLARA, ESCURA = (226, 222, 204), (98, 140, 118)
SETA = (232, 163, 61, 210)
PECAS = "C:/Windows/Fonts/seguisym.ttf"
SERIF = "C:/Windows/Fonts/georgia.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"

# Lances de cada abertura (origem e destino) e como aparecem escritos.
LANCES = {
    "Sicilian Defense": (["e2e4", "c7c5"], "1. e4 c5"),
    "Queen's Pawn Game": (["d2d4", "d7d5"], "1. d4 d5"),
    "French Defense": (["e2e4", "e7e6"], "1. e4 e6"),
    "Caro-Kann Defense": (["e2e4", "c7c6"], "1. e4 c6"),
    "Scandinavian Defense": (["e2e4", "d7d5"], "1. e4 d5"),
    "Italian Game": (["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"], "1. e4 e5 2. Nf3 Nc6 3. Bc4"),
}

# Glifo cheio para os dois lados; a cor do preenchimento diz de quem é a peça.
GLIFOS = {"r": "♜", "n": "♞", "b": "♝", "q": "♛", "k": "♚", "p": "♟"}
INICIAL = ["rnbqkbnr", "pppppppp", "", "", "", "", "PPPPPPPP", "RNBQKBNR"]


def mais_jogada(pasta: Path) -> str:
    total = Counter()
    for arquivo in pasta.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].json"):
        for nome, _, _, b, e, p, _ in json.loads(arquivo.read_text(encoding="utf-8"))["familias"]:
            total[nome] += b + e + p
    return next(n for n, _ in total.most_common() if n in LANCES)


def casa(c: str) -> tuple[int, int]:
    """'e4' -> (coluna, linha na imagem), com as brancas embaixo."""
    return ord(c[0]) - ord("a"), 8 - int(c[1])


def centro(c: str) -> tuple[float, float]:
    col, lin = casa(c)
    return (col + 0.5) * CASA, (lin + 0.5) * CASA


def seta(d: ImageDraw.ImageDraw, de: str, para: str) -> None:
    """Seta no estilo dos tabuleiros online: haste grossa e ponta larga, parando antes do centro."""
    (x0, y0), (x1, y1) = centro(de), centro(para)
    ang = math.atan2(y1 - y0, x1 - x0)
    cos, sen = math.cos(ang), math.sin(ang)
    xf, yf = x1 - 0.12 * CASA * cos, y1 - 0.12 * CASA * sen
    xb, yb = xf - 0.42 * CASA * cos, yf - 0.42 * CASA * sen
    xi, yi = x0 + 0.28 * CASA * cos, y0 + 0.28 * CASA * sen
    d.line([(xi, yi), (xb, yb)], fill=SETA, width=round(0.16 * CASA))
    abre = 0.3 * CASA
    d.polygon([(xf, yf), (xb - abre * sen, yb + abre * cos), (xb + abre * sen, yb - abre * cos)], fill=SETA)


def quadrado(d: ImageDraw.ImageDraw, col: int, lin: int, cor) -> None:
    d.rectangle([col * CASA, lin * CASA, (col + 1) * CASA - 1, (lin + 1) * CASA - 1], fill=cor)


def main(pasta: Path, saida: Path) -> None:
    abertura = mais_jogada(pasta)
    lances, notacao = LANCES[abertura]

    tab = [list(l.ljust(8)) for l in INICIAL]
    for lance in lances:
        (c0, l0), (c1, l1) = casa(lance[:2]), casa(lance[2:])
        tab[l1][c1], tab[l0][c0] = tab[l0][c0], " "

    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    # Embaixo do tabuleiro, o verde do card escurecendo até a base.
    for i in range(W, H):
        t = (i - W) / (H - W)
        d.line([(0, i), (W, i)], fill=tuple(round(v * (1 - 0.35 * t)) for v in VERDE))
    for lin in range(8):
        for col in range(8):
            quadrado(d, col, lin, CLARA if (lin + col) % 2 == 0 else ESCURA)

    # Casas de origem e destino marcadas de leve, como num tabuleiro online.
    marca = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for lance in lances:
        for c in (lance[:2], lance[2:]):
            quadrado(ImageDraw.Draw(marca), *casa(c), (232, 163, 61, 70))
    img = Image.alpha_composite(img, marca)

    # Setas por baixo das peças, para não cobrir quem chegou na casa.
    setas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for lance in lances:
        seta(ImageDraw.Draw(setas), lance[:2], lance[2:])
    img = Image.alpha_composite(img, setas)

    d = ImageDraw.Draw(img)
    fonte = ImageFont.truetype(PECAS, round(CASA * 0.82))
    for lin in range(8):
        for col in range(8):
            p = tab[lin][col]
            if p != " ":
                d.text(((col + 0.5) * CASA, (lin + 0.54) * CASA), GLIFOS[p.lower()], font=fonte, anchor="mm",
                       fill=(250, 248, 240) if p.isupper() else (28, 30, 30),
                       stroke_width=round(CASA * 0.03), stroke_fill=(28, 30, 30))

    # Texto com transparência de verdade: desenha em modo RGBA sobre a imagem já sem canal alfa.
    img = img.convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    esq = 90 * S
    d.text((esq, H - 205 * S), "aberturas", font=ImageFont.truetype(SERIF, 84 * S), fill=(255, 255, 255))
    mono = ImageFont.truetype(MONO, 28 * S)
    d.text((esq, H - 100 * S), f"{notacao} · {abertura}", font=mono, fill=(255, 255, 255, 220))
    d.text((esq, H - 58 * S), "a mais jogada no Lichess", font=mono, fill=(255, 255, 255, 160))

    img.resize((W // S, H // S), Image.LANCZOS).save(saida, optimize=True)
    print(f"Capa salva em {saida} ({abertura}, {notacao})")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
