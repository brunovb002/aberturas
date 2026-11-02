"""Junta os meses por ano, para ver como a popularidade de cada abertura mudou.

Os arquivos mensais somados passam de 150 MB; este resumo guarda só quantas partidas cada
abertura teve por ano, ritmo e faixa de rating, e cabe em algumas centenas de KB.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from .partida import FAIXAS, RITMOS

# Uma abertura entra no resumo se chegou a essa fatia das partidas em algum ano, ritmo e faixa
# com partidas suficientes. As outras são raras demais para aparecer num gráfico.
FATIA_MINIMA = 0.01
PARTIDAS_MINIMAS = 10_000

# O Lichess revisou os nomes das aberturas entre 2017 e 2021. Os nomes antigos com "#2", "#3"
# e os que vinham com a variante depois da vírgula ("King's Gambit Accepted, Fischer Defense")
# viram a família; estes aqui mudaram de nome de vez.
NOMES_ANTIGOS = {
    "Indian Game": "Indian Defense",
    "Queen's Gambit Refused": "Queen's Gambit Declined",
    "Queen's Pawn": "Queen's Pawn Game",
    "Robatsch (Modern) Defense": "Modern Defense",
    "Old Benoni Defense": "Benoni Defense",
    "Gruenfeld Defense": "Grünfeld Defense",
    "Reti Opening": "Réti Opening",
    "Budapest Defense": "Budapest Gambit",
    "Petrov's Defense": "Russian Game",
    "Petrov": "Russian Game",
}


def familia(nome: str) -> str:
    nome = re.sub(r" #\d+$", "", nome).split(", ")[0]
    return NOMES_ANTIGOS.get(nome, nome)


def _grade(anos):
    return [[[0] * len(anos) for _ in FAIXAS] for _ in RITMOS]


def resumir(pasta: Path) -> dict:
    arquivos = sorted(pasta.glob("????-??.json"))
    meses = [a.stem for a in arquivos]
    anos = sorted({int(m[:4]) for m in meses})
    pos_ano = {a: i for i, a in enumerate(anos)}
    pos_ritmo = {r: i for i, r in enumerate(RITMOS)}
    pos_faixa = {f: i for i, f in enumerate(FAIXAS)}

    total = _grade(anos)
    por_abertura = defaultdict(lambda: _grade(anos))
    for arquivo in arquivos:
        a = pos_ano[int(arquivo.stem[:4])]
        for nome, ritmo, faixa, b, e, p, _ in json.loads(arquivo.read_text(encoding="utf-8"))["familias"]:
            if ritmo not in pos_ritmo or faixa not in pos_faixa:
                continue
            r, f = pos_ritmo[ritmo], pos_faixa[faixa]
            total[r][f][a] += b + e + p
            por_abertura[familia(nome)][r][f][a] += b + e + p

    def entra(grade):
        return any(
            total[r][f][a] >= PARTIDAS_MINIMAS and grade[r][f][a] >= FATIA_MINIMA * total[r][f][a]
            for r in range(len(RITMOS)) for f in range(len(FAIXAS)) for a in range(len(anos))
        )

    ultimo = max(meses)
    return {
        "anos": anos,
        # O último ano costuma estar pela metade; o site avisa até que mês ele vai.
        "ate": ultimo,
        "ritmos": list(RITMOS),
        "faixas": list(FAIXAS),
        "total": total,
        "aberturas": {nome: g for nome, g in sorted(por_abertura.items()) if entra(g)},
    }


def salvar(resumo: dict, caminho: Path) -> None:
    """Uma abertura por linha, para o diff do git continuar legível."""
    cabeca = {k: v for k, v in resumo.items() if k != "aberturas"}
    linhas = ",\n".join(
        f"{json.dumps(nome, ensure_ascii=False)}: {json.dumps(g, separators=(',', ':'))}"
        for nome, g in resumo["aberturas"].items()
    )
    texto = json.dumps(cabeca, ensure_ascii=False, separators=(",", ":"))[:-1]
    caminho.write_text(f'{texto},\n"aberturas": {{\n{linhas}\n}}}}\n', encoding="utf-8")
