"""Vigia o Diário Oficial e diz se há ato que o acervo publicado não tem.

Feito para rodar **na nuvem**, onde os 7,5 GB de PDFs da máquina do usuário não
existem. O que existe é o acervo comprimido versionado em `acervo/`, e o portal
do Município, que é público. Com esses dois basta para responder à única
pergunta que interessa numa rotina semanal:

    há lei ou decreto novo que ainda não está no acervo?

O que este programa **não** faz é atualizar o acervo. A ingestão reconstrói tudo
do zero e depende dos PDFs por ato, que só existem na máquina do usuário. Quem
atualiza é `atualizar.py`, lá. Aqui só se avisa que vale ligar a máquina.

    python vigiar.py                 # últimos 30 dias
    python vigiar.py --dias 60
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def acervo_publicado() -> Path:
    candidatos = sorted((RAIZ / "acervo").glob("*.db.gz"))
    if not candidatos:
        raise SystemExit("Nenhum acervo em acervo/. Nada com que comparar.")
    return candidatos[-1]


def baixar(destino: Path, desde: date) -> int:
    """Traz as edições do ano corrente. O coletor já pula o que existe."""
    coletor = RAIZ / "baixar_diarios.py"
    anos = sorted({desde.year, date.today().year})
    return subprocess.run(
        [sys.executable, str(coletor), "--fonte", "municipio",
         "--ano-inicial", str(anos[0]), "--ano-final", str(anos[-1]),
         "--destino", str(destino)],
        cwd=RAIZ,
    ).returncode


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(prog="python vigiar.py")
    analisador.add_argument("--dias", type=int, default=30,
                            help="quantos dias de Diário examinar (padrão: 30)")
    analisador.add_argument("--pasta", metavar="PASTA",
                            help="acervo de Diários já baixado; sem isto, baixa "
                                 "para um diretório temporário")
    argumentos = analisador.parse_args(argv)

    sys.path.insert(0, str(RAIZ))
    from legis.comparar import abrir
    from legis.ingestao import segmentar

    publicado = acervo_publicado()
    conexao, temporario_db = abrir(publicado)
    try:
        conhecidos = {linha[0] for linha in conexao.execute("SELECT id FROM atos")}
        total = len(conhecidos)
    finally:
        conexao.close()
        if temporario_db:
            import shutil
            shutil.rmtree(temporario_db.parent, ignore_errors=True)

    print(f"acervo publicado: {publicado.name} — {total} atos")

    desde = date.today() - timedelta(days=argumentos.dias)
    print(f"examinando o Diário desde {desde.isoformat()}")

    if argumentos.pasta:
        pasta = Path(argumentos.pasta)
        efemera = None
    else:
        efemera = Path(tempfile.mkdtemp(prefix="diarios-"))
        pasta = efemera
        if baixar(pasta, desde) not in (0, 1):
            print("A coleta falhou.", file=sys.stderr)
            return 2

    padrao = re.compile(r"DOM_(\d{4}-\d{2}-\d{2})_\d+\.pdf$", re.IGNORECASE)
    edicoes = []
    for caminho in sorted(pasta.rglob("DOM_*.pdf")):
        achado = padrao.search(caminho.name)
        if achado and achado.group(1) >= desde.isoformat():
            edicoes.append(caminho)
    print(f"edições no período: {len(edicoes)}")

    novos: dict[str, tuple[str, str]] = {}
    for caminho in edicoes:
        for segmento in segmentar(caminho, caminho.name):
            identificador = f"{segmento.tipo}-{segmento.numero}-{segmento.ano}"
            if identificador in conhecidos or identificador in novos:
                continue
            novos[identificador] = (caminho.name, segmento.ementa[:160])

    print()
    if not novos:
        print("NADA NOVO. O acervo publicado está em dia com o Diário.")
        return 0

    print(f"{len(novos)} ATO(S) QUE O ACERVO NÃO TEM:\n")
    for identificador, (arquivo, ementa) in sorted(novos.items()):
        print(f"  {identificador}")
        print(f"     {ementa or '(sem ementa)'}")
        print(f"     em {arquivo}")
    print("\nPara incorporar, na máquina onde estão os PDFs por ato:")
    print("  python atualizar.py     # baixa, reprocessa e mostra o diff")
    print("\nEsta verificação NÃO atualiza o acervo — ela só avisa.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
