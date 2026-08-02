"""Compara dois acervos, ato a ato.

Este módulo existe porque o total agregado mente. Três vezes neste projeto uma
correção do extrator fez o número de atos com texto **subir** enquanto atos
reais desapareciam — numa delas, sete leis complementares, entre elas a que
altera o Código Tributário. Nenhuma foi pega por teste: em todas eu estava
consertando algo verdadeiro, e a métrica melhorava.

O que pega é comparar registro a registro contra a versão anterior. Por isso o
diff não é script de apoio: é a etapa que autoriza publicar.

    python -m legis.comparar acervo/legislacao-mesquita-v1.2.0.db.gz \
        dados/mesquita.sqlite
"""

from __future__ import annotations

import gzip
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Encolher não é sinônimo de perder: um ato que encolheu 90% pode ter parado de
# engolir o ato seguinte. Abaixo deste fator o caso vai ao relatório para ser
# lido, não para ser condenado.
FATOR_DE_ENCOLHIMENTO = 0.6


def abrir(caminho: Path) -> tuple[sqlite3.Connection, Path | None]:
    """Abre um acervo em .sqlite ou .db.gz, descomprimindo se preciso."""
    caminho = Path(caminho)
    temporario = None
    if caminho.suffix == ".gz":
        temporario = Path(tempfile.mkdtemp()) / "acervo.sqlite"
        with gzip.open(caminho, "rb") as entrada, temporario.open("wb") as saida:
            shutil.copyfileobj(entrada, saida, length=4 << 20)
        caminho = temporario
    conexao = sqlite3.connect(f"file:{caminho.as_posix()}?mode=ro", uri=True)
    conexao.row_factory = sqlite3.Row
    return conexao, temporario


def _atos(conexao: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    return {
        linha["id"]: dict(linha)
        for linha in conexao.execute(
            "SELECT id, ementa, caracteres, situacao, arquivo, data, tipo, "
            "numero, ano FROM atos"
        )
    }


def _revogados(conexao: sqlite3.Connection) -> set[tuple[str, str, str]]:
    return {
        (l["origem_id"], l["relacao"], l["alvo_id"])
        for l in conexao.execute(
            "SELECT origem_id, relacao, alvo_id FROM referencias "
            "WHERE esfera = 'municipal' AND alvo_id IS NOT NULL"
        )
    }


@dataclass(slots=True)
class Comparacao:
    total_antes: int = 0
    total_depois: int = 0
    surgiram: list[dict] = field(default_factory=list)
    sumiram: list[dict] = field(default_factory=list)
    ganharam: list[dict] = field(default_factory=list)
    perderam: list[dict] = field(default_factory=list)
    encolheram: list[dict] = field(default_factory=list)
    referencias_antes: int = 0
    referencias_depois: int = 0
    referencias_perdidas: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def exige_leitura(self) -> bool:
        """Há algo que ninguém deveria publicar sem olhar?

        Sumiço, perda de texto e encolhimento grande são os três sinais que já
        esconderam regressão neste projeto. Surgir ato novo, não: é o que a
        atualização deveria fazer.
        """
        return bool(self.sumiram or self.perderam or self.encolheram
                    or self.referencias_perdidas)


def comparar(antes: Path, depois: Path) -> Comparacao:
    conexao_a, tmp_a = abrir(antes)
    conexao_b, tmp_b = abrir(depois)
    try:
        antigos, novos = _atos(conexao_a), _atos(conexao_b)
        resultado = Comparacao(total_antes=len(antigos), total_depois=len(novos))

        for identificador in sorted(set(novos) - set(antigos)):
            resultado.surgiram.append(novos[identificador])
        for identificador in sorted(set(antigos) - set(novos)):
            resultado.sumiram.append(antigos[identificador])

        for identificador in sorted(set(antigos) & set(novos)):
            a, b = antigos[identificador], novos[identificador]
            if a["situacao"] != "ok" and b["situacao"] == "ok":
                resultado.ganharam.append(b | {"antes": a["caracteres"]})
            elif a["situacao"] == "ok" and b["situacao"] != "ok":
                resultado.perderam.append(b | {"antes": a["caracteres"]})
            elif (a["situacao"] == "ok"
                  and b["caracteres"] < a["caracteres"] * FATOR_DE_ENCOLHIMENTO):
                resultado.encolheram.append(b | {"antes": a["caracteres"]})

        antigas, atuais = _revogados(conexao_a), _revogados(conexao_b)
        resultado.referencias_antes = len(antigas)
        resultado.referencias_depois = len(atuais)
        resultado.referencias_perdidas = sorted(antigas - atuais)
        return resultado
    finally:
        conexao_a.close()
        conexao_b.close()
        for temporario in (tmp_a, tmp_b):
            if temporario:
                shutil.rmtree(temporario.parent, ignore_errors=True)


def _linha(ato: dict, limite: int = 62) -> str:
    import re

    ementa = re.sub(r"\s+", " ", ato.get("ementa") or "").strip()[:limite]
    return f"`{ato['id']}` — {ementa or '(sem ementa)'}"


def relatorio(c: Comparacao, antes: Path, depois: Path) -> str:
    linhas = [
        "# Diferença entre acervos",
        "",
        f"- **antes:** `{antes}` — {c.total_antes} atos",
        f"- **depois:** `{depois}` — {c.total_depois} atos",
        "",
        "| | |",
        "|---|---|",
        f"| Atos que surgiram | {len(c.surgiram)} |",
        f"| Atos que sumiram | **{len(c.sumiram)}** |",
        f"| Ganharam texto | {len(c.ganharam)} |",
        f"| Perderam texto | **{len(c.perderam)}** |",
        f"| Encolheram mais de 40% | **{len(c.encolheram)}** |",
        f"| Referências no grafo | {c.referencias_antes} → {c.referencias_depois} |",
        "",
    ]

    if not c.exige_leitura:
        linhas += [
            "## Nada exige leitura",
            "",
            "Nenhum ato sumiu, nenhum perdeu texto, nenhum encolheu, e o grafo "
            "de vigência não perdeu aresta. O que mudou foi acréscimo.",
            "",
        ]
    else:
        linhas += [
            "## Exige leitura antes de publicar",
            "",
            "Os itens abaixo já esconderam regressão neste projeto. Encolher "
            "pode ser conserto — um ato que parou de engolir o seguinte —, mas "
            "isso se afirma lendo, não contando.",
            "",
        ]

    if c.surgiram:
        linhas += ["### Surgiram", ""]
        for ato in c.surgiram:
            linhas.append(f"- {_linha(ato)} — {ato['caracteres']} c, "
                          f"{ato.get('data') or 'sem data'}")
        linhas.append("")

    for titulo, itens, nota in (
        ("Sumiram", c.sumiram, "existiam antes e não existem agora"),
        ("Perderam o texto", c.perderam, "tinham texto e ficaram sem"),
        ("Encolheram", c.encolheram, "conferir se o vizinho apareceu"),
    ):
        if not itens:
            continue
        linhas += [f"### {titulo} — {nota}", ""]
        for ato in itens:
            antes_c = ato.get("antes", "?")
            linhas.append(f"- {_linha(ato)} — {antes_c} → {ato['caracteres']} c")
        linhas.append("")

    if c.referencias_perdidas:
        linhas += [
            "### Arestas do grafo de vigência que sumiram", "",
            "Conferir de onde vinha cada uma: aresta extraída de documento "
            "alheio é conserto; de artigo do próprio ato, é perda.", "",
        ]
        for origem, relacao, alvo in c.referencias_perdidas[:40]:
            linhas.append(f"- `{origem}` —{relacao}→ `{alvo}`")
        if len(c.referencias_perdidas) > 40:
            linhas.append(f"- … e mais {len(c.referencias_perdidas) - 40}")
        linhas.append("")

    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    import argparse

    analisador = argparse.ArgumentParser(
        prog="python -m legis.comparar",
        description="Compara dois acervos ato a ato. Aceita .sqlite ou .db.gz.",
    )
    analisador.add_argument("antes")
    analisador.add_argument("depois")
    analisador.add_argument("--salvar", metavar="ARQUIVO",
                            help="grava o relatório em Markdown")
    argumentos = analisador.parse_args(argv)

    comparacao = comparar(Path(argumentos.antes), Path(argumentos.depois))
    texto = relatorio(comparacao, Path(argumentos.antes), Path(argumentos.depois))
    print(texto)
    if argumentos.salvar:
        Path(argumentos.salvar).write_text(texto, encoding="utf-8")
        print(f"\nrelatório em {argumentos.salvar}")

    # Código de saída como sinal: 0 quando nada exige leitura, 1 quando exige.
    # Serve para a tarefa agendada avisar sem que ninguém precise ler o texto.
    return 1 if comparacao.exige_leitura else 0


if __name__ == "__main__":
    raise SystemExit(main())
