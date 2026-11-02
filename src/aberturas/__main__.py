"""Linha de comando.

    python -m aberturas mes 2026-09                  amostra de um mês (1 GB compactado)
    python -m aberturas mes 2026-09 --arquivo x.zst  a partir de um arquivo baixado
    python -m aberturas pendentes --desde 2013-01    todos os meses que ainda faltam
    python -m aberturas evolucao                     junta os meses por ano em evolucao.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

from . import evolucao, lichess
from .contagem import CHAVES, Contagem
from .pgn import cabecalhos

PASTA = Path("meses")
GB = 1024**3


def processar_mes(mes: str, limite_gb: float | None, arquivo: str | None = None) -> None:
    limite = int(limite_gb * GB) if limite_gb else None
    origem = arquivo or lichess.url(mes)
    inicio = time.monotonic()
    contagem = Contagem()
    with lichess.abrir(origem, limite) as (texto, bruto):
        for cab in cabecalhos(texto, CHAVES):
            contagem.adicionar(cab)
            if contagem.lidas % 1_000_000 == 0:
                print(f"  {mes}: {contagem.lidas:,} partidas, {bruto.lidos / GB:.2f} GB", file=sys.stderr)
    completo = limite is None or bruto.lidos < limite

    contagem.salvar(PASTA / f"{mes}.json", mes, completo)
    atualizar_indice(mes, contagem.usadas, completo)
    segundos = time.monotonic() - inicio
    print(f"{mes}: {contagem.usadas:,} de {contagem.lidas:,} partidas usadas"
          f"{' (mês inteiro)' if completo else ''}, {segundos:.0f} s")


def atualizar_indice(mes: str, partidas: int, completo: bool) -> None:
    caminho = PASTA / "indice.json"
    indice = json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {"meses": {}}
    indice["meses"][mes] = {"partidas": partidas, "completo": completo}
    indice["meses"] = dict(sorted(indice["meses"].items()))
    indice["ultimo"] = max(indice["meses"])
    caminho.write_text(json.dumps(indice, indent=1) + "\n", encoding="utf-8")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="aberturas")
    sub = p.add_subparsers(dest="comando", required=True)

    m = sub.add_parser("mes", help="processa um mês")
    m.add_argument("mes", help="AAAA-MM")
    m.add_argument("--arquivo", help=".pgn.zst local, no lugar de baixar")

    pend = sub.add_parser("pendentes", help="processa os meses que ainda não estão em meses/")
    pend.add_argument("--desde", default="2013-01")
    pend.add_argument("--max", type=int, help="no máximo quantos meses nesta rodada")

    sub.add_parser("evolucao", help="junta os meses prontos por ano em evolucao.json")

    for s in (m, pend):
        s.add_argument("--limite-gb", type=float, default=1.0,
                       help="quanto ler de cada arquivo compactado (0 = inteiro)")

    args = p.parse_args(argv)
    if args.comando == "evolucao":
        resumo = evolucao.resumir(PASTA)
        evolucao.salvar(resumo, Path("evolucao.json"))
        print(f"evolucao.json: {len(resumo['aberturas'])} aberturas, {resumo['anos'][0]} a {resumo['ate']}")
        return
    limite = args.limite_gb or None

    if args.comando == "mes":
        processar_mes(args.mes, limite, args.arquivo)
        return

    feitos = {c.stem for c in PASTA.glob("????-??.json")}
    # Do mais novo para o mais antigo: a rodada mensal pega primeiro o mês que acabou de sair.
    faltam = [m for m in reversed(lichess.meses_disponiveis()) if m >= args.desde and m not in feitos]
    if args.max:
        faltam = faltam[: args.max]
    print(f"{len(faltam)} meses para processar")
    for mes in faltam:
        processar_mes(mes, limite)


if __name__ == "__main__":
    main()
