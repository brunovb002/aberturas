"""Acesso à base aberta do Lichess (database.lichess.org, licença CC0).

Cada mês é um .pgn.zst de dezenas de GB. Como só precisamos de uma amostra, baixamos os
primeiros bytes do arquivo (com Range) e descompactamos em streaming, sem gravar nada.
O zstd aceita ser cortado no meio: o que veio até ali sai normalmente.
"""

import io
import re
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import zstandard

BASE = "https://database.lichess.org/standard/"
AGENTE = "aberturas (github.com/brunovb002/aberturas)"


def url(mes: str) -> str:
    return f"{BASE}lichess_db_standard_rated_{mes}.pgn.zst"


def _abrir_url(endereco: str, limite: int | None = None):
    cabecalhos = {"User-Agent": AGENTE}
    if limite:
        cabecalhos["Range"] = f"bytes=0-{limite - 1}"
    return urllib.request.urlopen(urllib.request.Request(endereco, headers=cabecalhos), timeout=60)


def meses_disponiveis() -> list[str]:
    with _abrir_url(BASE + "list.txt") as resp:
        texto = resp.read().decode()
    return sorted(set(re.findall(r"rated_(\d{4}-\d{2})\.pgn\.zst", texto)))


class _Limitado(io.RawIOBase):
    """Lê no máximo `limite` bytes da fonte e conta quantos vieram."""

    def __init__(self, fonte, limite: int | None):
        self.fonte = fonte
        self.limite = limite
        self.lidos = 0

    def readable(self):
        return True

    def readinto(self, b):
        b = memoryview(b)
        if self.limite is not None:
            b = b[: max(self.limite - self.lidos, 0)]
            if not len(b):
                return 0
        n = self.fonte.readinto(b) or 0
        self.lidos += n
        return n


@contextmanager
def abrir(origem: str | Path, limite: int | None = None) -> Iterator[tuple[io.TextIOBase, _Limitado]]:
    """Abre um .pgn.zst (URL ou arquivo local) como texto.

    Devolve também o leitor bruto, para saber depois quantos bytes foram lidos e se o
    arquivo acabou antes do limite (ou seja, se o mês foi lido inteiro).
    """
    if str(origem).startswith("http"):
        fonte = _abrir_url(str(origem), limite)
    else:
        fonte = open(origem, "rb")
    with fonte:
        bruto = _Limitado(fonte, limite)
        leitor = zstandard.ZstdDecompressor().stream_reader(bruto, read_across_frames=True)
        # errors="replace": o corte pode cair no meio de um caractere UTF-8.
        yield io.TextIOWrapper(leitor, encoding="utf-8", errors="replace", newline=""), bruto
