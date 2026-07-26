"""Comprime o acervo e imprime as duas linhas que vão para o Dockerfile.

O banco não entra no Git: passa de 50 MB, é gerado por programa e muda a cada
coleta. Vai como asset de release, e a imagem o busca na construção conferindo
o sha256 — se o arquivo publicado divergir do declarado, o build falha em vez
de subir um acervo diferente daquele que foi testado.

    python preparar_release.py 1.0.0
"""

from __future__ import annotations

import gzip
import hashlib
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BANCO = RAIZ / "dados" / "mesquita.sqlite"


def preparar(versao: str, usuario_repo: str = "SEU-USUARIO/legis-mesquita") -> int:
    if not BANCO.exists():
        print(f"Acervo não encontrado em {BANCO}. Rode a ingestão antes.",
              file=sys.stderr)
        return 1

    destino = RAIZ / "dist" / f"legislacao-mesquita-v{versao}.db.gz"
    destino.parent.mkdir(parents=True, exist_ok=True)

    print(f"Comprimindo {BANCO.stat().st_size / 1048576:.1f} MB…")
    with BANCO.open("rb") as entrada, gzip.open(destino, "wb", compresslevel=9) as saida:
        shutil.copyfileobj(entrada, saida, length=4 * 1024 * 1024)

    digest = hashlib.sha256(destino.read_bytes()).hexdigest()
    tamanho = destino.stat().st_size / 1048576

    print(f"\n{destino}  ({tamanho:.1f} MB)")
    print(f"\n1. Mova para acervo/ e apague o .gz anterior:\n")
    print(f"   mv {destino} acervo/")
    print("\n2. Troque no Dockerfile:\n")
    print(f"ARG ACERVO=acervo/{destino.name}")
    print(f"ARG ACERVO_SHA256={digest}")
    print("\n3. git add -A && git commit && git push — o Render reconstrói.")
    print("4. Recrie os conectores nos clientes.")
    print("\nPreferindo publicar como asset de release (para não engordar o "
          "histórico\ndo Git), o `instalar_acervo.py` também aceita URL:\n")
    print(f"ARG ACERVO=https://github.com/{usuario_repo}/releases/download/"
          f"acervo-v{versao}/{destino.name}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raise SystemExit(preparar(sys.argv[1], *sys.argv[2:3]))
