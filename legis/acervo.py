"""Leitura do acervo: busca textual, texto do ato e grafo de vigência.

Só lê. O banco é aberto em modo somente-leitura porque quem consome é um
modelo de linguagem, e uma ferramenta de pesquisa não tem por que poder
alterar o acervo.

Uma base de legislação difere de uma de jurisprudência num ponto que muda o
desenho todo: **o precedente envelhece, a norma morre**. Um acórdão de 2008
continua sendo o que era; a Lei 460/2008 foi revogada em 2019 e citá-la hoje é
erro. A busca textual devolve as duas com a mesma confiança — por isso o grafo
de revogações não é um extra, é parte da resposta.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROTULOS = {
    "lei": "Lei",
    "lei_complementar": "Lei Complementar",
    "decreto": "Decreto",
}

MESES_EXTENSO = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

PORTAL = "https://transparencia.mesquita.rj.gov.br"

_OPERADORES = {"and", "or", "not", "near"}

# Quem consulta é um modelo, que manda a pergunta inteira ("posso construir a
# menos de dois metros da divisa?"). Com os termos ligados por E, um "posso"
# zera o resultado. Nenhuma destas palavras distingue uma norma de outra.
_VAZIAS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e",
    "em", "entre", "essa", "esse", "esta", "este", "eh", "existe", "existem",
    "foi", "ha", "isso", "meu", "minha", "na", "nas", "no", "nos", "num", "numa",
    "o", "os", "ou", "para", "pela", "pelo", "por", "pode", "podem", "posso",
    "qual", "quais", "quando", "que", "quem", "se", "sem", "ser", "sao", "seu",
    "sob", "sobre", "sua", "tem", "ter", "um", "uma", "uns", "umas",
    "cabe", "deve", "devem", "fazer", "gostaria", "haver", "preciso", "quero",
    # Ficam de fora de propósito palavras que PARECEM de formulação mas são o
    # objeto da pergunta em direito municipal: "isenção", "autoriza", "vedado",
    # "obrigatório", "prazo". Tirá-las devolve norma de outro assunto.
}


def _sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    ).lower()


def montar_consulta_fts(texto: str, operador: str = "AND") -> str:
    """Traduz linguagem natural para a sintaxe do FTS5.

    Cada termo vai entre aspas para que pontuação e operadores acidentais não
    quebrem a consulta: o `MATCH` rejeita a expressão inteira com erro de
    sintaxe, e o advogado só veria "a busca falhou". Trechos que ele mesmo
    aspeou são preservados como expressão exata.
    """
    partes: list[str] = []
    for frase in re.findall(r'"([^"]+)"', texto):
        limpa = frase.replace('"', " ").strip()
        if limpa:
            partes.append(f'"{limpa}"')

    resto = re.sub(r'"[^"]*"', " ", texto)
    livres = re.findall(r"[\wÀ-ɏ]+", resto)
    uteis = [
        t for t in livres
        if _sem_acento(t) not in _VAZIAS and _sem_acento(t) not in _OPERADORES
    ]
    partes.extend(f'"{t}"' for t in (uteis or livres))
    return f" {operador} ".join(partes)


def por_extenso(data: str | None) -> str | None:
    """2019-01-11 → '11 de janeiro de 2019'. É como a norma se cita."""
    if not data:
        return None
    try:
        ano, mes, dia = (int(p) for p in data.split("-"))
        return f"{dia} de {MESES_EXTENSO[mes]} de {ano}"
    except (ValueError, IndexError):
        return None


def numero_formatado(numero: int) -> str:
    return f"{numero:,}".replace(",", ".") if numero >= 1000 else str(numero)


@dataclass(slots=True)
class Ato:
    id: str
    tipo: str
    numero: int
    ano: int
    data: str | None
    ementa: str
    ementa_fonte: str | None
    autor: str | None
    trecho: str
    caracteres: int
    arquivo: str | None
    paginas: int
    fonte: str | None
    diario_numero: str | None
    diario_data: str | None
    url_origem: str | None
    situacao: str

    @property
    def citacao(self) -> str:
        """Referência no formato que vai para a peça."""
        base = (f"Mesquita/RJ, {ROTULOS.get(self.tipo, self.tipo)} nº "
                f"{numero_formatado(self.numero)}")
        extenso = por_extenso(self.data)
        return f"{base}, de {extenso}" if extenso else f"{base}/{self.ano}"

    @property
    def conferencia(self) -> str | None:
        """Onde conferir o texto oficial."""
        if self.diario_numero:
            data = por_extenso(self.diario_data) or self.diario_data
            return f"Diário Oficial de Mesquita nº {self.diario_numero}, de {data}"
        return None

    def para_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "especie": ROTULOS.get(self.tipo, self.tipo),
            "numero": self.numero,
            "ano": self.ano,
            "data": self.data,
            "citacao": self.citacao,
            "ementa": self.ementa,
            "trecho": self.trecho or None,
            "autor": self.autor,
            "publicacao": self.conferencia,
            "url_origem": self.url_origem,
            "texto_integral_disponivel": self.situacao == "ok",
            "extensao_em_caracteres": self.caracteres,
            "paginas": self.paginas,
        }


@dataclass(slots=True)
class Passagem:
    """Um trecho localizado no corpo de um ato, com a página para conferir."""

    ato: Ato
    pagina: int
    pagina_pdf: int | None
    trecho: str
    termos: list[str]

    def para_dict(self) -> dict[str, Any]:
        dados = self.ato.para_dict()
        dados.pop("ementa", None)
        return {
            **dados,
            "ementa_resumida": self.ato.ementa[:200] or None,
            "pagina": self.pagina,
            "pagina_no_pdf": self.pagina_pdf,
            "trecho": self.trecho,
            "termos_encontrados": self.termos,
            "onde": "corpo do ato",
        }


class Acervo:
    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        if not self.caminho.exists():
            raise FileNotFoundError(
                f"Acervo não encontrado em {self.caminho}. Rode a ingestão antes "
                f"(python -m legis.ingestao)."
            )
        self.conexao = sqlite3.connect(
            f"file:{self.caminho.as_posix()}?mode=ro", uri=True, check_same_thread=False
        )
        self.conexao.row_factory = sqlite3.Row

    def fechar(self) -> None:
        self.conexao.close()

    # -- busca ------------------------------------------------------------

    def pesquisar(
        self,
        consulta: str,
        *,
        especie: str | None = None,
        ano_min: int | None = None,
        ano_max: int | None = None,
        limite: int = 10,
    ) -> tuple[list[Ato], bool, str]:
        """Busca na ementa — o que a norma diz de si mesma.

        Tenta exigir todos os termos; não achando, repete aceitando qualquer
        um. Devolver a norma mais próxima avisando que a correspondência foi
        parcial é melhor do que devolver vazio porque a pergunta trazia uma
        palavra a mais.
        """
        return self._buscar("ementa", consulta, especie, ano_min, ano_max, limite)

    def pesquisar_texto(
        self,
        consulta: str,
        *,
        especie: str | None = None,
        ano_min: int | None = None,
        ano_max: int | None = None,
        limite: int = 10,
    ) -> tuple[list[Passagem], bool, str]:
        """Busca no corpo do ato, e devolve a página.

        A ementa diz do que a norma trata; o dispositivo é onde a regra está.
        Uma lei "que dispõe sobre o Código Tributário" tem ementa de uma linha
        e 155 páginas de regras — procurar só na ementa não acha nenhuma delas.
        """
        expressao = ""
        for operador in ("AND", "OR"):
            expressao = montar_consulta_fts(consulta, operador)
            if not expressao:
                return [], False, ""
            achados = self._consultar_paginas(
                expressao, especie, ano_min, ano_max, limite
            )
            if achados:
                return achados, operador == "OR", expressao
        return [], False, expressao

    def _buscar(self, coluna, consulta, especie, ano_min, ano_max, limite):
        expressao = ""
        for operador in ("AND", "OR"):
            expressao = montar_consulta_fts(consulta, operador)
            if not expressao:
                return [], False, ""
            achados = self._consultar(
                f"{coluna} : ({expressao})", especie, ano_min, ano_max, limite
            )
            if achados:
                return achados, operador == "OR", expressao
        return [], False, expressao

    def _consultar(self, expressao, especie, ano_min, ano_max, limite):
        sql = [
            "SELECT a.*, snippet(atos_fts, 0, '', '', ' … ', 26) AS achado",
            "FROM atos_fts f JOIN atos a ON a.rowid = f.rowid",
            "WHERE atos_fts MATCH ?",
        ]
        parametros: list[Any] = [expressao]
        if especie:
            sql.append("AND a.tipo = ?")
            parametros.append(especie)
        if ano_min is not None:
            sql.append("AND a.ano >= ?")
            parametros.append(ano_min)
        if ano_max is not None:
            sql.append("AND a.ano <= ?")
            parametros.append(ano_max)
        sql.append("ORDER BY rank LIMIT ?")
        parametros.append(max(1, min(limite, 50)))

        return [
            self._ato(linha, linha["achado"])
            for linha in self.conexao.execute(" ".join(sql), parametros)
        ]

    def _consultar_paginas(self, expressao, especie, ano_min, ano_max, limite):
        sql = [
            "SELECT a.*, p.pagina, p.pagina_pdf,",
            "       snippet(paginas_fts, 0, '\x02', '\x03', ' … ', 34) AS achado",
            "FROM paginas_fts f",
            "JOIN paginas p ON p.rowid = f.rowid",
            "JOIN atos a ON a.id = p.ato_id",
            "WHERE paginas_fts MATCH ?",
        ]
        parametros: list[Any] = [expressao]
        if especie:
            sql.append("AND a.tipo = ?")
            parametros.append(especie)
        if ano_min is not None:
            sql.append("AND a.ano >= ?")
            parametros.append(ano_min)
        if ano_max is not None:
            sql.append("AND a.ano <= ?")
            parametros.append(ano_max)
        sql.append("ORDER BY rank LIMIT ?")
        parametros.append(max(1, min(limite, 30)))

        achados = []
        for linha in self.conexao.execute(" ".join(sql), parametros):
            bruto = linha["achado"] or ""
            # Os delimitadores invisíveis marcam o que casou: extraí-los diz ao
            # advogado por que aquele trecho veio, e somem do texto exibido.
            termos = sorted({t.lower() for t in re.findall("\x02(.*?)\x03", bruto)})
            achados.append(
                Passagem(
                    ato=self._ato(linha, ""),
                    pagina=linha["pagina"],
                    pagina_pdf=linha["pagina_pdf"],
                    trecho=re.sub(
                        r"\s+", " ", bruto.replace("\x02", "").replace("\x03", "")
                    ).strip(),
                    termos=termos,
                )
            )
        return achados

    # -- acesso direto ----------------------------------------------------

    def obter(self, identificador: str) -> Ato | None:
        linha = self.conexao.execute(
            "SELECT * FROM atos WHERE id = ?", (identificador,)
        ).fetchone()
        return self._ato(linha, "") if linha else None

    def por_numero(self, especie: str, numero: int, ano: int | None) -> list[Ato]:
        """Localiza pela referência que o advogado tem em mãos: 'Lei 1.106/2019'."""
        sql = "SELECT * FROM atos WHERE tipo = ? AND numero = ?"
        parametros: list[Any] = [especie, numero]
        if ano is not None:
            sql += " AND ano = ?"
            parametros.append(ano)
        sql += " ORDER BY ano"
        return [self._ato(l, "") for l in self.conexao.execute(sql, parametros)]

    def texto_do_ato(self, identificador: str) -> str | None:
        linha = self.conexao.execute(
            "SELECT texto FROM atos WHERE id = ?", (identificador,)
        ).fetchone()
        return linha["texto"] if linha else None

    def paginas_do_ato(
        self, identificador: str, inicio: int, fim: int
    ) -> list[dict[str, Any]]:
        linhas = self.conexao.execute(
            "SELECT pagina, pagina_pdf, texto FROM paginas "
            "WHERE ato_id = ? AND pagina BETWEEN ? AND ? ORDER BY pagina",
            (identificador, inicio, fim),
        ).fetchall()
        return [
            {"pagina": l["pagina"], "pagina_no_pdf": l["pagina_pdf"], "texto": l["texto"]}
            for l in linhas
        ]

    def listar(
        self,
        *,
        especie: str | None = None,
        ano: int | None = None,
        limite: int = 20,
    ) -> list[Ato]:
        sql = ["SELECT * FROM atos WHERE 1=1"]
        parametros: list[Any] = []
        if especie:
            sql.append("AND tipo = ?")
            parametros.append(especie)
        if ano is not None:
            sql.append("AND ano = ?")
            parametros.append(ano)
        sql.append("ORDER BY ano DESC, numero DESC LIMIT ?")
        parametros.append(max(1, min(limite, 100)))
        return [self._ato(l, "") for l in self.conexao.execute(" ".join(sql), parametros)]

    # -- vigência ---------------------------------------------------------

    def vigencia(self, identificador: str) -> dict[str, Any]:
        """O que outros atos do acervo fizeram com esta norma.

        Devolve as revogações, alterações e regulamentações **expressas** que
        foram encontradas. Não devolve "vigente": nada aqui autoriza essa
        afirmação, e o campo `advertencia` diz por quê.
        """
        ato = self.obter(identificador)
        if ato is None:
            return {"erro": f"Ato não encontrado: {identificador}"}

        recebidas: dict[str, list[dict[str, Any]]] = {
            "revoga": [], "altera": [], "regulamenta": []
        }
        for linha in self.conexao.execute(
            "SELECT r.relacao, r.trecho, r.extensao, a.* FROM referencias r "
            "JOIN atos a ON a.id = r.origem_id "
            "WHERE r.alvo_id = ? ORDER BY a.ano, a.numero",
            (identificador,),
        ):
            origem = self._ato(linha, "")
            recebidas.setdefault(linha["relacao"], []).append({
                "ato": origem.citacao,
                "id": origem.id,
                "extensao": linha["extensao"] or "total",
                "ementa": origem.ementa[:300],
                "trecho_que_indica": re.sub(r"\s+", " ", linha["trecho"] or "").strip(),
            })

        feitas = []
        for linha in self.conexao.execute(
            "SELECT relacao, alvo_tipo, alvo_numero, alvo_ano, alvo_id, esfera, "
            "extensao, trecho FROM referencias WHERE origem_id = ? ORDER BY relacao",
            (identificador,),
        ):
            rotulo = ROTULOS.get(linha["alvo_tipo"], linha["alvo_tipo"])
            alvo = f"{rotulo} nº {numero_formatado(linha['alvo_numero'])}"
            if linha["alvo_ano"]:
                alvo += f"/{linha['alvo_ano']}"
            feitas.append({
                "relacao": linha["relacao"],
                "extensao": linha["extensao"] or "total",
                "alvo": alvo,
                "id_do_alvo": linha["alvo_id"],
                "esfera": linha["esfera"],
                "trecho": re.sub(r"\s+", " ", linha["trecho"] or "").strip(),
            })

        revogacoes = recebidas.get("revoga", [])
        alteracoes = recebidas.get("altera", [])
        integrais = [r for r in revogacoes if r["extensao"] == "total"]
        parciais = [r for r in revogacoes if r["extensao"] == "parcial"]

        # As situações são juridicamente distintas e não podem se confundir. Mas
        # nenhuma delas autoriza afirmar o estado da norma: o acervo prova o que
        # ENCONTROU, não o que existe. "Subsiste quanto ao restante" e "não
        # reflete a redação em vigor" — que era como estas frases estavam
        # escritas — afirmam vigência pela porta dos fundos, e essa é justamente
        # a afirmação que a ferramenta não pode dar.
        #
        # Também não são excludentes: o Plano Diretor tem revogação parcial E
        # alterações posteriores, e omitir uma das duas é meia resposta.
        partes = []
        if integrais:
            partes.append(
                "REVOGAÇÃO EXPRESSA INTEGRAL localizada no acervo: não cite esta "
                "norma como fundamento sem antes ler o ato revogador."
            )
        if parciais:
            partes.append(
                "A revogação expressa localizada é PARCIAL e não autoriza tratar a "
                "norma como integralmente revogada; quanto ao restante, não foi "
                "localizada revogação expressa no acervo. Veja no trecho indicado "
                "QUAIS dispositivos caíram — o que você pretende citar pode ser um "
                "deles."
            )
        if alteracoes:
            partes.append(
                "Há ALTERAÇÃO expressa posterior. A redação original armazenada "
                "aqui não deve ser apresentada como atual sem examinar o ato "
                "alterador e eventuais alterações subsequentes."
            )
        situacao = " ".join(partes) or (
            "Nenhuma revogação ou alteração expressa localizada no acervo — o que "
            "não equivale a vigência; veja `advertencia`."
        )

        return {
            "ato": ato.para_dict(),
            "situacao_no_acervo": situacao,
            "revogado_integralmente_por": integrais,
            "revogado_parcialmente_por": parciais,
            "revogado_por": revogacoes,
            "alterado_por": alteracoes,
            "regulamentado_por": recebidas.get("regulamenta", []),
            "o_que_este_ato_faz_com_outros": feitas,
            "advertencia": (
                "Isto NÃO é certidão de vigência. O acervo registra apenas "
                "revogações e alterações EXPRESSAS que foram citadas no texto de "
                "outro ato aqui presente. Ficam de fora: a revogação tácita (a "
                "cláusula 'revogam-se as disposições em contrário' está em quase "
                "todo ato e não diz o que revoga), a norma superveniente estadual "
                "ou federal, a declaração de inconstitucionalidade, e qualquer ato "
                "dos anos ausentes desta base. Ausência de registro aqui não é "
                "prova de vigência."
            ),
        }

    # -- cobertura --------------------------------------------------------

    def cobertura(self) -> dict[str, Any]:
        linha = self.conexao.execute(
            "SELECT valor FROM acervo_info WHERE chave = 'resumo'"
        ).fetchone()
        resumo = json.loads(linha["valor"]) if linha else {}

        por_ano = [
            {"ano": a, "atos": n}
            for a, n in self.conexao.execute(
                "SELECT ano, COUNT(*) FROM atos GROUP BY ano ORDER BY ano"
            )
        ]
        return {
            "fonte": "Portal da Transparência da Prefeitura de Mesquita/RJ — "
                     "leis e decretos municipais publicados.",
            "total_de_atos": resumo.get("total_de_atos"),
            "por_especie": resumo.get("por_especie"),
            "com_texto_integral": resumo.get("com_texto_integral"),
            "sem_texto_extraido": resumo.get("sem_texto_extraido"),
            "paginas_indexadas": resumo.get("paginas"),
            "caracteres": resumo.get("caracteres"),
            "por_ano": por_ano,
            "grafo_de_vigencia": {
                "referencias_resolvidas": resumo.get("referencias_municipais"),
                "atos_com_revogacao_integral": resumo.get(
                    "atos_com_revogacao_integral"),
                "atos_com_revogacao_parcial": resumo.get(
                    "atos_com_revogacao_parcial"),
            },
            "lacunas_conhecidas": resumo.get("lacunas"),
            "limites_do_acervo": [
                "Este acervo é uma CÓPIA de trabalho do que o Portal da "
                "Transparência publicou, não o repositório oficial. Antes de "
                "protocolar peça, confira o texto no Diário Oficial do Município.",
                "O texto guardado é o ORIGINAL de cada ato, na redação publicada. "
                "Não há texto compilado: uma lei alterada dez vezes aparece aqui "
                "como foi promulgada, e as alterações estão em atos separados.",
                "Há anos sem nenhum decreto e anos com pouquíssimos — veja "
                "`lacunas_conhecidas`. A ausência de um ato aqui NÃO significa que "
                "ele não exista.",
                "Não estão no acervo: a Lei Orgânica do Município, portarias, "
                "resoluções, instruções normativas e atos da Câmara Municipal.",
                "Alguns PDFs são digitalizações sem texto; esses atos constam com "
                "ementa mas sem texto integral pesquisável.",
            ],
        }

    # -- montagem ---------------------------------------------------------

    def _ato(self, linha: sqlite3.Row, achado: str) -> Ato:
        colunas = linha.keys()
        return Ato(
            id=linha["id"],
            tipo=linha["tipo"],
            numero=linha["numero"],
            ano=linha["ano"],
            data=linha["data"],
            ementa=linha["ementa"] or "",
            ementa_fonte=linha["ementa_fonte"] if "ementa_fonte" in colunas else None,
            autor=linha["autor"],
            trecho=re.sub(r"\s+", " ", achado or "").strip(),
            caracteres=linha["caracteres"] or 0,
            arquivo=linha["arquivo"],
            paginas=linha["paginas"] or 0,
            fonte=linha["fonte"],
            diario_numero=linha["diario_numero"],
            diario_data=linha["diario_data"],
            url_origem=linha["url_origem"],
            situacao=linha["situacao"] or "",
        )
