"""Capa do projeto: as aberturas mais jogadas no blitz, pontos acima do esperado por faixa de rating.

    python scripts/gerar_capa.py meses capa.png

Precisa do Pillow (pip install pillow). Gera 900x1200 (3:4), o formato dos cards do site.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 2  # desenha em 2x e reduz no fim, para as linhas ficarem suaves
W, H = 900 * S, 1200 * S
ESQ, DIR, TOPO, BASE_Y = 90 * S, 90 * S, 200 * S, 360 * S
VERDE = (47, 93, 80)
FONTE = "C:/Windows/Fonts/consola.ttf"
RITMO = "blitz"
FAIXAS = list(range(800, 2401, 200))
QUANTAS = 10
MIN_PARTIDAS = 300


def mistura(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def somar(pasta: Path):
    """Soma os meses: por abertura e faixa, e a base com todas as partidas da faixa."""
    aberturas = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0.0]))
    base = defaultdict(lambda: [0, 0, 0, 0.0])
    for arquivo in sorted(pasta.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].json")):
        for nome, ritmo, faixa, b, e, p, esp in json.loads(arquivo.read_text(encoding="utf-8"))["familias"]:
            if ritmo != RITMO:
                continue
            for c in (aberturas[nome][faixa], base[faixa]):
                c[0] += b; c[1] += e; c[2] += p; c[3] += esp
    return aberturas, base


def acima(c, b):
    """Pontos das brancas menos o esperado pelo Elo menos a vantagem típica da faixa, em p.p."""
    n, nb = sum(c[:3]), sum(b[:3])
    return 100 * ((c[0] + c[1] / 2 - c[3]) / n - (b[0] + b[1] / 2 - b[3]) / nb)


def main(pasta: Path, saida: Path) -> None:
    aberturas, base = somar(pasta)
    total = lambda nome: sum(sum(c[:3]) for c in aberturas[nome].values())
    top = sorted(aberturas, key=total, reverse=True)[:QUANTAS]
    linhas = {
        nome: [(i, acima(aberturas[nome][f], base[f])) for i, f in enumerate(FAIXAS)
               if sum(aberturas[nome][f][:3]) >= MIN_PARTIDAS]
        for nome in top
    }
    lim = max(abs(v) for pts in linhas.values() for _, v in pts) + 0.5
    x = lambda i: ESQ + i / (len(FAIXAS) - 1) * (W - ESQ - DIR)
    y = lambda v: TOPO + (lim - v) / (2 * lim) * (H - TOPO - BASE_Y)

    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    claro, escuro = mistura(VERDE, (255, 255, 255), 0.25), mistura(VERDE, (0, 0, 0), 0.35)
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=mistura(claro, VERDE, t / 0.55) if t < 0.55 else mistura(VERDE, escuro, (t - 0.55) / 0.45))

    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c = ImageDraw.Draw(camada)
    fonte = ImageFont.truetype(FONTE, 28 * S)

    # Tabuleiro discreto ao fundo: 8 colunas de casas alternadas, só um tom acima do verde.
    casa = (W - ESQ - DIR) / 8
    for lin in range(int((H - TOPO - BASE_Y) / casa)):
        for col in range(8):
            if (lin + col) % 2 == 0:
                x0, y0 = ESQ + col * casa, TOPO + lin * casa
                c.rectangle([x0, y0, x0 + casa, y0 + casa], fill=(255, 255, 255, 14))

    c.line([(ESQ, y(0)), (W - DIR, y(0))], fill=(255, 255, 255, 110), width=2 * S)
    destaque = top[0]
    for nome in top[1:]:
        c.line([(x(i), y(v)) for i, v in linhas[nome]], fill=(255, 255, 255, 110), width=3 * S, joint="curve")
    pts = [(x(i), y(v)) for i, v in linhas[destaque]]
    c.line(pts, fill=(255, 255, 255, 255), width=8 * S, joint="curve")
    for px, py in pts:
        c.ellipse([px - 9 * S, py - 9 * S, px + 9 * S, py + 9 * S], fill=(255, 255, 255, 255))

    c.text((ESQ, TOPO - 40 * S), "<1000", font=fonte, fill=(255, 255, 255, 150), anchor="ls")
    c.text((W - DIR, TOPO - 40 * S), "2400+", font=fonte, fill=(255, 255, 255, 150), anchor="rs")

    titulo = ImageFont.truetype(FONTE, 66 * S)
    c.text((ESQ, H - 235 * S), "aberturas", font=titulo, fill=(255, 255, 255, 255))
    c.text((ESQ, H - 160 * S), f"{destaque} em destaque", font=fonte, fill=(255, 255, 255, 200))
    c.text((ESQ, H - 115 * S), "Lichess · blitz · acima do esperado", font=fonte, fill=(255, 255, 255, 170))

    img = Image.alpha_composite(img.convert("RGBA"), camada).convert("RGB")
    img.resize((W // S, H // S), Image.LANCZOS).save(saida, optimize=True)
    print(f"Capa salva em {saida} ({len(top)} aberturas, de -{lim:.1f} a +{lim:.1f} p.p.)")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
