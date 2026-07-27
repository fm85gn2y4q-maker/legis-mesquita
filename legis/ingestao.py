"""Constrói o acervo da legislação de Mesquita a partir dos PDFs baixados.

Separa deliberadamente **coletar** de **processar**: os PDFs vieram do portal
da transparência e ficam intocados; tudo aqui é transformação determinística
sobre eles, refazível de graça quando o parser melhorar.

O problema central desta base não é extrair texto — 98% dos PDFs têm texto
nativo. É de **atribuição**. A partir de 2017 a Prefeitura passou a publicar em
Diário Oficial, e o arquivo `Lei_1106_2019.pdf` traz, na mesma página, a Lei
1.106 *e* o Decreto 2.430. Medido em amostra de 189 arquivos: 33% contêm dois
ou mais atos, um deles contém 17. Indexar o arquivo inteiro sob o nome do
arquivo faria a Lei "dispor" sobre o que o Decreto dispõe — erro de sentido,
não de precisão, e invisível para qualquer métrica de busca.

Daí a segmentação por cabeçalho de ato, e daí o cuidado do regex em não
confundir cabeçalho com citação: "ALTERA A LEI Nº 500 DE 10 DE MAIO DE 2010"
tem a mesma forma de um cabeçalho e é o oposto dele.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

MESES = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "ABRIL": 4, "MAIO": 5,
    "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10,
    "NOVEMBRO": 11, "DEZEMBRO": 12,
}

# O Município foi instalado em 1º de janeiro de 2001; o acervo começa ali.
PRIMEIRO_ANO = 2001

ROTULOS = {
    "lei": "Lei",
    "lei_complementar": "Lei Complementar",
    "decreto": "Decreto",
}

# --- o discriminador entre cabeçalho e citação -------------------------------
#
# Cabeçalho e citação têm a MESMA forma: "LEI Nº 460 DE 18 DE JUNHO DE 2008"
# abre um ato e também aparece no meio de "Fica revogada a Lei nº 460 de 18 de
# junho de 2008". Confundir os dois cria atos que não existem e atribui texto
# ao ato errado — por isso o reconhecimento é feito em duas etapas: a forma,
# aqui; e a posição, em `parece_cabecalho`.
#
# A primeira hipótese foi exigir CAIXA ALTA na espécie e no mês, dispensando a
# posição. Reprovada contra o acervo: no modelo antigo o próprio cabeçalho vem
# em caixa mista — `LEI Nº 013, DE 07 DE maio DE 2001` e até `Lei nº 005 de 05
# de março de 2001`. A caixa alta descartava 60 dos 400 primeiros arquivos,
# todos legítimos. Fica registrada a hipótese reprovada: a caixa não separa
# cabeçalho de citação nesta base.
#
# As variantes de pontuação não foram supostas — cada uma apareceu no acervo:
# `LEI Nº 134 – DE 10 DE JANEIRO DE 2003`, `LEI Nº 001,DE 13 DE…`,
# `DECRETO Nº 1999, 6 DE JANEIRO DE 2017` (sem "DE" antes do dia),
# `LEI Nº 1.284, DE 17 DE ABRIL 2026` (sem "DE" antes do ano),
# `LEI Nº 046, DE 1º DE NOVEMBRO DE 2001` (dia com ordinal),
# `LEI Nº 100 / 2002 de 25 de abril de 2002` (número com ano colado),
# `LEI N.º 128 – DE 11 DE NOVEMBRO DE 2002` e cabeçalhos recuados 13 espaços.
#
# Grupos: 1 espécie · 2 número · 3 ano na forma `123/2002` · 4 dia · 5 mês ·
# 6 ano por extenso. A data inteira é opcional porque há cabeçalho que só traz
# `LEI Nº 123/2002`; o ano, esse, é obrigatório — sem ele não há como
# identificar o ato, e o candidato é descartado.
# O cabeçalho ocupa UMA linha, e por isso o espaço interno aqui é `[ \t]`, não
# `\s`. Com `\s`, que casa quebra de linha, a extração de PDF justificado — que
# põe cada palavra numa linha — transformava a citação `Lei \nnº048, \nde \n21
# \nde \nnovembro de 2001` em cabeçalho, e o ato que a citava era cortado ali.
# A exceção é `LEI COMPLEMENTAR`, que a diagramação às vezes parte em duas.
# Espaço interno do cabeçalho. Proibir a quebra de linha aqui foi a primeira
# tentativa, e ela reprovou contra os dados: a diagramação parte cabeçalhos
# legítimos — `LEI COMPLEMENTAR` numa linha e `Nº 018 DE 11 DE DEZEMBRO DE
# 2015` na seguinte —, e a proibição custou 27 atos que tinham texto, entre
# eles sete leis complementares. O que separa o cabeçalho partido da citação
# desmontada não é haver quebra: é QUANTAS. Ver `MAXIMO_DE_QUEBRAS`.
_E = r"\s"
# O que separa os pedaços da data varia sem critério no acervo: vírgula, hífen,
# travessão, a palavra "de", barra — e combinações delas. `DECRETO N.º162 – DE -
# 18 DE SETEMBRO DE 2003` traz travessão, "DE" e hífen entre o número e o dia.
# Enumerar as combinações seria interminável; aceitar o conjunto, com o limite
# de não atravessar a linha, é o que funciona.
_SEP = rf"(?:{_E}|[,;\-–—/]|DE(?![A-Za-zÀ-ÿ]))*"
# O mês, reconhecido pela raiz de três letras e não pela grafia inteira.
#
# "Qualquer palavra de 4 a 9 letras" era permissivo demais: fazia `Decreto Nº
# 1.994/2017 \nGABINETE` engolir o GABINETE como se fosse mês. Exigir as doze
# palavras corretas foi ao outro extremo e custou cinco atos — porque quem
# publicou errou a grafia:
#
#     DE OUTRUBRO DE 2006     DE AGOSOTO DE 2010    DE FEVEIRO DE 2023
#     DEJUNHO DE 2006         DE OUTUIBRO DE 2002
#
# A raiz aceita as cinco e continua recusando GABINETE, que não contém nenhuma.
_RAIZES = "JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ"
_LETRAS = "A-Za-zÇÃÂÉÊÍÓÔÕÚÀçãâéêíóôõúà"
# Segunda alternativa, para o erro que nem a raiz sobrevive: `DE 02 DE STEMBRO
# DE 2022` — SETEMBRO sem o "E". Aqui não é a palavra que identifica o mês, é a
# MOLDURA: qualquer palavra entre um dia e um ano de quatro dígitos, ligados por
# "de", está na posição do mês e em nenhuma outra. Foi justamente a moldura que
# faltou ao `GABINETE`, que vinha seguido de "DO PREFEITO".
_MES = (rf"([A-Za-z]{{0,3}}(?:{_RAIZES})[{_LETRAS}]{{0,6}}"
        rf"|[{_LETRAS}]{{4,10}}(?={_E}*DE{_E}+\d{{4}}))")
CABECALHO = re.compile(
    # Prefixo: o que a diagramação põe antes do cabeçalho. `( * ) LEI Nº 110` e
    # `(*) LEI Nº 135` marcam republicação, como o `*` sozinho.
    r"^[ \t]*(?:\([ \t*]{0,4}\)[ \t]*)?[*\"“”'\-–—_]{0,4}[ \t]*"
    rf"(LEI\s+COMPLEMENTAR|LEI{_E}+ORDIN[ÁA]RIA|LEI|DECRETO){_E}+"
    rf"(?:MUNICIPAL{_E}+)?"
    # `LEI DE Nº 1111 DE 04 DE JANEIRO DE 2019` — o "de" antes do número.
    rf"(?:DE{_E}+)?"
    # O ponto do "número" anda: `N. º 150`, `N.º162`, `nº. 060` — e às vezes
    # vira vírgula: `Decreto nº, 215`. As quatro formas estão no acervo.
    rf"(?:N{_E}*[.,]?{_E}*[º°ᵒoO]?{_E}*[.,]?{_E}*)?"
    # O `+` no grupo do separador de milhar não é cosmético. Com `*`, a
    # primeira alternativa casava "110" de `LEI Nº 1106` e o motor aceitava
    # o resto sem data — o ato ficava sem ano e era descartado em silêncio.
    # Exigindo pelo menos um ".000", o número sem separador cai na segunda
    # alternativa, que é gulosa e lê "1106" inteiro.
    r"(\d{1,3}(?:\.\d{3})+|\d{1,5})"
    rf"(?:{_E}*/{_E}*(\d{{4}}))?"
    # Dia e mês são opcionais: há cabeçalho sem dia — `LEI Nº 058 DE DEZEMBRO
    # DE 2001` — e há cabeçalho só com `LEI Nº 123/2002`. Exigi-los custava o
    # ato inteiro, porque sem casar a data o candidato ficava sem ano.
    rf"(?:{_SEP}(\d{{1,2}}){_E}*[º°ᵒ]?(?![\d]))?"
    rf"(?:{_SEP}{_MES})?"
    rf"(?:{_SEP}(\d{{4}}))?",
    re.MULTILINE | re.IGNORECASE,
)

# Como uma linha termina quando a frase continua na seguinte. Terminando assim
# a linha anterior ao candidato, o que vem abaixo é continuação de oração —
# "Regulamenta dispositivo da" seguido de "Lei nº 048…" —, e não cabeçalho.
# Sem isto, a quebra de linha do PDF basta para inverter o sentido da citação.
# Só palavras de ligação. A primeira versão incluía `,` e `:`, e reprovou: a
# linha que antecede o cabeçalho costuma ser justamente `PROMULGO A SEGUINTE
# LEI:` ou `Republicado:` — rótulos que ABREM o ato, não frases cortadas —, e
# no Diário há linhas contendo só uma vírgula. Custou 26 atos, entre eles o
# bloco inteiro das Leis 84 a 104 de 2002.
CONTINUACAO = re.compile(
    r"\b(?:d[aeo]s?|n[ao]s?|pel[ao]s?|aos?|em|com|para|por|que|ou|e|à|às"
    r"|sobre|entre|contra|conforme|constante|revoga|altera|regulamenta)\s*$",
    re.IGNORECASE,
)

# O que o `re.IGNORECASE` deixou de fazer, a posição faz.
#
# O cabeçalho ocupa a linha sozinho: depois da data vem, no máximo, um ponto.
# A citação continua a oração — "…de 18 de junho de 2008, que "Cria o Conselho
# Municipal de Transportes…"" —, e é isso que a denuncia mesmo quando a quebra
# de linha do PDF a joga para o começo de uma linha.
RESTO_DA_LINHA = 30

# Segunda confirmação: todo ato traz a fórmula de promulgação ou o primeiro
# artigo logo abaixo do cabeçalho. Uma linha solta num anexo que liste normas
# revogadas passaria pelo critério de posição, mas não por este.
CORPO_DE_ATO = re.compile(
    r"\bArt\s*\.?\s*1|DECRETA|D\s*E\s*C\s*R\s*E\s*T\s*A|Fa[çc]o\s+saber"
    r"|sanciono|promulg|O\s+PREFEITO|A\s+C[ÂA]MARA",
    re.IGNORECASE,
)


# Um cabeçalho legítimo cabe numa linha, ou em duas quando a diagramação o
# parte (`LEI COMPLEMENTAR` / `Nº 018 DE 11 DE DEZEMBRO DE 2015`). A citação que
# o PDF justificado desmonta palavra por palavra — `Lei \nnº048, \nde \n21 \nde
# \nnovembro de 2001` — gasta quatro ou mais. A contagem de quebras separa as
# duas coisas; proibir a quebra separava mal, e custou caro.
MAXIMO_DE_QUEBRAS = 1


def parece_cabecalho(texto: str, achado: re.Match) -> bool:
    """Decide se a ocorrência abre um ato ou apenas o cita."""
    if achado.group(0).count("\n") > MAXIMO_DE_QUEBRAS:
        return False

    quebra = texto.find("\n", achado.end())
    cauda = texto[achado.end(): quebra if quebra != -1 else len(texto)]
    if len(cauda.strip(" \t.\r\"“”';")) > RESTO_DA_LINHA:
        return False

    # A linha de cima estava no meio de uma frase? Então isto é o resto dela.
    anteriores = texto[:achado.start()].splitlines()
    for linha in reversed(anteriores):
        if linha.strip():
            if CONTINUACAO.search(linha.rstrip()):
                return False
            break

    return bool(CORPO_DE_ATO.search(texto[achado.end(): achado.end() + 4000]))

# Fórmulas que encerram a ementa e abrem o corpo do ato.
FIM_DA_EMENTA = re.compile(
    r"(O\s+PREFEITO|A\s+C[ÂA]MARA|O\s+POVO\s+DO\s+MUNIC[ÍI]PIO|Fa[çc]o\s+saber"
    r"|DECRETA\s*:|D\s*E\s*C\s*R\s*E\s*T\s*A|LEI\s*:|Art\.\s*1)",
    re.IGNORECASE,
)
AUTOR = re.compile(r"^\s*Autor\s*:\s*(.{3,80})$", re.MULTILINE | re.IGNORECASE)

# Cabeçalho do Diário Oficial: "Mesquita, Sexta-feira, 11 de janeiro de 2019 | Nº 00670"
DIARIO = re.compile(
    r"Mesquita,\s*[\wÀ-ÿ\-]+,?\s*(\d{1,2})\s+de\s+([A-Za-zÀ-ÿ]+)\s+de\s+(\d{4})"
    r"\s*\|\s*N[º°o\.]*\s*(\d+)",
    re.IGNORECASE,
)

# --- referências entre atos (o grafo de vigência) ----------------------------
#
# É o que permite avisar que a norma encontrada foi revogada. A busca textual,
# sozinha, entrega com a mesma confiança um ato vigente e um revogado há dez
# anos — e citar norma revogada em peça é erro que o cliente paga.
RELACOES = [
    ("revoga", r"revoga(?:d[ao]s?|m|r|ndo)?"),
    ("altera", r"(?:altera(?:d[ao]s?|m|r|ndo)?|modifica(?:d[ao]s?|m|r|ndo)?"
               r"|acrescenta|inclui\s+(?:o\s+)?(?:art|par)|d[áa]\s+nova\s+reda[çc][ãa]o)"),
    ("regulamenta", r"regulamenta(?:d[ao]s?|m|r|ndo)?"),
]
ALVO = (
    r"(?:d[ao]s?\s+|na\s+|no\s+|à\s+|a\s+|pel[ao]s?\s+)?"
    r"(Lei\s+Complementar|Lei|Decreto)\s+"
    r"(?:Municipal\s+|Ordin[áa]ri[ao]\s+)?"
    r"n?[º°oO\.]{0,3}\s*"
    # Mesmo defeito que o do cabeçalho, e aqui ele custa mais caro: com `*`,
    # "Decreto nº 1059" era lido como 105 e "Decreto nº 2529" como 252. O ato
    # errado ficava marcado como revogado — uma norma viva declarada morta,
    # com trecho de aparência impecável para sustentar o engano.
    r"(\d{1,3}(?:\.\d{3})+|\d{1,5})"
    r"(?:\s*[,/]?\s*(?:de\s+\d{1,2}\s+de\s+[A-Za-zÀ-ÿ]+\s+de\s+|/)\s*(\d{4}))?"
)
REFERENCIAS = [
    (nome, re.compile(verbo + r"[^.;]{0,60}?" + ALVO, re.IGNORECASE))
    for nome, verbo in RELACOES
]
ABREVIACOES = re.compile(
    r"\b(arts?|incs?|al[íi]neas?|par[áa]grafos?|caput|n[º°o]?|c/c)\s*\.",
    re.IGNORECASE,
)

# "Revogam-se as disposições em contrário" está no fecho de quase todo ato e
# não revoga nada identificável — é cláusula de estilo. Quando ela aparece
# ENTRE o verbo e a norma citada, só há revogação expressa se vier um conector
# de ressalva: "revogadas as disposições em contrário, **especialmente** o
# Decreto nº 063". Sem o conector, o que existe é uma citação qualquer na
# vizinhança da cláusula, e ligá-las inventaria uma revogação.
#
# Ordem inversa é legítima e não cai nesta regra: "revogando o Decreto nº
# 792/09 e as demais disposições em contrário" cita antes da cláusula.
CLAUSULA_DE_ESTILO = re.compile(
    r"disposi[çc][õo]es\s+em\s+contr[áa]rio", re.IGNORECASE
)

# "Fica revogado o artigo 93 do Decreto nº 127" não revoga o Decreto 127: revoga
# um artigo dele, e a norma segue viva sem aquele dispositivo. Registrar as duas
# coisas como "revoga" faria a ferramenta declarar morta uma norma em vigor —
# com a agravante de o trecho citado parecer confirmar.
DISPOSITIVO = re.compile(
    r"\b(artigos?|arts?|incisos?|incs?|par[áa]grafos?|al[íi]neas?|caput|itens?|"
    r"anexos?|§)\b|§",
    re.IGNORECASE,
)

# Mas "REVOGA TODOS OS ARTIGOS DA LEI Nº 899/2015" nomeia dispositivo e revoga a
# lei inteira. A menção a artigo, aqui, é a forma de dizer "tudo" — e classificar
# isso como parcial faria a ferramenta dizer que a norma subsiste. Estas
# expressões prevalecem sobre a menção a dispositivo.
INTEGRALIDADE = re.compile(
    r"todos\s+os\s+(?:artigos|dispositivos|incisos)|na\s+[íi]ntegra|integralmente"
    r"|em\s+sua\s+totalidade|por\s+inteiro",
    re.IGNORECASE,
)
RESSALVA = re.compile(
    r"especialmente|em\s+especial|notadamente|em\s+particular|sobretudo",
    re.IGNORECASE,
)

# Normas federais citadas o tempo todo nos considerandos. Ficam de fora do
# grafo municipal — dizer que a Lei 4.320/1964 foi alterada por decreto de
# Mesquita seria absurdo, e é o tipo de absurdo que passa despercebido.
FEDERAIS = {
    ("lei", 4320), ("lei", 8666), ("lei", 14133), ("lei", 8429), ("lei", 10520),
    ("lei", 12527), ("lei", 13019), ("lei", 13709), ("lei", 8080), ("lei", 9394),
    ("lei", 8069), ("lei", 10406), ("lei", 5172), ("lei", 6766), ("lei", 11445),
    ("lei", 13979), ("lei", 14434), ("lei", 9503), ("lei", 6938),
    # As complementares federais são o caso perigoso: têm número BAIXO, dentro
    # da faixa municipal, e por isso não são pegas pelo teto da série.
    ("lei_complementar", 101), ("lei_complementar", 116), ("lei_complementar", 123),
    ("lei_complementar", 131), ("lei_complementar", 141), ("lei_complementar", 156),
    ("lei_complementar", 173), ("lei_complementar", 187), ("lei_complementar", 214),
}

# Margem sobre o maior número catalogado: a página do Diário pode trazer ato um
# pouco à frente do que o portal listou, mas não centenas à frente.
MARGEM_DA_SERIE = 50


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def normalizar_tipo(bruto: str) -> str:
    limpo = sem_acento(re.sub(r"\s+", " ", bruto)).strip().upper()
    if limpo.startswith("LEI COMPLEMENTAR"):
        return "lei_complementar"
    if limpo.startswith("DECRETO"):
        return "decreto"
    return "lei"


def numero_inteiro(bruto: str) -> int | None:
    digitos = bruto.replace(".", "").strip()
    return int(digitos) if digitos.isdigit() else None


def identificador(tipo: str, numero: int, ano: int) -> str:
    return f"{tipo}-{numero}-{ano}"


@dataclass(slots=True)
class Segmento:
    """Um ato localizado dentro de um PDF, já delimitado."""

    tipo: str
    numero: int
    ano: int
    data: str | None
    ementa: str
    autor: str | None
    texto: str
    arquivo: str
    pagina_inicial: int
    paginas: list[tuple[int, str]] = field(default_factory=list)
    # Número e data do Diário Oficial em que o ato saiu — é a referência de
    # conferência que o advogado leva para a peça. Vem do banner no alto da
    # página, que fica ACIMA do cabeçalho do ato e portanto fora do recorte do
    # segmento: tem de ser lido do documento inteiro, não do trecho.
    diario: tuple[str, str] | None = None


# --- extração ---------------------------------------------------------------


def paginas_do_pdf(caminho: Path) -> list[str]:
    import fitz

    try:
        documento = fitz.open(caminho)
    except Exception:
        return []
    try:
        return [pagina.get_text() for pagina in documento]
    finally:
        documento.close()


def _data_iso(dia: str, mes: str, ano: str) -> str | None:
    limpo = sem_acento(mes).upper()
    numero_mes = MESES.get(limpo)
    if not numero_mes:
        # Grafia errada na origem — "OUTRUBRO", "AGOSOTO", "DEJUNHO". A raiz de
        # três letras identifica o mês sem ambiguidade, e datar o ato certo vale
        # mais do que recusar a data por causa do erro de quem digitou.
        for nome, numero in MESES.items():
            if nome[:3] in limpo:
                numero_mes = numero
                break
    if not numero_mes:
        return None
    try:
        return f"{int(ano):04d}-{numero_mes:02d}-{int(dia):02d}"
    except ValueError:
        return None


def extrair_ementa(corpo: str) -> str:
    """A ementa é o que vem entre o cabeçalho e a fórmula de promulgação.

    Vem entre aspas com frequência, mas não sempre; e às vezes em caixa alta
    (`REGULAMENTA O INC. XII DO ART. 94…`). O corte é pela fórmula, não pela
    aparência.
    """
    trecho = corpo[:2500]
    trecho = AUTOR.sub(" ", trecho)
    # Linhas de publicação do modelo antigo: "PUBLICADO / Jornal: / Data: / Página:"
    trecho = re.sub(r"PUBLICADO|Jornal\s*:.*|Data\s*:\s*[\d/]*|P[áa]gina\s*:\s*\d*",
                    " ", trecho)
    corte = FIM_DA_EMENTA.search(trecho)
    if corte:
        trecho = trecho[: corte.start()]
    limpo = re.sub(r"\s+", " ", trecho).strip(" \t\"“”'*-–—.,;:")
    return limpo[:1200]


def segmentar(caminho: Path, relativo: str) -> list[Segmento]:
    """Divide um PDF nos atos que ele contém.

    Cada segmento vai do seu cabeçalho até o cabeçalho seguinte. O arquivo pode
    trazer um ato só (modelo antigo, com timbre) ou a página inteira do Diário
    Oficial, com vários.
    """
    paginas = paginas_do_pdf(caminho)
    if not paginas:
        return []

    # Offset de cada página no texto concatenado, para saber em que página do
    # PDF cada ato começa — é por ela que o advogado confere no documento.
    inteiro, inicios = [], []
    posicao = 0
    for texto in paginas:
        inicios.append(posicao)
        inteiro.append(texto)
        posicao += len(texto) + 1
    completo = "\n".join(inteiro)

    # Validar ANTES de delimitar. Antes esta lista trazia todo candidato que
    # parecia cabeçalho, e a identidade do ato — número e ano — só era conferida
    # no laço adiante. O candidato que falhava ali era descartado como ato, mas
    # já tinha servido de FRONTEIRA: o ato anterior terminava nele. Resultado:
    # atos cortados na ementa, com 110 caracteres, por causa de uma ocorrência
    # que o próprio parser considerou inválida em seguida.
    achados = []
    for candidato in CABECALHO.finditer(completo):
        if not parece_cabecalho(completo, candidato):
            continue
        numero = numero_inteiro(candidato.group(2))
        ano_bruto = candidato.group(6) or candidato.group(3)
        if numero is None or not ano_bruto:
            continue
        ano = int(ano_bruto)
        # Mesquita se emancipou de Nova Iguaçu e foi instalada em 2001: não
        # existe ato municipal anterior. O piso não é higiene de dados, é a
        # regra que descarta a Lei Complementar 101/2000 — a LRF, federal —
        # quando a diagramação a deixa sozinha numa linha e ela passa por
        # cabeçalho.
        if not (PRIMEIRO_ANO <= ano <= 2100):
            continue
        achados.append((candidato, normalizar_tipo(candidato.group(1)), numero, ano))

    if not achados:
        return []

    banner = DIARIO.search(completo[:4000])
    diario = None
    if banner:
        data = _data_iso(banner.group(1), banner.group(2), banner.group(3))
        diario = (banner.group(4), data or "")

    def pagina_de(indice: int) -> int:
        pagina = 1
        for numero, comeco in enumerate(inicios, start=1):
            if comeco <= indice:
                pagina = numero
            else:
                break
        return pagina

    segmentos: list[Segmento] = []
    for ordem, (achado, tipo, numero, ano) in enumerate(achados):
        fim = (achados[ordem + 1][0].start() if ordem + 1 < len(achados)
               else len(completo))
        corpo = completo[achado.start(): fim]
        autor = AUTOR.search(corpo[:600])

        pagina_inicial = pagina_de(achado.start())
        pagina_final = pagina_de(max(achado.start(), fim - 1))
        recorte: list[tuple[int, str]] = []
        for numero_pagina in range(pagina_inicial, pagina_final + 1):
            comeco = max(inicios[numero_pagina - 1], achado.start())
            termino = min(
                inicios[numero_pagina - 1] + len(paginas[numero_pagina - 1]), fim
            )
            if termino > comeco:
                recorte.append((numero_pagina, completo[comeco:termino]))

        segmentos.append(
            Segmento(
                tipo=tipo,
                numero=numero,
                ano=ano,
                # Dia, mês e ano: os três, ou data nenhuma. Cabeçalho sem dia
                # existe (`LEI Nº 058 DE DEZEMBRO DE 2001`) e o ato entra assim
                # mesmo — sem data exata, que é melhor do que uma inventada.
                data=(
                    _data_iso(achado.group(4), achado.group(5), achado.group(6))
                    if achado.group(4) and achado.group(5) and achado.group(6)
                    else None
                ),
                ementa=extrair_ementa(corpo[achado.end() - achado.start():]),
                autor=autor.group(1).strip(" .\t") if autor else None,
                texto=corpo.strip(),
                arquivo=relativo,
                pagina_inicial=pagina_inicial,
                paginas=recorte,
                diario=diario,
            )
        )
    return segmentos


def extrair_referencias(texto: str) -> list[tuple[str, str, int, int | None, str]]:
    """Colhe do texto as relações de revogação, alteração e regulamentação.

    Devolve (relação, tipo do alvo, número, ano, trecho). O ano vem vazio
    quando a citação não o traz — "revoga a Lei nº 460" acontece —, e a
    resolução fica para depois, contra o próprio acervo.
    """
    achados = []
    limpo = re.sub(r"\s+", " ", texto)
    # O trecho entre o verbo e a norma citada não pode atravessar o fim de uma
    # frase, senão "revoga o art. 2º. A Lei nº 500 dispõe…" vira uma revogação
    # que ninguém decretou. Mas o ponto da abreviação não é fim de frase:
    # "revogados os arts. 3º e 4º da Lei nº 828" precisa passar. Tira-se o
    # ponto das abreviações, e o ponto que sobra é de verdade.
    limpo = ABREVIACOES.sub(r"\1 ", limpo)
    vistos: set[tuple[str, str, int, int | None]] = set()
    for relacao, padrao in REFERENCIAS:
        for achado in padrao.finditer(limpo):
            numero = numero_inteiro(achado.group(2))
            if numero is None:
                continue

            intervalo = limpo[achado.start(): achado.start(1)]
            if CLAUSULA_DE_ESTILO.search(intervalo) and not RESSALVA.search(intervalo):
                continue

            ano = int(achado.group(3)) if achado.group(3) else None
            if ano is not None and not (1990 <= ano <= 2100):
                ano = None

            parcial = DISPOSITIVO.search(intervalo) and not INTEGRALIDADE.search(
                intervalo
            )
            extensao = "parcial" if parcial else "total"

            chave = (relacao, normalizar_tipo(achado.group(1)), numero, ano)
            if chave in vistos:
                # A mesma revogação costuma aparecer duas vezes no ato: uma na
                # ementa, outra no artigo. É um fato só.
                continue
            vistos.add(chave)

            inicio = max(0, achado.start() - 90)
            achados.append(
                (*chave, extensao, limpo[inicio: achado.end() + 40].strip())
            )
    return achados


# --- metadados do portal -----------------------------------------------------


# O portal repete a identificação dentro da descrição: "Lei 1106 - Revoga a
# Lei Municipal nº 460…". Espécie e número já são campos próprios; repeti-los
# na ementa só atrapalha a leitura e polui o índice de busca. A marca de
# republicação, essa, fica: diz que o texto saiu duas vezes no Diário.
PREFIXO_DO_PORTAL = re.compile(
    r"^\s*(?:lei\s+complementar|lei|decreto)\s*n?[º°o\.]*\s*[\d\.]+\s*[-–—:]\s*",
    re.IGNORECASE,
)


def limpar_ementa_do_portal(descricao: str) -> str:
    return PREFIXO_DO_PORTAL.sub("", descricao).strip()


def ler_metadados(pasta: Path) -> dict[tuple[str, int, int], dict]:
    """Lê os relatórios de download: são a ementa oficial e a URL de origem.

    A descrição que o portal dá a cada ato é a ementa como o Município a
    publicou. Vale mais que a ementa extraída do PDF, que depende do recorte —
    por isso ela é a preferida, e a do PDF só entra quando aquela falta.
    """
    catalogo: dict[tuple[str, int, int], dict] = {}
    for arquivo in sorted(pasta.glob("relatorio_download*.csv")):
        with open(arquivo, encoding="utf-8-sig", newline="") as fh:
            for linha in csv.DictReader(fh, delimiter=";"):
                tipo_bruto = (linha.get("tipo") or "").strip()
                if not tipo_bruto or "\x00" in tipo_bruto:
                    continue
                numero = numero_inteiro((linha.get("numero") or "").strip())
                ano_bruto = (linha.get("ano") or "").strip()
                if numero is None or not ano_bruto.isdigit():
                    continue
                chave = (normalizar_tipo(tipo_bruto), numero, int(ano_bruto))
                descricao = re.sub(r"\s+", " ", (linha.get("descricao") or "")).strip()
                anterior = catalogo.get(chave)
                if anterior and len(anterior.get("ementa") or "") >= len(descricao):
                    continue
                catalogo[chave] = {
                    "ementa": limpar_ementa_do_portal(descricao),
                    "url": (linha.get("url") or "").strip(),
                    "arquivo": (linha.get("arquivo") or "").strip(),
                }
    return catalogo


def teto_da_serie(catalogo: dict[tuple[str, int, int], dict]) -> dict[str, int]:
    """Maior número que cada espécie municipal pode ter, pelo catálogo do portal.

    Existe porque o corpo de um decreto de Mesquita cita normas federais e
    estaduais, e a diagramação às vezes deixa a citação em forma de cabeçalho.
    Sem teto, entraram no acervo cinco atos que não são do Município — entre
    eles a Lei federal 14.133/2021 e o Decreto estadual 46.984/2020 —, e o
    servidor as citaria como "Mesquita/RJ, Lei nº 14.133". Atribuir lei federal
    ao Município não é imprecisão: é erro de competência.

    O teto vem dos dados, não de constante escolhida a dedo: a série municipal
    chega a 1.288 (leis) e 3.917 (decretos), e cresce sozinha quando o portal
    publicar mais.
    """
    maiores: dict[str, int] = {}
    for tipo, numero, _ in catalogo:
        maiores[tipo] = max(maiores.get(tipo, 0), numero)

    tetos = {t: v + MARGEM_DA_SERIE for t, v in maiores.items()}
    # A Lei Complementar não tem teto próprio: o portal a cataloga como "Lei".
    # Herda o da lei ordinária, e as complementares federais — de número baixo,
    # dentro da faixa — ficam por conta da lista `FEDERAIS`.
    tetos.setdefault("lei_complementar", tetos.get("lei", 0))
    return tetos


def da_serie_municipal(
    chave: tuple[str, int, int],
    tetos: dict[str, int],
    catalogo: dict[tuple[str, int, int], dict],
) -> bool:
    """Decide se o ato pertence à série do Município.

    Estar no catálogo do portal basta: é a lista oficial. Fora dela, exige-se
    número dentro da série e que a chave não seja de norma federal conhecida.
    """
    if chave in catalogo or ("lei", chave[1], chave[2]) in catalogo:
        return True
    tipo, numero, _ = chave
    if numero > tetos.get(tipo, 0):
        return False
    return (tipo, numero) not in FEDERAIS


def pdfs_unicos(pasta: Path) -> Iterator[tuple[Path, str]]:
    """Percorre os PDFs ignorando as cópias `_vN` de conteúdo idêntico.

    O download gerou 7.763 arquivos para cerca de 4.000 atos: cada nova
    tentativa salvava `_v2`, `_v3`. Muitas são byte a byte iguais; outras não
    são, e por isso a duplicata é decidida por hash, não pelo nome.
    """
    vistos: set[str] = set()
    for tipo in ("Leis", "Decretos"):
        raiz = pasta / tipo
        if not raiz.is_dir():
            continue
        for ano in sorted(raiz.iterdir()):
            if not ano.is_dir():
                continue
            for caminho in sorted(ano.glob("*.pdf")):
                resumo = hashlib.md5(caminho.read_bytes()).hexdigest()
                if resumo in vistos:
                    continue
                vistos.add(resumo)
                yield caminho, f"{tipo}/{ano.name}/{caminho.name}"


# --- banco -------------------------------------------------------------------

ESQUEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS atos (
    id             TEXT PRIMARY KEY,
    tipo           TEXT NOT NULL,
    numero         INTEGER NOT NULL,
    ano            INTEGER NOT NULL,
    data           TEXT,
    ementa         TEXT,
    ementa_fonte   TEXT,
    autor          TEXT,
    texto          TEXT,
    caracteres     INTEGER,
    arquivo        TEXT,
    pagina_inicial INTEGER,
    paginas        INTEGER,
    fonte          TEXT,
    diario_numero  TEXT,
    diario_data    TEXT,
    url_origem     TEXT,
    situacao       TEXT
);
CREATE INDEX IF NOT EXISTS ix_atos_chave ON atos(tipo, numero, ano);
CREATE INDEX IF NOT EXISTS ix_atos_ano ON atos(ano);

CREATE TABLE IF NOT EXISTS paginas (
    ato_id      TEXT NOT NULL,
    pagina      INTEGER NOT NULL,
    pagina_pdf  INTEGER,
    texto       TEXT
);
CREATE INDEX IF NOT EXISTS ix_paginas_ato ON paginas(ato_id, pagina);

CREATE TABLE IF NOT EXISTS referencias (
    origem_id   TEXT NOT NULL,
    relacao     TEXT NOT NULL,
    alvo_tipo   TEXT NOT NULL,
    alvo_numero INTEGER NOT NULL,
    alvo_ano    INTEGER,
    alvo_id     TEXT,
    esfera      TEXT,
    extensao    TEXT,
    trecho      TEXT
);
CREATE INDEX IF NOT EXISTS ix_ref_alvo ON referencias(alvo_id);
CREATE INDEX IF NOT EXISTS ix_ref_origem ON referencias(origem_id);

CREATE TABLE IF NOT EXISTS acervo_info (chave TEXT PRIMARY KEY, valor TEXT);
"""

# Conteúdo externo: sem isso o FTS5 guarda uma segunda cópia do texto e o
# índice fica maior que o dado — medido no acervo anterior, 54% do banco.
INDICES = """
DROP TABLE IF EXISTS atos_fts;
CREATE VIRTUAL TABLE atos_fts USING fts5(
    ementa, texto,
    content='atos', content_rowid='rowid',
    tokenize="unicode61 remove_diacritics 2"
);
INSERT INTO atos_fts(rowid, ementa, texto) SELECT rowid, ementa, texto FROM atos;

DROP TABLE IF EXISTS paginas_fts;
CREATE VIRTUAL TABLE paginas_fts USING fts5(
    texto,
    content='paginas', content_rowid='rowid',
    tokenize="unicode61 remove_diacritics 2"
);
INSERT INTO paginas_fts(rowid, texto) SELECT rowid, texto FROM paginas;
"""


def construir(pasta: Path, banco: Path, limite: int | None = None) -> dict:
    pasta, banco = Path(pasta), Path(banco)
    banco.parent.mkdir(parents=True, exist_ok=True)
    if banco.exists():
        banco.unlink()

    conexao = sqlite3.connect(banco)
    conexao.executescript(ESQUEMA)

    catalogo = ler_metadados(pasta)
    tetos = teto_da_serie(catalogo)
    print(f"metadados do portal: {len(catalogo)} atos", flush=True)
    print(f"teto da série municipal: "
          + ", ".join(f"{t}≤{v}" for t, v in sorted(tetos.items())), flush=True)

    # Um mesmo ato aparece em vários arquivos (a cópia isolada e a página do
    # Diário). Guarda-se o segmento mais longo: é o que traz o ato inteiro.
    melhores: dict[tuple[str, int, int], Segmento] = {}
    diarios: dict[str, tuple[str, str]] = {}
    contagem = {"arquivos": 0, "sem_texto": 0, "sem_cabecalho": 0, "segmentos": 0,
                "fora_da_serie_municipal": 0}
    recusados: set[tuple[str, int, int]] = set()

    for caminho, relativo in pdfs_unicos(pasta):
        contagem["arquivos"] += 1
        if limite and contagem["arquivos"] > limite:
            break
        if contagem["arquivos"] % 250 == 0:
            print(f"  {contagem['arquivos']} arquivos, "
                  f"{len(melhores)} atos", flush=True)

        segmentos = segmentar(caminho, relativo)
        if not segmentos:
            paginas = paginas_do_pdf(caminho)
            if sum(len(p.strip()) for p in paginas) < 100:
                contagem["sem_texto"] += 1
            else:
                contagem["sem_cabecalho"] += 1
            continue

        for segmento in segmentos:
            contagem["segmentos"] += 1
            chave = (segmento.tipo, segmento.numero, segmento.ano)
            if not da_serie_municipal(chave, tetos, catalogo):
                contagem["fora_da_serie_municipal"] += 1
                recusados.add(chave)
                continue
            anterior = melhores.get(chave)
            if anterior is None or len(segmento.texto) > len(anterior.texto):
                melhores[chave] = segmento
                if segmento.diario:
                    diarios[identificador(*chave)] = segmento.diario

    print(f"lidos {contagem['arquivos']} arquivos → {len(melhores)} atos distintos",
          flush=True)
    if recusados:
        # Recusa é dado, não linha de log: quem reler isto em seis meses precisa
        # saber o que ficou de fora e por quê.
        print(f"fora da série municipal ({len(recusados)}): "
              + ", ".join(f"{t} {n}/{a}" for t, n, a in sorted(recusados)), flush=True)

    # Atos catalogados no portal cujo PDF não rendeu segmento: existem, e
    # precisam existir na base com a ementa oficial e o aviso de que o texto
    # não foi extraído. Omiti-los faria a busca dizer "não há" sobre norma que
    # há — o pior defeito possível numa base de legislação.
    # O portal cataloga Lei Complementar como "Lei": a LC 2/2002 aparece no
    # relatório como Lei 2/2002. Quem sabe a espécie é o cabeçalho do próprio
    # ato, lido do PDF. Sem esta reconciliação nasceriam duas entradas para a
    # mesma norma — uma com ementa e sem texto, outra com texto e sem ementa.
    complementares = {
        (numero, ano) for (tipo, numero, ano) in melhores if tipo == "lei_complementar"
    }
    for chave, meta in catalogo.items():
        if chave[0] == "lei" and (chave[1], chave[2]) in complementares:
            continue
        if chave not in melhores:
            melhores[chave] = Segmento(
                tipo=chave[0], numero=chave[1], ano=chave[2], data=None,
                ementa="", autor=None, texto="", arquivo=meta.get("arquivo", ""),
                pagina_inicial=0, paginas=[],
            )

    for chave, segmento in sorted(melhores.items()):
        identidade = identificador(*chave)
        meta = catalogo.get(chave) or (
            catalogo.get(("lei", chave[1], chave[2]), {})
            if chave[0] == "lei_complementar" else {}
        )
        ementa_oficial = (meta.get("ementa") or "").strip()
        ementa = ementa_oficial or segmento.ementa
        fonte_ementa = "portal" if ementa_oficial else ("pdf" if segmento.ementa else "")
        diario = diarios.get(identidade)

        conexao.execute(
            "INSERT OR REPLACE INTO atos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                identidade, segmento.tipo, segmento.numero, segmento.ano,
                segmento.data, ementa, fonte_ementa, segmento.autor,
                segmento.texto, len(segmento.texto), segmento.arquivo,
                segmento.pagina_inicial or None, len(segmento.paginas),
                "diario_oficial" if diario else "ato_isolado",
                diario[0] if diario else None, diario[1] if diario else None,
                meta.get("url") or None,
                "ok" if len(segmento.texto) > 200 else "sem_texto_extraido",
            ),
        )
        for ordem, (pagina_pdf, texto) in enumerate(segmento.paginas, start=1):
            conexao.execute(
                "INSERT INTO paginas VALUES (?,?,?,?)",
                (identidade, ordem, pagina_pdf, texto),
            )
        for (
            relacao, alvo_tipo, alvo_numero, alvo_ano, extensao, trecho
        ) in extrair_referencias(segmento.texto):
            if (alvo_tipo, alvo_numero) in FEDERAIS and alvo_ano != segmento.ano:
                esfera, alvo_id = "externa", None
            else:
                esfera, alvo_id = "indefinida", None
            conexao.execute(
                "INSERT INTO referencias VALUES (?,?,?,?,?,?,?,?,?)",
                (identidade, relacao, alvo_tipo, alvo_numero, alvo_ano,
                 alvo_id, esfera, extensao, trecho[:400]),
            )

    conexao.commit()
    resolver_referencias(conexao)
    print("montando os índices de busca…", flush=True)
    conexao.executescript(INDICES)

    resumo = estatisticas(conexao) | {"leitura": contagem}
    conexao.execute(
        "INSERT OR REPLACE INTO acervo_info VALUES ('resumo', ?)",
        (json.dumps(resumo, ensure_ascii=False),),
    )
    conexao.commit()
    conexao.execute("VACUUM")
    conexao.close()
    return resumo


def resolver_referencias(conexao: sqlite3.Connection) -> None:
    """Liga cada citação ao ato correspondente do acervo, quando ele existir.

    Uma citação sem ano ("revoga a Lei nº 460") só se resolve se houver um
    único ato daquele tipo e número em todo o acervo. Havendo mais de um, fica
    sem resolver: apontar para o errado é pior do que não apontar.
    """
    por_chave = {}
    por_tipo_numero = defaultdict(list)
    for identidade, tipo, numero, ano in conexao.execute(
        "SELECT id, tipo, numero, ano FROM atos"
    ):
        por_chave[(tipo, numero, ano)] = identidade
        por_tipo_numero[(tipo, numero)].append(identidade)

    atualizacoes = []
    for rowid, tipo, numero, ano in conexao.execute(
        "SELECT rowid, alvo_tipo, alvo_numero, alvo_ano FROM referencias"
    ):
        alvo = None
        if ano is not None:
            alvo = por_chave.get((tipo, numero, ano))
        else:
            candidatos = por_tipo_numero.get((tipo, numero), [])
            if len(candidatos) == 1:
                alvo = candidatos[0]
        if alvo:
            atualizacoes.append(("municipal", alvo, rowid))

    conexao.executemany(
        "UPDATE referencias SET esfera = ?, alvo_id = ? WHERE rowid = ?", atualizacoes
    )
    conexao.execute(
        "UPDATE referencias SET esfera = 'externa' WHERE alvo_id IS NULL AND esfera <> 'externa'"
    )
    conexao.commit()
    print(f"referências resolvidas: {len(atualizacoes)}", flush=True)


def estatisticas(conexao: sqlite3.Connection) -> dict:
    def um(sql: str, *p):
        return conexao.execute(sql, p).fetchone()[0]

    por_tipo = {
        ROTULOS.get(t, t): {"quantidade": n, "periodo": f"{a}–{b}"}
        for t, n, a, b in conexao.execute(
            "SELECT tipo, COUNT(*), MIN(ano), MAX(ano) FROM atos GROUP BY tipo"
        )
    }
    lacunas = []
    for tipo in ("lei", "lei_complementar", "decreto"):
        anos = {a for (a,) in conexao.execute(
            "SELECT DISTINCT ano FROM atos WHERE tipo = ? AND situacao = 'ok'", (tipo,)
        )}
        if not anos:
            continue
        faltando = sorted(set(range(min(anos), max(anos) + 1)) - anos)
        magras = sorted(
            a for (a, n) in conexao.execute(
                "SELECT ano, COUNT(*) FROM atos WHERE tipo = ? AND situacao='ok' "
                "GROUP BY ano HAVING COUNT(*) <= 10", (tipo,)
            )
        )
        if faltando or magras:
            lacunas.append({"tipo": ROTULOS[tipo], "anos_ausentes": faltando,
                            "anos_com_ate_10_atos": magras})

    return {
        "total_de_atos": um("SELECT COUNT(*) FROM atos"),
        "por_especie": por_tipo,
        "com_texto_integral": um("SELECT COUNT(*) FROM atos WHERE situacao='ok'"),
        "sem_texto_extraido": um("SELECT COUNT(*) FROM atos WHERE situacao<>'ok'"),
        "paginas": um("SELECT COUNT(*) FROM paginas"),
        "caracteres": um("SELECT COALESCE(SUM(caracteres),0) FROM atos"),
        "referencias_municipais": um(
            "SELECT COUNT(*) FROM referencias WHERE esfera='municipal'"),
        "atos_com_revogacao_integral": um(
            "SELECT COUNT(DISTINCT alvo_id) FROM referencias "
            "WHERE relacao='revoga' AND esfera='municipal' AND extensao='total'"),
        "atos_com_revogacao_parcial": um(
            "SELECT COUNT(DISTINCT alvo_id) FROM referencias "
            "WHERE relacao='revoga' AND esfera='municipal' AND extensao='parcial'"),
        "lacunas": lacunas,
    }


if __name__ == "__main__":
    import argparse

    analisador = argparse.ArgumentParser(prog="python -m legis.ingestao")
    analisador.add_argument("--pasta", default=os.path.expanduser("~/Mesquita_Legislacao"))
    analisador.add_argument("--banco", default=str(Path(__file__).parent.parent / "dados" / "mesquita.sqlite"))
    analisador.add_argument("--limite", type=int, default=None,
                            help="processa só os N primeiros PDFs (calibração)")
    argumentos = analisador.parse_args()

    resumo = construir(Path(argumentos.pasta), Path(argumentos.banco), argumentos.limite)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
