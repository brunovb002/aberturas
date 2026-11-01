import json
from pathlib import Path

import pytest
import zstandard

from aberturas import Contagem, cabecalhos
from aberturas import contagem as modulo
from aberturas.lichess import abrir

AMOSTRA = Path(__file__).parent / "fixtures" / "amostra.pgn"


def contar(linhas):
    c = Contagem()
    for cab in cabecalhos(linhas, modulo.CHAVES):
        c.adicionar(cab)
    return c


def test_ultima_partida_sem_lances_e_ignorada():
    # A amostra termina no meio de uma partida, como quando o download é cortado.
    jogos = list(cabecalhos(AMOSTRA.read_text(encoding="utf-8").splitlines()))
    assert len(jogos) == 6
    assert jogos[0]["Opening"] == "Sicilian Defense: Najdorf Variation, English Attack"
    assert jogos[-1]["Site"].endswith("ffffffff")


def test_filtros():
    c = contar(AMOSTRA.read_text(encoding="utf-8").splitlines())
    assert c.lidas == 6
    # Fica de fora: a abandonada e a por correspondência.
    assert c.usadas == 4


def test_celulas():
    c = contar(AMOSTRA.read_text(encoding="utf-8").splitlines())
    siciliana = c.familias["Sicilian Defense", "blitz", 1400]
    assert siciliana[:3] == [1, 1, 0]
    assert siciliana[3] == pytest.approx(0.5 + 1 / (1 + 10 ** (140 / 400)))
    assert c.variantes["Sicilian Defense: Najdorf Variation", "blitz", 1400][:3] == [1, 1, 0]
    assert c.familias["Elephant Gambit", "bullet", 2400][:3] == [0, 0, 1]
    assert c.familias["Italian Game", "rapid", 800][:3] == [1, 0, 0]
    assert ("Elephant Gambit", "bullet", 2400) not in c.variantes


def test_salvar(tmp_path, monkeypatch):
    monkeypatch.setattr(modulo, "MINIMO_FAMILIA", 1)
    monkeypatch.setattr(modulo, "MINIMO_VARIANTE", 1)
    c = contar(AMOSTRA.read_text(encoding="utf-8").splitlines())
    destino = tmp_path / "2026-09.json"
    c.salvar(destino, "2026-09", completo=True)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert dados["partidas"] == 4
    assert dados["familias"][0] == ["Elephant Gambit", "bullet", 2400, 0, 0, 1, 0.41]
    assert [l[0] for l in dados["variantes"]] == ["Sicilian Defense: Najdorf Variation"]


def test_minimo_corta_aberturas_raras(tmp_path):
    c = contar(AMOSTRA.read_text(encoding="utf-8").splitlines())
    c.salvar(tmp_path / "x.json", "2026-09", completo=True)
    dados = json.loads((tmp_path / "x.json").read_text(encoding="utf-8"))
    assert dados["familias"] == [] and dados["variantes"] == []


def test_zst_cortado_no_meio(tmp_path):
    # Um bloco por cópia da amostra, para o corte pegar blocos inteiros antes dele
    # (texto repetido demais caberia num bloco só, e aí nada sairia da metade).
    comp = zstandard.ZstdCompressor().compressobj()
    partes = []
    for _ in range(200):
        partes.append(comp.compress(AMOSTRA.read_bytes()))
        partes.append(comp.flush(zstandard.COMPRESSOBJ_FLUSH_BLOCK))
    partes.append(comp.flush())
    arquivo = tmp_path / "amostra.pgn.zst"
    arquivo.write_bytes(b"".join(partes))

    with abrir(arquivo) as (linhas, bruto):
        inteiro = contar(linhas)
    assert inteiro.lidas == 6 * 200
    assert bruto.lidos == arquivo.stat().st_size

    with abrir(arquivo, limite=arquivo.stat().st_size // 2) as (linhas, bruto):
        metade = contar(linhas)
    assert 0 < metade.lidas < inteiro.lidas
    assert bruto.lidos == arquivo.stat().st_size // 2
