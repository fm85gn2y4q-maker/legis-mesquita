"""Onde a ingestão procura os PDFs.

As fontes saíram de `~` e hoje vivem em raízes **diferentes**: os PDFs por ato
em `D:\\Acervos\\Mesquita_Legislacao`, e o acervo do Diário alcançável por
`~/Mesquita_Diarios_Oficiais`, que é junção para dentro do projeto
`diarios-mesquita` — e lá dentro `municipio` é outro link, para o `D:`.

A primeira versão deste módulo procurava **uma raiz comum para as duas**, e
quebrou quando elas se separaram. Cada pasta se resolve sozinha agora.

Código que escolhe pasta errada em silêncio já custou caro aqui: uma variável
sombreada fez a ingestão ler um dicionário vazio por 13 minutos, e a única
pista foi a contagem de arquivos ter dado idêntica.
"""

from __future__ import annotations

import pytest

from legis import fontes


@pytest.fixture
def sem_variavel(monkeypatch):
    monkeypatch.delenv("LEGIS_FONTES", raising=False)


def test_variavel_de_ambiente_manda_nas_duas(monkeypatch, tmp_path):
    monkeypatch.setenv("LEGIS_FONTES", str(tmp_path))
    assert fontes.legislacao() == tmp_path / "Mesquita_Legislacao"
    assert fontes.diarios() == tmp_path / "Mesquita_Diarios_Oficiais"


def test_argumento_explicito_vence_a_variavel(monkeypatch, tmp_path):
    monkeypatch.setenv("LEGIS_FONTES", "Z:/nao-e-esta")
    assert fontes.legislacao(str(tmp_path)) == tmp_path / "Mesquita_Legislacao"


def test_cada_pasta_se_resolve_na_sua_propria_raiz(monkeypatch, tmp_path,
                                                   sem_variavel):
    """O caso real de 20/09/2026: as duas em unidades diferentes.

    A versão anterior exigia raiz comum e devolvia um caminho que não abre.
    """
    externo = tmp_path / "externo"
    (externo / fontes.LEGISLACAO).mkdir(parents=True)
    casa = tmp_path / "casa"
    (casa / fontes.DIARIOS).mkdir(parents=True)

    monkeypatch.setattr(fontes, "CANDIDATAS_LEGISLACAO", (str(externo), str(casa)))
    monkeypatch.setattr(fontes, "CANDIDATAS_DIARIOS", (str(casa), str(externo)))

    assert fontes.legislacao() == externo / fontes.LEGISLACAO
    assert fontes.diarios() == casa / fontes.DIARIOS


def test_pula_a_candidata_que_nao_abre(monkeypatch, tmp_path, sem_variavel):
    """Junção pendurada responde False em `is_dir()`, e é o que salva aqui.

    `~` guarda uma junção `Mesquita_Legislacao` cujo alvo foi apagado. Se a
    busca parasse nela, a ingestão receberia um caminho que não abre.
    """
    quebrada = tmp_path / "quebrada"
    quebrada.mkdir()                      # existe, mas sem a pasta dentro
    boa = tmp_path / "boa"
    (boa / fontes.LEGISLACAO).mkdir(parents=True)

    monkeypatch.setattr(fontes, "CANDIDATAS_LEGISLACAO", (str(quebrada), str(boa)))
    assert fontes.legislacao() == boa / fontes.LEGISLACAO


def test_a_ordem_de_producao_poe_o_hd_na_frente_da_legislacao(sem_variavel):
    """Sobra em `~` seria cópia velha: achá-la antes reprocessaria o passado."""
    assert fontes.CANDIDATAS_LEGISLACAO[0] == "D:/Acervos"


def test_a_ordem_de_producao_poe_a_casa_na_frente_do_diario(sem_variavel):
    """Em `~` estão o coletor e o banco que ele usa; os PDFs vêm por link."""
    assert fontes.CANDIDATAS_DIARIOS[0] == "~"


def test_sem_nenhuma_candidata_devolve_caminho_concreto(monkeypatch, tmp_path,
                                                        sem_variavel):
    """Para a queixa mostrar um caminho, não `None`."""
    monkeypatch.setattr(fontes, "CANDIDATAS_LEGISLACAO", (str(tmp_path / "nada"),))
    assert fontes.legislacao() == tmp_path / "nada" / fontes.LEGISLACAO


def test_onde_estao_nomeia_as_duas(monkeypatch, tmp_path):
    monkeypatch.setenv("LEGIS_FONTES", str(tmp_path))
    linha = fontes.onde_estao()
    assert fontes.LEGISLACAO in linha and fontes.DIARIOS in linha


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
    assert "junção pendurada" in queixa, "é a causa mais provável hoje"
