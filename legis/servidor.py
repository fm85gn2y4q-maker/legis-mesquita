"""Servidor MCP da legislação municipal de Mesquita.

Fala os dois transportes porque os clientes divergem: o Claude conversa por
stdio com um processo local, enquanto o ChatGPT só aceita servidor remoto por
HTTP.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .acervo import ROTULOS, Acervo

_LOCAIS = ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"]

ESPECIES = {"lei", "lei_complementar", "decreto"}


def seguranca_de_transporte(dominios: list[str] | None) -> TransportSecuritySettings:
    """Monta a política de Host/Origin aceitos.

    O SDK bloqueia por padrão qualquer Host que não seja local — é proteção
    contra DNS rebinding, e sem ela um site malicioso poderia falar com o
    servidor pelo navegador da vítima. Servir por um endereço público exige
    declarar o domínio aqui; não há curinga, a comparação é exata.
    """
    hosts = list(_LOCAIS)
    origens = [f"http://{h}" for h in _LOCAIS if "*" not in h]

    for dominio in dominios or []:
        limpo = dominio.strip().removeprefix("https://").removeprefix("http://")
        limpo = limpo.rstrip("/")
        if not limpo:
            continue
        hosts += [limpo, f"{limpo}:*"]
        origens.append(f"https://{limpo}")

    if dominios:
        origens += ["https://chatgpt.com", "https://chat.openai.com"]

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origens,
    )


INSTRUCOES = """
Legislação do Município de Mesquita/RJ: leis ordinárias, leis complementares e
decretos municipais, coletados do Portal da Transparência da Prefeitura.

Como responder ao advogado:
- Entregue a norma e a análise, não o funcionamento da ferramenta. Não cite
  nomes de tools, identificadores internos nem estrutura de URL.
- Cite no formato do campo `citacao` — é a referência que vai para a peça.
- Chame `cobertura_do_acervo` quando precisar saber o alcance da base, e
  declare os limites que afetarem a resposta.

A REGRA QUE NÃO PODE SER QUEBRADA: VIGÊNCIA

Um precedente envelhece; uma norma morre. O acórdão de 2008 continua sendo o
que era — a Lei 460/2008 foi revogada em 2019, e citá-la hoje como fundamento
é erro que o cliente paga. A busca textual devolve norma viva e norma revogada
com exatamente a mesma confiança: nada no texto de uma lei revogada avisa que
ela foi.

**Antes de apresentar qualquer norma como fundamento, chame
`verificar_vigencia`.** Sempre. Inclusive quando a norma for recente — lei de
2023 pode ter sido alterada em 2024.

O que a ferramenta devolve, e o que ela NÃO devolve:

- Devolve as revogações e alterações **expressas** que outro ato do acervo
  declarou. Isso é fato verificável, e vem com o trecho que o indica.
- NÃO devolve "está em vigor". Nenhuma consulta a esta base autoriza essa
  afirmação. Ficam fora: a revogação tácita (a cláusula "revogam-se as
  disposições em contrário" está em quase todo ato e não diz o que revoga),
  a norma estadual ou federal superveniente, a declaração de
  inconstitucionalidade, e tudo que esteja nos anos ausentes da base.

Três situações, três frases diferentes — não as confunda, e **nenhuma delas se
enuncia como afirmação sobre o estado atual da norma**:

- `revogado_integralmente_por`: há revogação expressa integral localizada. Não
  use esta norma como fundamento sem antes ler o ato revogador.
- `revogado_parcialmente_por`: a revogação expressa localizada é **parcial** e
  não autoriza tratar a norma como integralmente revogada; quanto ao restante,
  não foi localizada revogação expressa no acervo. Leia o `trecho_que_indica`
  para saber QUAIS dispositivos caíram, e confira se o que você pretende citar
  é um deles. Dizer aqui que "a norma foi revogada" seria falso — e dizer que
  "continua em vigor" seria afirmar mais do que a base sustenta.
- `alterado_por`: há alteração expressa posterior. A redação original
  armazenada aqui **não deve ser apresentada como atual** sem examinar o ato
  alterador e eventuais alterações subsequentes.

As três podem ocorrer juntas na mesma norma. Havendo revogação parcial *e*
alterações, diga as duas coisas.

Então diga "não localizei revogação expressa", nunca "está em vigor". A
diferença entre as duas frases é a diferença entre uma pesquisa e uma
garantia — e você não pode dar a garantia.

TEXTO ORIGINAL, NÃO TEXTO COMPILADO

O que está guardado aqui é o ato **como foi publicado**. Não há redação
consolidada. Uma lei alterada cinco vezes aparece com o texto de origem, e as
cinco alterações são cinco outros atos.

Consequência prática: achando o dispositivo que responde à pergunta, verifique
se aquele artigo foi alterado antes de transcrevê-lo. Transcrever redação
revogada como se fosse a vigente é o erro mais fácil de cometer nesta base, e
o mais difícil de o leitor perceber — o texto parece perfeito.

ESPÉCIE NORMATIVA: DIGA DE ONDE VEIO A REGRA — SEM INVENTAR HIERARQUIA

- **Lei Orgânica**: parâmetro fundamental da legislação municipal e fonte das
  reservas de matéria e das competências locais. **Não está neste acervo.**
  Dependendo a questão dela, avise que a conferência é fora daqui.
- **Lei complementar e lei ordinária**: **não há superioridade hierárquica
  genérica entre as duas.** O que distingue a lei complementar é o processo
  legislativo e, sobretudo, a matéria a ela reservada. A pergunta correta nunca
  é "qual espécie é superior", e sim *aquela matéria está reservada à lei
  complementar?*
- **Decreto**: ato infralegal, subordinado à lei e aos limites da competência
  regulamentar. Regra que só exista em decreto e restrinja direito é atacável
  por isso.

Cuidado com a objeção fácil e errada: encontrando lei ordinária que altera lei
complementar, **não conclua pela invalidade só por causa da espécie**. Isso
depende de haver reserva de lei complementar para aquela matéria — e a norma
que estabelece as reservas no Município é a Lei Orgânica, que não está aqui.
Aponte a questão ao advogado, dizendo o que seria preciso verificar; não a
resolva com uma escada que não existe.

Quando a resposta se apoiar em decreto, diga com todas as letras que é decreto
e, havendo lei sobre a matéria, apresente-a.

DUAS BUSCAS, PROPOSITALMENTE SEPARADAS

- `pesquisar_legislacao` procura na **ementa** — o que a norma diz de si
  mesma. Serve para achar qual norma trata do assunto.
- `pesquisar_dispositivos` procura no **corpo do ato**, e devolve a página. É
  onde a regra está.

A ementa do Código Tributário tem uma linha; as regras estão nas 155 páginas
seguintes. Perguntas sobre o que a norma *determina* quase sempre se respondem
pela segunda busca. Não encontrando na ementa, procure no corpo antes de
concluir que o Município não legislou.

UMA PERGUNTA, VÁRIAS FORMULAÇÕES

A busca é literal. Uma só tradução da pergunta em consulta pode falhar por
motivo puramente lexical: o vocabulário do legislador municipal raramente é o
da pergunta. "Posso construir a dois metros da divisa?" não acha nada;
"afastamento lateral" e "recuo" acham.

1. **Preserve a consulta inicial.** As variantes acrescentam, não substituem.
2. **Reformule quando o resultado for fraco ou lateral.** Sinais: os primeiros
   resultados tratam de assunto diverso; os termos aparecem dispersos sem
   formar a relação jurídica perguntada; a leitura do melhor resultado mostra
   que ele não responde.
3. **Variante é o mesmo problema com outro vocabulário, nunca a resposta
   presumida.** Vale trocar "imposto sobre serviço" por "ISS" ou "ISSQN";
   não vale embutir na consulta a conclusão que se quer encontrar.
4. **Antes de dizer que não há norma, tente ao menos uma variante** e a busca
   no corpo do ato.

O campo `expressao_executada` traz a expressão de fato usada. Registre por qual
formulação cada norma apareceu — serve para o advogado refazer a pesquisa.

COMO APRESENTAR CADA NORMA — os quatro itens, nesta ordem:

1. **Citação.** Exatamente o campo `citacao`: espécie, número e data por
   extenso, no formato de peça.
2. **Do que trata.** Uma ou duas frases a partir da ementa.
3. **O dispositivo e como se aplica.** Transcreva o artigo pertinente e diga
   em que ele ajuda ou atrapalha a questão. Norma contrária ao que o advogado
   busca, diga com todas as letras — norma contrária conhecida a tempo vale
   mais do que norma favorável que não se sustenta.
4. **Situação e conferência.** O resultado de `verificar_vigencia` e onde
   conferir o texto oficial (`publicacao` traz o número e a data do Diário
   Oficial; `url_origem`, o PDF como foi coletado — apresente-o como
   "[Texto no portal](url)", sem comentar o formato do endereço).

Nunca cite uma norma sem os quatro. Citação sem dispositivo obriga o advogado
a abrir tudo; dispositivo sem verificação de vigência é armadilha.

LIMITES QUE NÃO PODEM SER OMITIDOS QUANDO IMPORTAREM

- A base é cópia de trabalho do Portal da Transparência, não o repositório
  oficial. Para protocolar, confira no Diário Oficial do Município.
- Há anos sem nenhum decreto e anos com pouquíssimos. Ausência aqui não é
  prova de inexistência — consulte `cobertura_do_acervo` antes de afirmar que
  o Município não tratou de um assunto.
- Não estão no acervo: Lei Orgânica, portarias, resoluções, instruções
  normativas e atos da Câmara Municipal.
- Alguns PDFs são digitalizações sem texto: o ato consta com ementa, mas sem
  texto pesquisável. O campo `texto_integral_disponivel` diz quando é o caso,
  e nesse caso a ausência de um dispositivo na busca não significa nada.
""".strip()


def _caminho_padrao() -> Path:
    if os.environ.get("LEGIS_BANCO"):
        return Path(os.environ["LEGIS_BANCO"])
    return Path(__file__).resolve().parent.parent / "dados" / "mesquita.sqlite"


def _especie(bruta: str | None) -> str | None:
    """Aceita 'Lei', 'lei', 'Lei Complementar', 'decreto'."""
    if not bruta:
        return None
    chave = bruta.strip().lower().replace(" ", "_").replace("ó", "o")
    if chave in {"lei_ordinaria", "leis"}:
        chave = "lei"
    if chave in {"decretos"}:
        chave = "decreto"
    if chave in {"lc", "leis_complementares"}:
        chave = "lei_complementar"
    return chave if chave in ESPECIES else None


def construir(
    banco: str | Path | None = None,
    dominios: list[str] | None = None,
    url_publica: str | None = None,
    segredo_oauth: str | None = None,
    **ajustes: Any,
) -> FastMCP:
    acervo = Acervo(banco or _caminho_padrao())

    # O ChatGPT recusa servidor MCP sem OAuth; o Claude conecta sem. O fluxo só
    # é montado quando há URL pública, porque os metadados precisam apontar
    # para endereços que o cliente alcance.
    if url_publica:
        from .autenticacao import montar

        provedor, definicoes = montar(url_publica, segredo_oauth)
        ajustes |= {"auth_server_provider": provedor, "auth": definicoes}

    mcp = FastMCP(
        "legislacao-mesquita",
        instructions=INSTRUCOES,
        transport_security=seguranca_de_transporte(dominios),
        **ajustes,
    )

    @mcp.tool()
    def pesquisar_legislacao(
        consulta: str,
        especie: str | None = None,
        ano_min: int | None = None,
        ano_max: int | None = None,
        limite: int = 10,
    ) -> dict[str, Any]:
        """Procura normas de Mesquita pela ementa — do que a norma trata.

        Busca sem sensibilidade a acento ("iluminacao" acha "iluminação") e
        combina os termos com E. Para expressão exata, use aspas dentro da
        própria consulta: 'taxa "coleta de lixo"'.

        Args:
            consulta: palavras ou expressão a procurar na ementa.
            especie: filtra por lei, lei_complementar ou decreto.
            ano_min: ano mais antigo aceito.
            ano_max: ano mais recente aceito.
            limite: quantos resultados devolver (máximo 50).
        """
        achados, parcial, expressao = acervo.pesquisar(
            consulta, especie=_especie(especie), ano_min=ano_min,
            ano_max=ano_max, limite=limite,
        )
        if not achados:
            observacao = (
                "Nada na ementa. Antes de concluir que o Município não legislou, "
                "procure no corpo dos atos com `pesquisar_dispositivos` e tente "
                "uma variante lexical — a ementa costuma ser genérica."
            )
        elif parcial:
            observacao = (
                "Nenhuma ementa reunia todos os termos; estas atendem a parte "
                "deles, ordenadas por relevância."
            )
        else:
            observacao = None

        return {
            "consulta": consulta,
            "expressao_executada": expressao,
            "quantidade": len(achados),
            "correspondencia_parcial": parcial,
            "resultados": [a.para_dict() for a in achados],
            "observacao": observacao,
            "lembrete": "Verifique a vigência antes de citar qualquer uma delas.",
        }

    @mcp.tool()
    def pesquisar_dispositivos(
        consulta: str,
        especie: str | None = None,
        ano_min: int | None = None,
        ano_max: int | None = None,
        limite: int = 10,
    ) -> dict[str, Any]:
        """Procura dentro do texto dos atos, não nas ementas.

        É onde a regra está: a ementa diz que a lei "dispõe sobre o Código
        Tributário", e o que interessa são os artigos. Cada resultado traz a
        página, para conferência no documento publicado.

        Args:
            consulta: palavras ou expressão a procurar no corpo dos atos.
            especie: filtra por lei, lei_complementar ou decreto.
            ano_min: ano mais antigo aceito.
            ano_max: ano mais recente aceito.
            limite: quantos trechos devolver (máximo 30).
        """
        achados, parcial, expressao = acervo.pesquisar_texto(
            consulta, especie=_especie(especie), ano_min=ano_min,
            ano_max=ano_max, limite=limite,
        )
        if not achados:
            observacao = (
                "Nada com esta formulação. A busca é literal: o legislador "
                "municipal pode nomear o mesmo instituto com outras palavras. "
                "Tente ao menos uma variante antes de concluir."
            )
        elif parcial:
            observacao = (
                "Nenhuma página reunia todos os termos; estas atendem a parte "
                "deles. Veja `termos_encontrados` para saber o que casou."
            )
        else:
            observacao = None

        return {
            "consulta": consulta,
            "expressao_executada": expressao,
            "quantidade": len(achados),
            "correspondencia_parcial": parcial,
            "resultados": [p.para_dict() for p in achados],
            "observacao": observacao,
            "lembrete": (
                "O texto guardado é o ORIGINAL do ato. Antes de transcrever o "
                "artigo, verifique com `verificar_vigencia` se ele foi alterado."
            ),
        }

    @mcp.tool()
    def verificar_vigencia(id: str) -> dict[str, Any]:
        """Mostra o que outros atos do acervo fizeram com esta norma.

        Etapa obrigatória antes de apresentar qualquer norma como fundamento.
        Devolve revogações, alterações e regulamentações **expressas**, com o
        trecho que as indica — e não devolve "está em vigor", porque esta base
        não autoriza tal afirmação. Leia o campo `advertencia`.

        Args:
            id: identificador do ato, vindo de uma pesquisa anterior.
        """
        return acervo.vigencia(id)

    @mcp.tool()
    def localizar_norma(
        especie: str, numero: int, ano: int | None = None
    ) -> dict[str, Any]:
        """Localiza um ato pela referência que o advogado já tem em mãos.

        Para quando a citação vem de outra peça, de um ofício ou do processo:
        "Lei 1.106/2019", "Decreto nº 3.128".

        Args:
            especie: lei, lei_complementar ou decreto.
            numero: número do ato.
            ano: ano do ato; omita se não souber.
        """
        chave = _especie(especie)
        if chave is None:
            return {"erro": "Espécie deve ser lei, lei_complementar ou decreto."}
        achados = acervo.por_numero(chave, numero, ano)
        if not achados:
            return {
                "erro": f"Não localizado: {especie} {numero}"
                        + (f"/{ano}" if ano else ""),
                "observacao": (
                    "Pode existir e não estar nesta base — consulte "
                    "`cobertura_do_acervo` para os anos ausentes."
                ),
            }
        return {
            "quantidade": len(achados),
            "resultados": [a.para_dict() for a in achados],
            "lembrete": "Chame `verificar_vigencia` antes de usar.",
        }

    @mcp.tool()
    def ler_texto(id: str, pagina: int = 1, quantidade: int = 3) -> dict[str, Any]:
        """Lê o texto do ato, página a página.

        O raciocínio de um artigo atravessa a quebra de página: ler só a página
        que casou mostra o caput sem os parágrafos, ou a exceção sem a regra.

        Args:
            id: identificador do ato.
            pagina: primeira página a ler.
            quantidade: quantas páginas a partir dela (até 10).
        """
        fim = pagina + max(1, min(quantidade, 10)) - 1
        paginas = acervo.paginas_do_ato(id, pagina, fim)
        ato = acervo.obter(id)
        if ato is None:
            return {"erro": f"Ato não encontrado: {id}"}
        if not paginas:
            texto = acervo.texto_do_ato(id)
            if not texto:
                return {
                    "citacao": ato.citacao,
                    "erro": "Este ato não tem texto extraído — o PDF de origem é "
                            "digitalização sem camada de texto.",
                    "url_origem": ato.url_origem,
                }
            paginas = [{"pagina": 1, "pagina_no_pdf": None, "texto": texto}]
        return {
            "citacao": ato.citacao,
            "ementa": ato.ementa,
            "publicacao": ato.conferencia,
            "url_origem": ato.url_origem,
            "total_de_paginas": ato.paginas,
            "paginas": paginas,
            "lembrete": (
                "Redação ORIGINAL. Confira alterações com `verificar_vigencia` "
                "antes de transcrever."
            ),
        }

    @mcp.tool()
    def obter_ato(id: str) -> dict[str, Any]:
        """Devolve os dados completos de um ato já localizado.

        Args:
            id: identificador vindo de uma pesquisa anterior.
        """
        achado = acervo.obter(id)
        if achado is None:
            return {"erro": f"Ato não encontrado: {id}"}
        return achado.para_dict()

    @mcp.tool()
    def listar_atos(
        especie: str | None = None, ano: int | None = None, limite: int = 20
    ) -> dict[str, Any]:
        """Lista atos por espécie e ano, sem termo de busca.

        Serve para varrer o acervo — por exemplo, todas as leis complementares,
        ou os decretos de um ano.

        Args:
            especie: lei, lei_complementar ou decreto.
            ano: ano exato.
            limite: quantos devolver (máximo 100).
        """
        achados = acervo.listar(especie=_especie(especie), ano=ano, limite=limite)
        return {
            "quantidade": len(achados),
            "resultados": [a.para_dict() for a in achados],
        }

    @mcp.tool()
    def listar_atos_sem_texto(
        especie: str | None = None, ano: int | None = None
    ) -> dict[str, Any]:
        """Lista os atos que constam do acervo mas não têm texto pesquisável.

        São os pontos cegos da base: existem, têm ementa, e o corpo não foi
        extraído. Uma busca por dispositivo que não encontre nada em nenhum
        deles **não significa que a regra não exista** — significa que aquele
        texto não está indexado.

        Consulte antes de afirmar que o Município não tratou de um assunto, e
        sempre que a norma que interessa ao caso for de espécie e ano cobertos
        por esta lista.

        Args:
            especie: filtra por lei, lei_complementar ou decreto.
            ano: ano exato.
        """
        achados = acervo.sem_texto(especie=_especie(especie), ano=ano)
        por_ano: dict[int, int] = {}
        for ato in achados:
            por_ano[ato.ano] = por_ano.get(ato.ano, 0) + 1
        return {
            "quantidade": len(achados),
            "por_ano": dict(sorted(por_ano.items())),
            "resultados": [
                {"id": a.id, "citacao": a.citacao, "ementa": a.ementa,
                 "caracteres_extraidos": a.caracteres,
                 "url_origem": a.url_origem}
                for a in achados
            ],
            "observacao": (
                "A ementa destes atos é confiável — vem do catálogo do portal. "
                "O que falta é o corpo. Para o inteiro teor, abra o link de "
                "origem ou consulte o Diário Oficial."
            ),
        }

    @mcp.tool()
    def cobertura_do_acervo() -> dict[str, Any]:
        """Descreve o que existe na base: volumes, período, lacunas e limites.

        Consulte antes de afirmar que o Município não legislou sobre algo.
        """
        return acervo.cobertura()

    # -- Compatibilidade com os conectores do ChatGPT ---------------------
    # A pesquisa profunda espera exatamente `search` e `fetch`, com este
    # formato de retorno. São fachadas finas sobre as ferramentas acima.

    @mcp.tool()
    def search(query: str) -> dict[str, Any]:
        """Search municipal legislation of Mesquita/RJ by keyword.

        Args:
            query: words to look for in the legislation.
        """
        achados, _, _ = acervo.pesquisar(query, limite=10)
        passagens, _, _ = acervo.pesquisar_texto(query, limite=10)
        vistos, resultados = set(), []
        for ato in achados:
            vistos.add(ato.id)
            resultados.append({
                "id": ato.id, "title": ato.citacao,
                "text": ato.ementa[:400] or ato.trecho,
                "url": ato.url_origem or PORTAL_BUSCA,
            })
        for passagem in passagens:
            if passagem.ato.id in vistos:
                continue
            vistos.add(passagem.ato.id)
            resultados.append({
                "id": passagem.ato.id, "title": passagem.ato.citacao,
                "text": passagem.trecho,
                "url": passagem.ato.url_origem or PORTAL_BUSCA,
            })
        return {"results": resultados}

    @mcp.tool()
    def fetch(id: str) -> dict[str, Any]:
        """Fetch the full record of a Mesquita municipal act by its id.

        Args:
            id: identifier returned by `search`.
        """
        achado = acervo.obter(id)
        if achado is None:
            return {"id": id, "title": "não encontrado", "text": "", "url": "",
                    "metadata": {}}
        texto = acervo.texto_do_ato(id) or achado.ementa
        situacao = acervo.vigencia(id)
        return {
            "id": achado.id,
            "title": achado.citacao,
            "text": texto,
            "url": achado.url_origem or PORTAL_BUSCA,
            "metadata": {
                "especie": ROTULOS.get(achado.tipo, achado.tipo),
                "numero": str(achado.numero),
                "ano": str(achado.ano),
                "data": achado.data or "",
                "ementa": achado.ementa,
                "publicacao": achado.conferencia or "",
                "situacao_no_acervo": situacao.get("situacao_no_acervo", ""),
                "fonte": "Portal da Transparência de Mesquita/RJ",
            },
        }

    return mcp


PORTAL_BUSCA = "https://transparencia.mesquita.rj.gov.br"
