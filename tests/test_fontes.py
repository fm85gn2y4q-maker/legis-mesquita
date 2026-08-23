"""Onde a ingestão procura os PDFs.

As fontes saíram de `~` para o HD externo em 23/08/2026. A escolha do caminho
virou código, e código que escolhe pasta errada em silêncio já custou caro neste
projeto: uma variável sombreada fez a ingestão ler um dicionário vazio por 13
minutos, e a única pista foi a contagem de arquivos ter dado idêntica.
"""

from __future__ import annotations

import pytest

from legis import fontes


@pytest.fixture
def sem_variavel(monkeypatch):
    monkeypatch.delenv("LEGIS_FONTES", raising=False)


def test_variavel_de_ambiente_manda(monkeypatch, tmp_path):
    monkeypatch.setenv("LEGIS_FONTES", str(tmp_path))
    assert fontes.raiz_das_fontes() == tmp_path
    assert fontes.legislacao() == tmp_path / "Mesquita_Legislacao"
    assert fontes.diarios() == tmp_path / "Mesquita_Diarios_Oficiais"


def test_argumento_explicito_vence_a_variavel(monkeypatch, tmp_path):
    monkeypatch.setenv("LEGIS_FONTES", "Z:/nao-e-esta")
    assert fontes.raiz_das_fontes(str(tmp_path)) == tmp_path


def test_escolhe_a_pasta_que_existe(monkeypatch, tmp_path, sem_variavel):
    externo = tmp_path / "externo"
    (externo / fontes.LEGISLACAO).mkdir(parents=True)
    casa = tmp_path / "casa"
    (casa / fontes.LEGISLACAO).mkdir(parents=True)

    monkeypatch.setattr(fontes, "CANDIDATAS", (str(externo), str(casa)))
    assert fontes.raiz_das_fontes() == externo


def test_a_ordem_declarada_e_respeitada(monkeypatch, tmp_path, sem_variavel):
    """Qualquer das duas pastas serve para reconhecer a raiz: a de PDFs por ato
    ou a do Diário. Basta uma existir."""
    primeira = tmp_path / "primeira"
    (primeira / fontes.DIARIOS).mkdir(parents=True)
    segunda = tmp_path / "segunda"
    (segunda / fontes.LEGISLACAO).mkdir(parents=True)

    monkeypatch.setattr(fontes, "CANDIDATAS", (str(primeira), str(segunda)))
    assert fontes.raiz_das_fontes() == primeira

    monkeypatch.setattr(fontes, "CANDIDATAS", (str(segunda), str(primeira)))
    assert fontes.raiz_das_fontes() == segunda


def test_a_ordem_de_producao_poe_a_casa_na_frente(sem_variavel):
    """Invertida de propósito em 23/08/2026: o HD externo reprovou na
    conferência — 0,4 MB/s e banco corrompido — e preferi-lo mandaria a rotina
    de sábado ler de um disco que não devolve o que gravou."""
    assert fontes.CANDIDATAS[0] == "~", (
        "se o HD voltou a ser confiável, esta é a linha a trocar — e o "
        "comentário em fontes.py explica o que reconferir antes")


def test_sem_nenhuma_pasta_devolve_caminho_concreto(monkeypatch, tmp_path,
                                                    sem_variavel):
    """Para a mensagem de erro mostrar um caminho, não `None`."""
    monkeypatch.setattr(fontes, "CANDIDATAS", (str(tmp_path / "nao-existe"),))
    assert fontes.raiz_das_fontes() == tmp_path / "nao-existe"


def test_conferir_cala_quando_esta_tudo_no_lugar(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    assert fontes.conferir(tmp_path / "a", tmp_path / "b") is None


def test_conferir_nomeia_a_pasta_que_falta_e_ensina_o_conserto(tmp_path):
    """Com o HD desligado, a rotina tem de parar dizendo o quê e como.

    Sem isso ela reconstruiria o acervo a partir de pasta vazia — o que passa
    pela ingestão inteira e só é pego lá na frente, pelo diff.
    """
    presente = tmp_path / "presente"
    presente.mkdir()
    ausente = tmp_path / "sumida"
    queixa = fontes.conferir(presente, ausente)

    assert queixa is not None
    assert str(ausente) in queixa, "tem de dizer QUAL pasta falta"
    assert str(presente) not in queixa, "listar a que está lá confunde"
    assert "LEGIS_FONTES" in queixa, "tem de ensinar o conserto"
