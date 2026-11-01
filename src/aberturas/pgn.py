"""Leitura só dos cabeçalhos de um PGN.

Os lances não interessam aqui: o Lichess já escreve o nome da abertura no cabeçalho.
Uma partida só é entregue quando aparece a linha de lances, então se o arquivo terminar
no meio de uma partida (o que acontece quando lemos só o começo do mês), ela é ignorada.
"""

from collections.abc import Iterable, Iterator


def cabecalhos(linhas: Iterable[str], chaves: set[str] | None = None) -> Iterator[dict[str, str]]:
    atual: dict[str, str] = {}
    dentro = False
    for linha in linhas:
        if linha.startswith("["):
            dentro = True
            ini = linha.find(' "')
            fim = linha.rfind('"')
            if ini == -1 or fim < ini + 2:
                continue
            chave = linha[1:ini]
            if chaves is None or chave in chaves:
                atual[chave] = linha[ini + 2 : fim]
        elif dentro and linha.strip():
            yield atual
            atual = {}
            dentro = False
