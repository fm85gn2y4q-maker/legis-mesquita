"""Rotina semanal: baixa o Diário novo, reprocessa e compara. Não publica.

A divisão é deliberada. Baixar, reprocessar e comparar são mecânicos e podem
rodar sozinhos. **Publicar não.** Três vezes neste projeto uma correção do
extrator fez o número de atos com texto subir enquanto atos reais sumiam — numa
delas, sete leis complementares. Um pipeline que publicasse sozinho teria
levado isso ao ar com uma tabela de melhorias para justificar.

Por isso esta rotina termina num relatório e num código de saída:

    0  nada exige leitura — só acréscimo
    1  algo sumiu, perdeu texto ou encolheu — alguém precisa olhar
    2  a coleta ou o reprocessamento falhou

O acervo publicado não é tocado. O novo fica em `dados/staging.sqlite` até
alguém decidir promovê-lo.

    python atualizar.py                 # ciclo completo
    python atualizar.py --sem-baixar    # só reprocessa e compara
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PYTHON = sys.executable
DIARIOS = Path(os.path.expanduser("~/Mesquita_Diarios_Oficiais"))
LEGISLACAO = Path(os.path.expanduser("~/Mesquita_Legislacao"))
STAGING = RAIZ / "dados" / "staging.sqlite"

# Reler edição já lida é barato — a deduplicação por conteúdo resolve — e a
# margem protege contra ato publicado com atraso ou republicado. Perder um ato
# por economia de dias seria a pior troca possível.
MARGEM_DE_DIAS = 21


def publicado() -> Path:
    """O `.db.gz` que está no ar, e que serve de base de comparação."""
    candidatos = sorted((RAIZ / "acervo").glob("*.db.gz"))
    if not candidatos:
        raise SystemExit("Nenhum acervo publicado em acervo/. Nada a comparar.")
    return candidatos[-1]


def corte(acervo: Path) -> str:
    """Data a partir da qual reler o Diário, com margem para trás."""
    from legis.comparar import abrir

    conexao, temporario = abrir(acervo)
    try:
        ultima = conexao.execute(
            "SELECT MAX(data) FROM atos WHERE data IS NOT NULL").fetchone()[0]
    finally:
        conexao.close()
        if temporario:
            import shutil
            shutil.rmtree(temporario.parent, ignore_errors=True)

    if not ultima:
        return "2026-01-01"
    quando = datetime.strptime(ultima, "%Y-%m-%d").date() - timedelta(
        days=MARGEM_DE_DIAS)
    return quando.isoformat()


def rodar(comando: list[str], onde: Path) -> int:
    print(f"\n$ {' '.join(str(x) for x in comando)}", flush=True)
    return subprocess.run(comando, cwd=onde).returncode


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(prog="python atualizar.py")
    analisador.add_argument("--sem-baixar", action="store_true",
                            help="pula a coleta e só reprocessa")
    analisador.add_argument("--desde", metavar="AAAA-MM-DD",
                            help="força a data de corte da leitura do Diário")
    argumentos = analisador.parse_args(argv)

    sys.path.insert(0, str(RAIZ))
    atual = publicado()
    desde = argumentos.desde or corte(atual)
    print(f"acervo publicado: {atual.name}")
    print(f"relendo o Diário a partir de {desde} "
          f"(margem de {MARGEM_DE_DIAS} dias)")

    if not argumentos.sem_baixar:
        coletor = DIARIOS / "baixar_diarios.py"
        if not coletor.exists():
            print(f"Coletor não encontrado em {coletor}", file=sys.stderr)
            return 2
        codigo = rodar([PYTHON, str(coletor), "--fonte", "municipio",
                        "--ano-inicial", str(date.today().year)], DIARIOS)
        if codigo != 0:
            print("A coleta falhou; nada foi reprocessado.", file=sys.stderr)
            return 2

    STAGING.parent.mkdir(parents=True, exist_ok=True)
    codigo = rodar([PYTHON, "-m", "legis.ingestao",
                    "--pasta", str(LEGISLACAO),
                    "--banco", str(STAGING),
                    "--diarios", str(DIARIOS / "municipio"),
                    "--desde", desde], RAIZ)
    if codigo != 0:
        print("O reprocessamento falhou.", file=sys.stderr)
        return 2

    from legis.comparar import comparar, relatorio

    comparacao = comparar(atual, STAGING)
    texto = relatorio(comparacao, atual, STAGING)

    destino = RAIZ / "dist" / f"diferenca-{date.today():%Y-%m-%d}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")

    print("\n" + "─" * 70)
    print(texto)
    print("─" * 70)
    print(f"\nrelatório em {destino}")
    print(f"acervo novo em {STAGING} — o publicado não foi tocado")

    if comparacao.exige_leitura:
        print("\nHÁ O QUE LER antes de publicar. Nada foi enviado.")
        return 1

    if not comparacao.surgiram:
        print("\nNada mudou. Não há o que publicar.")
        return 0

    print(f"\n{len(comparacao.surgiram)} ato(s) novo(s), e nada a perder.")
    print("Para publicar:")
    print("  1. copy dados\\staging.sqlite dados\\mesquita.sqlite")
    print("  2. python preparar_release.py <versão>")
    print("  3. mover o .gz para acervo/, apagar o anterior,")
    print("     trocar as duas linhas ARG do Dockerfile")
    print("  4. git add -A && git commit && git push  (o Render reconstrói)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
