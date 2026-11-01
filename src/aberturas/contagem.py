"""Soma as partidas de um mês por abertura, ritmo e faixa de rating."""

import json
from collections import defaultdict
from pathlib import Path

from .partida import RESULTADOS, RITMOS, esperado_brancas, faixa, nomes, ritmo

CHAVES = {"Result", "WhiteElo", "BlackElo", "TimeControl", "Opening", "Termination"}

# Abaixo disso a abertura sai do arquivo do mês: é ruído e só aumenta o tamanho.
MINIMO_FAMILIA = 50
MINIMO_VARIANTE = 1000


def _celula():
    # [vitórias das brancas, empates, vitórias das pretas, soma do esperado das brancas]
    return [0, 0, 0, 0.0]


class Contagem:
    def __init__(self):
        self.familias = defaultdict(_celula)
        self.variantes = defaultdict(_celula)
        self.lidas = 0
        self.usadas = 0

    def adicionar(self, cab: dict[str, str]) -> None:
        self.lidas += 1
        resultado = RESULTADOS.get(cab.get("Result", ""))
        if resultado is None or cab.get("Termination") == "Abandoned":
            return
        r = ritmo(cab.get("TimeControl", ""))
        if r not in RITMOS:
            return
        try:
            brancas, pretas = int(cab["WhiteElo"]), int(cab["BlackElo"])
        except (KeyError, ValueError):
            return
        abertura = cab.get("Opening", "?")
        if abertura == "?":
            return

        familia, variante = nomes(abertura)
        f = faixa(brancas, pretas)
        e = esperado_brancas(brancas, pretas)
        alvos = [self.familias[familia, r, f]]
        if variante:
            alvos.append(self.variantes[variante, r, f])
        for celula in alvos:
            celula[resultado] += 1
            celula[3] += e
        self.usadas += 1

    def linhas(self, tabela, minimo: int) -> list[list]:
        totais = defaultdict(int)
        for (nome, _, _), c in tabela.items():
            totais[nome] += c[0] + c[1] + c[2]
        ordem = {r: i for i, r in enumerate(RITMOS)}
        chaves = sorted(
            (k for k in tabela if totais[k[0]] >= minimo),
            key=lambda k: (k[0], ordem[k[1]], k[2]),
        )
        return [[*k, *tabela[k][:3], round(tabela[k][3], 2)] for k in chaves]

    def salvar(self, caminho: Path, mes: str, completo: bool) -> None:
        """Grava uma linha por célula, para o diff do git ficar legível."""
        cabeca = {
            "mes": mes,
            "partidas": self.usadas,
            "lidas": self.lidas,
            "completo": completo,
            "colunas": ["abertura", "ritmo", "faixa", "brancas", "empates", "pretas", "esperado"],
        }
        partes = [json.dumps(cabeca, ensure_ascii=False)[:-1]]
        for nome, tabela, minimo in (
            ("familias", self.familias, MINIMO_FAMILIA),
            ("variantes", self.variantes, MINIMO_VARIANTE),
        ):
            linhas = ",\n".join(json.dumps(l, ensure_ascii=False) for l in self.linhas(tabela, minimo))
            partes.append(f'"{nome}": [\n{linhas}\n]')
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(",\n".join(partes) + "}\n", encoding="utf-8")
