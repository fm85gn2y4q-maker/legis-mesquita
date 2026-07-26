"""Testes da camada de leitura, sobre um acervo mínimo montado no teste.

O banco é construído aqui, com o mesmo esquema da ingestão, para que estes
testes não dependam de ter rodado a coleta — e para que o caso central fique
explícito: a Lei 460/2008 existe, responde à busca, e foi revogada em 2019.
"""

from __future__ import annotations

import sqlite3

import pytest

from legis.acervo import Acervo, montar_consulta_fts, numero_formatado, por_extenso
from legis.ingestao import ESQUEMA, INDICES

ATOS = [
    # id, tipo, numero, ano, data, ementa, texto
    ("lei-460-2008", "lei", 460, 2008, "2008-06-18",
     "Cria o Conselho Municipal de Transportes e dá outras providências.",
     "Art. 1º Fica criado o Conselho Municipal de Transportes de Mesquita, "
     "órgão colegiado de caráter consultivo."),
    ("lei-1106-2019", "lei", 1106, 2019, "2019-01-11",
     "Revoga a Lei Municipal nº 460 de 18 de junho de 2008.",
     "Art. 1º Fica revogada na íntegra a Lei Municipal nº 460 de 18 de junho de "
     "2008, que Cria o Conselho Municipal de Transportes."),
    ("decreto-3128-2022", "decreto", 3128, 2022, "2022-01-03",
     "Dispõe sobre a abertura do exercício financeiro de 2022.",
     "Art. 1º Fica aberto o orçamento para o exercício financeiro de 2022 dos "
     "órgãos da administração direta."),
]


@pytest.fixture
def acervo(tmp_path):
    caminho = tmp_path / "teste.sqlite"
    conexao = sqlite3.connect(caminho)
    conexao.executescript(ESQUEMA)
    for identidade, tipo, numero, ano, data, ementa, texto in ATOS:
        conexao.execute(
            "INSERT INTO atos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (identidade, tipo, numero, ano, data, ementa, "portal", "Poder Executivo",
             texto, len(texto), f"Leis/{ano}/x.pdf", 1, 1, "diario_oficial",
             "00670", "2019-01-11", "https://exemplo/x.pdf", "ok"),
        )
        conexao.execute("INSERT INTO paginas VALUES (?,?,?,?)",
                        (identidade, 1, 1, texto))
    conexao.execute(
        "INSERT INTO referencias VALUES (?,?,?,?,?,?,?,?,?)",
        ("lei-1106-2019", "revoga", "lei", 460, 2008, "lei-460-2008", "municipal",
         "total",
         "Fica revogada na íntegra a Lei Municipal nº 460 de 18 de junho de 2008"),
    )
    conexao.execute(
        "INSERT INTO referencias VALUES (?,?,?,?,?,?,?,?,?)",
        ("lei-1106-2019", "revoga", "decreto", 3128, 2022, "decreto-3128-2022",
         "municipal", "parcial",
         "Fica revogado o artigo 5º do Decreto nº 3.128 de 03 de janeiro de 2022"),
    )
    # O mesmo decreto recebe também uma alteração: é o caso do Plano Diretor,
    # que tem revogação parcial E alterações posteriores.
    conexao.execute(
        "INSERT INTO referencias VALUES (?,?,?,?,?,?,?,?,?)",
        ("lei-1106-2019", "altera", "decreto", 3128, 2022, "decreto-3128-2022",
         "municipal", "parcial",
         "Dá nova redação ao artigo 2º do Decreto nº 3.128 de 03 de janeiro de 2022"),
    )
    conexao.execute("INSERT INTO acervo_info VALUES ('resumo', '{}')")
    conexao.executescript(INDICES)
    conexao.commit()
    conexao.close()
    return Acervo(caminho)


def test_busca_na_ementa_sem_acento(acervo):
    """"exercicio" tem de achar "exercício": ninguém digita acento na pergunta."""
    achados, _, _ = acervo.pesquisar("exercicio financeiro")
    assert [a.id for a in achados] == ["decreto-3128-2022"]


def test_a_busca_por_ementa_nao_alcanca_o_corpo_do_ato(acervo):
    """As duas buscas são separadas de propósito, e a separação tem de valer.

    "orçamento" está no artigo do decreto, não na sua ementa. Se a busca por
    ementa o devolvesse, o modelo diria "consta da ementa" sobre um texto que
    está no corpo — e as duas coisas pesam diferente numa peça.
    """
    por_ementa, _, _ = acervo.pesquisar("orcamento")
    assert por_ementa == []
    no_corpo, _, _ = acervo.pesquisar_texto("orcamento")
    assert [p.ato.id for p in no_corpo] == ["decreto-3128-2022"]


def test_busca_no_corpo_devolve_pagina(acervo):
    passagens, _, _ = acervo.pesquisar_texto("colegiado consultivo")
    assert len(passagens) == 1
    assert passagens[0].ato.id == "lei-460-2008"
    assert passagens[0].pagina == 1
    assert "colegiado" in passagens[0].termos


def test_pergunta_inteira_nao_zera_o_resultado(acervo):
    """A pergunta chega como frase; as palavras vazias não podem eliminá-la."""
    achados, parcial, expressao = acervo.pesquisar(
        "existe conselho de transportes no município?"
    )
    assert [a.id for a in achados] == ["lei-460-2008"]
    assert "posso" not in expressao and "existe" not in expressao


def test_correspondencia_parcial_e_declarada(acervo):
    achados, parcial, _ = acervo.pesquisar("conselho transportes saneamento")
    assert achados and parcial is True


def test_vigencia_aponta_a_revogacao(acervo):
    situacao = acervo.vigencia("lei-460-2008")
    assert "INTEGRAL" in situacao["situacao_no_acervo"]
    assert situacao["revogado_integralmente_por"][0]["id"] == "lei-1106-2019"
    assert "460" in situacao["revogado_por"][0]["trecho_que_indica"]


def test_revogacao_de_artigo_nao_mata_a_norma(acervo):
    """"Fica revogado o artigo 5º do Decreto 3.128" não revoga o Decreto 3.128.

    Achatar as duas coisas em "revogado" declararia morta uma norma que não foi
    revogada — e o trecho citado pareceria confirmar.
    """
    situacao = acervo.vigencia("decreto-3128-2022")
    assert "PARCIAL" in situacao["situacao_no_acervo"]
    assert "INTEGRAL" not in situacao["situacao_no_acervo"]
    assert situacao["revogado_integralmente_por"] == []
    assert situacao["revogado_parcialmente_por"][0]["id"] == "lei-1106-2019"


# Os textos de `situacao_no_acervo` são o que o modelo lê como limite
# autoritativo. Qualquer um deles que afirme o estado da norma — "subsiste",
# "continua valendo", "não reflete a redação em vigor" — dá ao advogado uma
# garantia que esta base não pode dar. O acervo prova o que ENCONTROU.
AFIRMACOES_PROIBIDAS = (
    "está em vigor", "continua em vigor", "continua valendo", "subsiste",
    "permanece vigente", "é a redação atual", "reflete a redação em vigor",
)


@pytest.mark.parametrize("identificador", [
    "lei-460-2008",        # revogação integral
    "decreto-3128-2022",   # revogação parcial
    "lei-1106-2019",       # nada localizado
])
def test_vigencia_nunca_afirma_o_estado_da_norma(acervo, identificador):
    situacao = acervo.vigencia(identificador)
    frase = situacao["situacao_no_acervo"].lower()
    for proibida in AFIRMACOES_PROIBIDAS:
        assert proibida not in frase, f"{identificador}: afirmou {proibida!r}"


def test_sem_revogacao_localizada_nao_e_certidao_de_vigencia(acervo):
    situacao = acervo.vigencia("lei-1106-2019")
    assert "Nenhuma revogação" in situacao["situacao_no_acervo"]
    assert "não equivale a vigência" in situacao["situacao_no_acervo"]
    assert "tácita" in situacao["advertencia"]


def test_revogacao_parcial_e_alteracao_aparecem_juntas(acervo):
    """As situações não são excludentes.

    O Plano Diretor de Mesquita tem revogação parcial (§ 5º do art. 128) e
    doze alterações posteriores. Contar só uma delas é meia resposta.
    """
    situacao = acervo.vigencia("decreto-3128-2022")["situacao_no_acervo"]
    assert "PARCIAL" in situacao
    assert "ALTERAÇÃO" in situacao
    assert "não foi localizada revogação expressa" in situacao


def test_o_ato_revogador_declara_o_que_revogou(acervo):
    situacao = acervo.vigencia("lei-1106-2019")
    feitas = situacao["o_que_este_ato_faz_com_outros"]
    assert {(f["relacao"], f["id_do_alvo"], f["extensao"]) for f in feitas} == {
        ("revoga", "lei-460-2008", "total"),
        ("revoga", "decreto-3128-2022", "parcial"),
        ("altera", "decreto-3128-2022", "parcial"),
    }


def test_citacao_no_formato_de_peca(acervo):
    ato = acervo.obter("lei-1106-2019")
    assert ato.citacao == "Mesquita/RJ, Lei nº 1.106, de 11 de janeiro de 2019"


def test_localizar_pela_referencia_que_o_advogado_tem(acervo):
    assert [a.id for a in acervo.por_numero("lei", 460, 2008)] == ["lei-460-2008"]
    assert [a.id for a in acervo.por_numero("lei", 460, None)] == ["lei-460-2008"]
    assert acervo.por_numero("decreto", 9999, None) == []


def test_expressao_exata_entre_aspas_e_preservada():
    assert montar_consulta_fts('taxa "coleta de lixo"') == '"coleta de lixo" AND "taxa"'


def test_consulta_so_de_palavras_vazias_nao_fica_em_branco():
    assert montar_consulta_fts("o que é isso") != ""


def test_numero_e_data_no_formato_juridico():
    assert numero_formatado(1106) == "1.106"
    assert numero_formatado(46) == "46"
    assert por_extenso("2019-01-11") == "11 de janeiro de 2019"
    assert por_extenso(None) is None
