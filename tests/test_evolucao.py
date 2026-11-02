import json

from aberturas.evolucao import familia, resumir, salvar


def test_nomes_antigos_viram_a_familia_atual():
    assert familia("Philidor Defense #3") == "Philidor Defense"
    assert familia("King's Gambit Accepted, Fischer Defense") == "King's Gambit Accepted"
    assert familia("Queen's Gambit Refused") == "Queen's Gambit Declined"
    assert familia("Petrov's Defense") == "Russian Game"
    assert familia("Sicilian Defense") == "Sicilian Defense"


def mes(pasta, nome, linhas):
    (pasta / f"{nome}.json").write_text(json.dumps({"mes": nome, "familias": linhas}), encoding="utf-8")


def test_soma_por_ano_e_junta_nomes(tmp_path, monkeypatch):
    monkeypatch.setattr("aberturas.evolucao.PARTIDAS_MINIMAS", 10)
    mes(tmp_path, "2019-05", [
        ["Philidor Defense #2", "blitz", 1400, 3, 1, 2, 3.0],
        ["Sicilian Defense", "blitz", 1400, 50, 10, 40, 50.0],
    ])
    mes(tmp_path, "2020-01", [["Philidor Defense", "blitz", 1400, 1, 0, 1, 1.0]])
    mes(tmp_path, "2020-02", [
        ["Philidor Defense", "blitz", 1400, 1, 0, 0, 0.5],
        ["Rara", "blitz", 1400, 0, 0, 1, 0.5],
        ["Sicilian Defense", "correspondence", 1400, 1, 0, 0, 0.5],
    ])
    r = resumir(tmp_path)
    assert r["anos"] == [2019, 2020] and r["ate"] == "2020-02"
    blitz, f1400 = r["ritmos"].index("blitz"), r["faixas"].index(1400)
    assert r["total"][blitz][f1400] == [106, 4]
    assert r["aberturas"]["Philidor Defense"][blitz][f1400] == [6, 3]
    # "Rara" só aparece em 2020, que tem poucas partidas para contar: fica de fora.
    assert "Rara" not in r["aberturas"]
    salvar(r, tmp_path / "evolucao.json")
    assert json.loads((tmp_path / "evolucao.json").read_text(encoding="utf-8")) == r
