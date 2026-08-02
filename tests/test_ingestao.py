"""Testes do parser.

As cadeias usadas aqui **não são inventadas**: cada uma foi copiada de um PDF
do acervo. Um teste sintético provaria que o regex casa o que eu imaginei; o
que precisa ser provado é que ele casa o que a Prefeitura de fato publicou —
com os treze espaços de recuo, o asterisco de republicação e o mês em
minúscula que apareceram lá.
"""

from __future__ import annotations

import pytest

from legis.ingestao import (
    CABECALHO,
    extrair_ementa,
    extrair_referencias,
    da_serie_municipal,
    limpar_ementa_do_portal,
    normalizar_tipo,
    numero_inteiro,
    parece_cabecalho,
    teto_da_serie,
)


def cabecalhos(texto: str):
    return [a for a in CABECALHO.finditer(texto) if parece_cabecalho(texto, a)]


RODAPE = "\nO PREFEITO MUNICIPAL DE MESQUITA, no uso de suas atribuições\nArt. 1º - Fica\n"

# Formas reais de cabeçalho, uma por variação encontrada no acervo.
FORMAS = [
    ("LEI Nº 001,DE 13 DE FEVEREIRO DE 2001.", "lei", 1, 2001),
    ("LEI Nº 013, DE 07 DE maio DE 2001.", "lei", 13, 2001),
    ("Lei nº 005 de 05 de março de 2001.", "lei", 5, 2001),
    ("LEI Nº 046, DE 1º DE NOVEMBRO DE 2001.", "lei", 46, 2001),
    ("LEI Nº 100 / 2002 de 25 de abril de 2002.", "lei", 100, 2002),
    ("LEI Nº 123/2002 de 31 de outubro de 2002.", "lei", 123, 2002),
    ("LEI N.º 128 – DE 11 DE NOVEMBRO DE 2002", "lei", 128, 2002),
    ("LEI Nº 134 – DE 10 DE JANEIRO DE 2003.", "lei", 134, 2003),
    ("*LEI Nº 688 DE 16 DE JUNHO DE 2011.", "lei", 688, 2011),
    ("LEI Nº 1.284, DE 17 DE ABRIL 2026", "lei", 1284, 2026),
    ("DECRETO Nº 196 – DE 26 DE MARÇO DE 2004", "decreto", 196, 2004),
    ("DECRETO Nº 1999, 6 DE JANEIRO DE 2017", "decreto", 1999, 2017),
    ("DECRETO Nº 3.128, DE 03 DE JANEIRO DE 2022", "decreto", 3128, 2022),
    ("             LEI Nº 006, DE 05 DE MARÇO DE 2001.", "lei", 6, 2001),
    ("LEI COMPLEMENTAR Nº 35 DE 20 DE MAIO DE 2020", "lei_complementar", 35, 2020),
    # Formas que só apareceram quando fui recuperar os atos sem texto.
    ("Decreto nº. 060 de 25 de Janeiro de 2002.", "decreto", 60, 2002),
    ("DECRETO Nº. 111, - DE 21 DE NOVEMBRO DE 2002.", "decreto", 111, 2002),
    ("( * ) LEI Nº 110 DE 28 DE JUNHO DE 2002.", "lei", 110, 2002),
    ("DECRETO N.º162 – DE - 18 DE SETEMBRO DE 2003", "decreto", 162, 2003),
    ("DECRETO N. º 150 - DE 02 DE JUNHO DE 2003.", "decreto", 150, 2003),
    ("LEI Nº 058 DE DEZEMBRO DE 2001.", "lei", 58, 2001),
    ("LEI ORDINÁRIA Nº 1131 DE 18 DE JULHO DE 2019.", "lei", 1131, 2019),
    ("LEI DE Nº 1111 DE 04 DE JANEIRO DE 2019", "lei", 1111, 2019),
    ("Decreto nº, 215 de 13 de setembro de 2004.", "decreto", 215, 2004),
    # A grafia do mês está errada na origem, nestes cinco. O ato existe.
    ("DECRETO Nº455, DE 19 DE OUTRUBRO DE 2006", "decreto", 455, 2006),
    ("*LEI Nº  638 DE 02 DE AGOSOTO DE 2010.", "lei", 638, 2010),
    ("DECRETO 3.406, DE 28 DE FEVEIRO DE 2023", "decreto", 3406, 2023),
    ("LEI Nº 293 DE 21 DEJUNHO DE 2006.", "lei", 293, 2006),
    ("DECRETO Nº 103, DE 08 DE OUTUIBRO DE 2002.", "decreto", 103, 2002),
    # Erro que nem a raiz de três letras sobrevive: SETEMBRO sem o "E". Aqui
    # quem identifica o mês é a moldura `DE <dia> DE … DE <ano>`.
    ("DECRETO Nº 3.293, DE 02 DE STEMBRO DE 2022", "decreto", 3293, 2022),
]


@pytest.mark.parametrize("linha,tipo,numero,ano", FORMAS)
def test_reconhece_as_formas_reais(linha, tipo, numero, ano):
    achados = cabecalhos(linha + RODAPE)
    assert len(achados) == 1, f"não reconheceu: {linha!r}"
    achado = achados[0]
    assert normalizar_tipo(achado.group(1)) == tipo
    assert numero_inteiro(achado.group(2)) == numero
    assert int(achado.group(6) or achado.group(3)) == ano


# O caso que motiva o parser inteiro: a citação tem a MESMA forma do cabeçalho.
CITACOES = [
    'Art. 1º Fica revogada na íntegra a Lei Municipal nº 460 de 18 de junho de '
    '2008, que "Cria o Conselho Municipal de Transportes e dá outras providências".',
    "conforme a Lei nº 4.320 de 17 de março de 1964 e a Lei Complementar nº 101/2000",
    "Suprime-se o inciso IV, do artigo 17 da Lei Municipal nº 53 de 13 de dezembro de 2001",
]


@pytest.mark.parametrize("texto", CITACOES)
def test_nao_confunde_citacao_com_cabecalho(texto):
    assert cabecalhos(texto + RODAPE) == []


def test_citacao_jogada_para_o_inicio_da_linha_pela_quebra_do_pdf():
    """A quebra de linha do PDF põe a citação começando a linha.

    O critério de posição sozinho aceitaria; o de cauda curta rejeita, porque
    a oração continua depois da data.
    """
    texto = (
        "Art. 1º Fica revogada na íntegra a\n"
        'Lei Municipal nº 460 de 18 de junho de 2008, que "Cria o Conselho'
        ' Municipal de Transportes".\n' + RODAPE
    )
    assert cabecalhos(texto) == []


def test_citacao_desmontada_palavra_por_palavra_nao_e_cabecalho():
    """O PDF justificado põe cada palavra numa linha.

    `Lei \\nnº048, \\nde \\n21 \\nde \\nnovembro de 2001` tem forma de cabeçalho,
    começa uma linha e tem cauda curta — passa por todos os critérios de posição.
    O que a denuncia é gastar quatro quebras de linha; cabeçalho legítimo gasta
    no máximo uma, quando a diagramação o parte.
    """
    texto = ("Regulamenta dispositivo da\nLei \nnº048, \nde \n21 \nde \nnovembro"
             " de 2001.\n" + RODAPE)
    assert cabecalhos(texto) == []


def test_cabecalho_partido_em_duas_linhas_e_aceito():
    """`LEI COMPLEMENTAR` numa linha e o resto na seguinte é legítimo.

    Proibir a quebra de linha para matar o caso acima custou 26 atos, entre eles
    sete leis complementares. O critério é quantas quebras, não se há.
    """
    texto = "LEI COMPLEMENTAR\nNº 018 DE 11 DE DEZEMBRO DE 2015.\n" + RODAPE
    achados = cabecalhos(texto)
    assert len(achados) == 1
    assert normalizar_tipo(achados[0].group(1)) == "lei_complementar"
    assert numero_inteiro(achados[0].group(2)) == 18


def test_rotulo_que_abre_o_ato_nao_e_continuacao_de_frase():
    """A linha anterior ao cabeçalho costuma ser a fórmula de promulgação.

    `PROMULGO A SEGUINTE LEI:` e `Republicado:` terminam em dois-pontos e ABREM
    o ato. Tratá-los como frase inacabada custou o bloco das Leis 84 a 104/2002.
    """
    for antes in ("ORIGEM, PROMULGO A SEGUINTE LEI:", "Republicado:", ","):
        texto = f"{antes}\nLEI Nº 100 / 2002 de 25 de abril de 2002.\n" + RODAPE
        assert len(cabecalhos(texto)) == 1, antes


def test_frase_inacabada_antes_do_cabecalho_recusa():
    texto = ("Suprime-se o inciso IV, do artigo 17 da\n"
             "Lei Municipal nº 53 de 13 de dezembro de 2001.\n" + RODAPE)
    assert cabecalhos(texto) == []


def test_palavra_qualquer_nao_passa_por_mes():
    """`Decreto Nº 1.994/2017 \\nGABINETE` engolia o GABINETE como mês.

    A moldura é o que separa: `GABINETE` vinha seguido de "DO PREFEITO", e não
    de um ano. `STEMBRO`, entre um dia e 2022, está na posição do mês e em
    nenhuma outra — por isso passa, mesmo sem conter raiz reconhecível.
    """
    achados = cabecalhos("Decreto Nº 1.994/2017 \nGABINETE DO PREFEITO\n" + RODAPE)
    assert len(achados) == 1
    assert "GABINETE" not in achados[0].group(0)
    assert numero_inteiro(achados[0].group(2)) == 1994

    emoldurado = cabecalhos(
        "DECRETO Nº 3.293, DE 02 DE STEMBRO DE 2022\n" + RODAPE)
    assert len(emoldurado) == 1
    assert emoldurado[0].group(5).upper() == "STEMBRO"


def test_mes_com_grafia_errada_na_origem_ainda_data_o_ato():
    from legis.ingestao import _data_iso

    assert _data_iso("19", "OUTRUBRO", "2006") == "2006-10-19"
    assert _data_iso("02", "AGOSOTO", "2010") == "2010-08-02"
    assert _data_iso("21", "DEJUNHO", "2006") == "2006-06-21"
    assert _data_iso("10", "GABINETE", "2017") is None


def test_cauda_com_palavra_nao_e_cabecalho():
    """Decisão administrativa publicada no Diário, começando a linha.

    `LEI MUNICIPAL No 017/2014, COM REDAÇÃO DA LEI` vem logo abaixo do cabeçalho
    da página — que não é frase inacabada — e tem cauda de 20 caracteres, dentro
    do limite de comprimento. Criaria uma "Lei 17/2014" com 15.884 caracteres de
    texto de 2026. O que a denuncia é a cauda ter PALAVRA: depois da data, um
    cabeçalho traz ponto, ou nada.
    """
    texto = ("Mesquita, Quinta-Feira, 30 de julho de 2026 | Nº 02494.\n"
             "LEI MUNICIPAL No 017/2014, COM REDAÇÃO DA LEI\n"
             "COMPLEMENTAR No 018/2015. DECISÃO\n" + RODAPE)
    assert cabecalhos(texto) == []


def test_cauda_de_pontuacao_continua_valendo():
    for linha in ("LEI Nº 1.290, DE 30 DE JULHO DE 2026",
                  "LEI Nº 1.290, DE 30 DE JULHO DE 2026.",
                  "DECRETO Nº 3.918, DE 28 DE JULHO DE 2026 ."):
        assert len(cabecalhos(linha + "\n" + RODAPE)) == 1, linha


def test_linha_solta_sem_corpo_de_ato_nao_e_cabecalho():
    """Anexo que lista normas revogadas: posição boa, mas não há ato abaixo."""
    texto = (
        "ANEXO I - NORMAS REVOGADAS\n"
        "LEI Nº 500 DE 10 DE MAIO DE 2010\n"
        "LEI Nº 501 DE 11 DE MAIO DE 2010\n"
    )
    assert cabecalhos(texto) == []


def test_pagina_de_diario_com_dois_atos():
    """O defeito que o parser existe para evitar.

    `Lei_1106_2019.pdf` traz, na mesma página, a Lei 1.106 e o Decreto 2.430.
    Indexar o arquivo inteiro sob o nome do arquivo faria a Lei dispor sobre
    orçamento.
    """
    texto = (
        "ATOS DO PODER EXECUTIVO\n"
        "LEI Nº 1106 DE 11 DE JANEIRO DE 2019.\n"
        "Autor: Poder Executivo\n"
        "Revoga a Lei Municipal nº 460 de 18 de junho de 2008.\n"
        "A CÂMARA MUNICIPAL DE MESQUITA aprova e EU sanciono a seguinte Lei:\n"
        "Art. 1º Fica revogada na íntegra a Lei Municipal nº 460 de 18 de junho"
        " de 2008.\n"
        "DECRETO Nº 2430 DE  09 DE JANEIRO DE 2019.\n"
        "“DISPÕE SOBRE A PUBLICAÇÃO DO QUADRO DE DETALHAMENTO ORÇAMENTÁRIO 2019.”\n"
        "O PREFEITO MUNICIPAL DE MESQUITA, no uso das atribuições legais\n"
        "DECRETA:\n"
        "Art. 1° - fica publicado o Quadro de Detalhamento da Despesa.\n"
    )
    achados = cabecalhos(texto)
    assert [normalizar_tipo(a.group(1)) for a in achados] == ["lei", "decreto"]
    assert [numero_inteiro(a.group(2)) for a in achados] == [1106, 2430]


def test_ementa_para_no_inicio_do_ato():
    corpo = (
        "\nAutor: Poder Executivo\n"
        "Revoga a Lei Municipal nº 460 de 18 de junho de 2008, que “Cria o "
        "Conselho Municipal de Transportes e dá outras providências”.\n"
        "A CÂMARA MUNICIPAL DE MESQUITA, por seus representantes legais aprova\n"
        "Art. 1º Fica revogada na íntegra a Lei Municipal nº 460.\n"
    )
    ementa = extrair_ementa(corpo)
    assert ementa.startswith("Revoga a Lei Municipal nº 460")
    assert "CÂMARA" not in ementa
    assert "Art. 1" not in ementa


def test_ementa_do_modelo_antigo_ignora_o_bloco_de_publicacao():
    corpo = (
        "\nPUBLICADO\nJornal: D.O.\nData: 07/05/01\nPágina: 02\n"
        "Dispõe sobre a Criação da Escola Municipal Professor Samuel.\n"
        "O PREFEITO DO MUNICÍPIO DE MESQUITA:\n"
    )
    ementa = extrair_ementa(corpo)
    assert "Jornal" not in ementa and "PUBLICADO" not in ementa
    assert ementa.startswith("Dispõe sobre a Criação")


def test_extrai_revogacao_com_ano():
    achados = extrair_referencias(
        "Art. 1º Fica revogada na íntegra a Lei Municipal nº 460 de 18 de junho"
        " de 2008, que Cria o Conselho."
    )
    assert ("revoga", "lei", 460, 2008) in [a[:4] for a in achados]


def test_extrai_revogacao_sem_ano():
    achados = extrair_referencias("Ficam revogados os arts. 3º e 4º da Lei nº 828.")
    assert ("revoga", "lei", 828, None) in [a[:4] for a in achados]


def test_extrai_alteracao_e_regulamentacao():
    relacoes = {
        a[0] for a in extrair_referencias(
            "Altera a Lei nº 1.052/2017 e regulamenta o Decreto nº 2.430/2019."
        )
    }
    assert {"altera", "regulamenta"} <= relacoes


def test_numero_de_quatro_digitos_na_citacao_nao_e_truncado():
    """O defeito que a auditoria do acervo real encontrou.

    "Decreto nº 1059" era lido como 105 e "Decreto nº 2529" como 252 — e o ato
    de número truncado ficava marcado como revogado. Norma viva declarada
    morta, com trecho de aparência impecável sustentando o engano.
    """
    achados = extrair_referencias(
        "Art. 49. Revogam-se as disposições em contrário, em especial o "
        "Decreto nº 1059, de 11 de novembro de 2011."
    )
    assert [a[:4] for a in achados] == [("revoga", "decreto", 1059, 2011)]

    achados = extrair_referencias(
        "revogando-se as disposições em contrário, notadamente as do Decreto "
        "nº 2529 de 05 de julho de 2019."
    )
    assert [a[:4] for a in achados] == [("revoga", "decreto", 2529, 2019)]


def test_clausula_de_estilo_sozinha_nao_revoga_a_norma_vizinha():
    """"Revogam-se as disposições em contrário" é fecho de quase todo ato.

    Sem conector de ressalva, a norma citada em seguida é apenas uma citação
    na vizinhança — ligá-las inventaria uma revogação.
    """
    achados = extrair_referencias(
        "Art. 5º Este Decreto entra em vigor na data de sua publicação, "
        "revogadas as disposições em contrário, observado o Decreto nº 105 "
        "de 12 de março de 2002."
    )
    assert [a for a in achados if a[0] == "revoga"] == []


def test_ressalva_expressa_depois_da_clausula_vale_revogacao():
    achados = extrair_referencias(
        "revogadas as disposições em contrário, especialmente o Decreto nº063, "
        "de 25 de fevereiro de 2002."
    )
    assert ("revoga", "decreto", 63, 2002) in [a[:4] for a in achados]


def test_citacao_antes_da_clausula_de_estilo_vale_revogacao():
    achados = extrair_referencias(
        "revogando o Decreto nº 792 de 10 de maio de 2009 e as demais "
        "disposições em contrário."
    )
    assert ("revoga", "decreto", 792, 2009) in [a[:4] for a in achados]


def test_a_mesma_revogacao_na_ementa_e_no_artigo_conta_uma_vez():
    achados = extrair_referencias(
        "Dispõe sobre a revogação do Decreto Municipal nº 741 de 22 de maio de "
        "2009. O PREFEITO DECRETA: Art. 1º Fica revogado integralmente o "
        "Decreto Municipal nº 741 de 22 de maio de 2009."
    )
    revogacoes = [a[:4] for a in achados if a[0] == "revoga"]
    assert revogacoes == [("revoga", "decreto", 741, 2009)]


def test_revogacao_de_dispositivo_e_marcada_como_parcial():
    achados = extrair_referencias(
        "Art. 3º - Fica revogado o artigo 93 do Decreto nº 127, de 12 de "
        "fevereiro de 2003."
    )
    assert [(a[0], a[2], a[4]) for a in achados] == [("revoga", 127, "parcial")]


def test_revogar_todos_os_artigos_e_revogar_a_lei():
    """Caso real: "REVOGA TODOS OS ARTIGOS DA LEI Nº 899/2015".

    A menção a "artigos" é a forma de dizer "tudo". Classificar como parcial
    faria a ferramenta afirmar que a norma subsiste — o oposto do que houve.
    """
    achados = extrair_referencias(
        "LEI Nº 939 DE 02 DE DEZEMBRO DE 2015. REVOGA TODOS OS ARTIGOS DA LEI "
        "Nº 899 DE 27 DE MAIO DE 2015 E DÁ OUTRAS PROVIDÊNCIAS."
    )
    assert [(a[0], a[2], a[4]) for a in achados] == [("revoga", 899, "total")]


def test_revogacao_integral_dita_de_outras_formas():
    for frase, esperado in [
        ("Fica revogado integralmente o Decreto nº 741 de 22 de maio de 2009.", "total"),
        ("Fica revogada na íntegra a Lei nº 460 de 18 de junho de 2008.", "total"),
        ("Fica revogado o § 5º do Art. 128 da Lei nº 355 de 25 de outubro de 2006.",
         "parcial"),
    ]:
        achados = extrair_referencias(frase)
        assert [a[4] for a in achados if a[0] == "revoga"] == [esperado], frase


def test_revogacao_da_norma_inteira_e_marcada_como_total():
    achados = extrair_referencias(
        "Art. 1º Fica revogada na íntegra a Lei Municipal nº 460 de 18 de "
        "junho de 2008."
    )
    assert [(a[0], a[2], a[4]) for a in achados] == [("revoga", 460, "total")]


def test_ementa_do_portal_perde_o_prefixo_redundante():
    assert limpar_ementa_do_portal(
        "Lei 1106 - Revoga a Lei Municipal nº 460 de 18 de junho de 2008."
    ) == "Revoga a Lei Municipal nº 460 de 18 de junho de 2008."
    # A marca de republicação fica: diz que o texto saiu duas vezes no Diário.
    assert limpar_ementa_do_portal(
        "Decreto 2430 - Republicado - DISPÕE SOBRE O QUADRO DE DETALHAMENTO."
    ) == "Republicado - DISPÕE SOBRE O QUADRO DE DETALHAMENTO."
    # Ementa que já vem limpa não pode ser mutilada.
    assert limpar_ementa_do_portal(
        "Dispõe sobre a estrutura administrativa da Prefeitura."
    ) == "Dispõe sobre a estrutura administrativa da Prefeitura."


# Catálogo de mentirinha com a forma do real: a série municipal chega a 1.288
# (leis) e 3.917 (decretos), e a Lei Complementar vem rotulada como "Lei".
CATALOGO = {
    ("lei", 1288, 2026): {}, ("lei", 460, 2008): {},
    ("decreto", 3917, 2026): {}, ("decreto", 2430, 2019): {},
    ("lei", 17, 2014): {},  # é a LC 17/2014, catalogada como Lei
}

# Os cinco atos que de fato entraram no acervo antes deste filtro existir.
FANTASMAS = [
    ("lei", 14133, 2021),        # Lei federal de Licitações
    ("lei", 10520, 2002),        # Lei federal do Pregão
    ("lei", 14434, 2022),        # Lei federal do piso da enfermagem
    ("decreto", 10282, 2020),    # Decreto federal
    ("decreto", 46984, 2020),    # Decreto estadual do Rio de Janeiro
]


@pytest.mark.parametrize("chave", FANTASMAS)
def test_norma_de_fora_do_municipio_nao_entra_como_ato_municipal(chave):
    """Atribuir lei federal ao Município não é imprecisão: é erro de competência.

    O servidor citaria "Mesquita/RJ, Lei nº 14.133, de 1º de abril de 2021".
    """
    assert not da_serie_municipal(chave, teto_da_serie(CATALOGO), CATALOGO)


def test_complementar_federal_tem_numero_baixo_e_escapa_do_teto():
    """A LC 116/2003 cabe na faixa municipal — só a lista `FEDERAIS` a pega."""
    tetos = teto_da_serie(CATALOGO)
    assert not da_serie_municipal(("lei_complementar", 116, 2003), tetos, CATALOGO)
    assert not da_serie_municipal(("lei_complementar", 173, 2020), tetos, CATALOGO)


@pytest.mark.parametrize("chave", [
    ("lei", 460, 2008),               # está no catálogo
    ("decreto", 2430, 2019),          # está no catálogo
    ("lei_complementar", 17, 2014),   # catalogado como Lei 17/2014
    ("decreto", 2263, 2018),          # fora do catálogo, mas dentro da série
    ("lei_complementar", 61, 2026),   # a série de LC do Município chega a 61
])
def test_ato_municipal_legitimo_continua_entrando(chave):
    """O filtro não pode cobrar ingresso de quem é de casa.

    60 atos do acervo aparecem em página de Diário e não constam do catálogo do
    portal — são municipais e precisam continuar entrando.
    """
    assert da_serie_municipal(chave, teto_da_serie(CATALOGO), CATALOGO)


def test_teto_vem_do_catalogo_e_nao_de_constante_escolhida():
    tetos = teto_da_serie(CATALOGO)
    assert tetos["lei"] == 1288 + 50
    assert tetos["decreto"] == 3917 + 50
    # Sem série própria no catálogo, a complementar herda o teto da lei.
    assert tetos["lei_complementar"] == tetos["lei"]


CORPO_DO_ATO = (
    "LEI Nº 1.290, DE 30 DE JULHO DE 2026\n"
    "“Dispõe sobre alterar o nome do logradouro público Rua Amazonas”.\n"
    "A CÂMARA MUNICIPAL DE MESQUITA aprovou e eu sanciono a seguinte Lei:\n"
    "Art. 1º - Fica alterado o nome da Rua Amazonas, no Bairro Coreia.\n"
    "Art. 2º - Esta Lei entra em vigor na data de sua publicação.\n"
    "Mesquita, 30 de julho de 2026.\n"
    "MAROTTO MIRANDA\nPrefeito\n"
)


def test_ato_termina_onde_comeca_outro_documento():
    """Numa página de Diário o ato acaba e a edição continua.

    A Lei 1.290/2026 renomeia uma rua e carregava 24.108 caracteres — 97% deles
    extratos de ata, portarias e decisões de IPTU que vieram atrás na mesma
    edição. Ela responderia a uma busca por "registro de preços".
    """
    from legis.ingestao import fim_do_ato

    for alheio in ("EXTRATO DE ATA DE REGISTRO DE PREÇOS\nATA Nº 09/2026\n",
                   "PORTARIA Nº 453/2026\nAltera a Comissão de Fiscalização\n",
                   "DECISÃO PROCESSO - 05/5265/23\n1 - À luz dos pareceres\n",
                   "EMENTA: ISENÇÃO TRIBUTÁRIA. IPTU. IDOSO.\n"):
        inteiro = CORPO_DO_ATO + alheio
        corte = fim_do_ato(inteiro)
        assert corte is not None, alheio[:20]
        assert corte == len(CORPO_DO_ATO), alheio[:20]


def test_anexo_vem_depois_da_assinatura_e_e_do_ato():
    """O corte não pode ser na assinatura.

    `decreto-2001-2017` são 848 caracteres de ato e 190 mil de Quadro de
    Detalhamento, que vem depois de "Mesquita, <data> / Prefeito". Cortar ali
    destruiria justamente o conteúdo que o ato aprova.
    """
    from legis.ingestao import fim_do_ato

    for anexo in ("ANEXO I – CLASSIFICAÇÃO DE ATIVIDADES\nCNAE  DESCRIÇÃO\n",
                  "Anexo I – Classificação por Risco Sanitário\n",
                  "ANEXO 01\nTABELA DE MULTAS\nDESCRIÇÃO  VALOR EM UFIME\n",
                  "www.mesquita.rj.gov.br\nNº 00434.\n30  FUNDO  27.510.180,00\n"):
        assert fim_do_ato(CORPO_DO_ATO + anexo) is None, anexo[:20]


def test_palavra_solta_no_corpo_do_ato_nao_encerra():
    """O ato pode citar portaria ou edital em prosa, e isso não o encerra."""
    from legis.ingestao import fim_do_ato

    texto = (
        "DECRETO Nº 3.900, DE 1º DE JULHO DE 2026\n"
        "“Regulamenta a fiscalização de contratos”.\n"
        "O PREFEITO DO MUNICÍPIO DE MESQUITA DECRETA:\n"
        "Art. 1º - A designação de fiscal far-se-á por portaria do secretário,\n"
        "observado o edital de licitação e o contrato administrativo firmado.\n"
        "Mesquita, 1º de julho de 2026.\nJORGE MIRANDA\nPrefeito\n"
    )
    assert fim_do_ato(texto) is None


def test_numero_com_separador_de_milhar():
    assert numero_inteiro("1.284") == 1284
    assert numero_inteiro("3.128") == 3128
    assert numero_inteiro("") is None
