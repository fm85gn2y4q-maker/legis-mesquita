"""Prova que o passo do Dockerfile reproduz o acervo declarado, e falha fechado.

Era um script de rascunho, refeito a cada sessão e perdido junto com ela. É a
conferência que separa "o Render serve o acervo testado" de "o Render serve
algo": merece viver no repositório, como teste, e rodar sozinho.
"""

from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DOCKERFILE = RAIZ / "Dockerfile"

# Sem isto o subprocesso escreve em cp1252 no Windows e "Conferência" chega
# aqui com o "ê" trocado por caractere de substituição — o teste reprovava
# uma verificação que tinha funcionado.
UTF8 = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def _declarado() -> tuple[str, str]:
    """Lê do Dockerfile, para não divergir dele em silêncio."""
    texto = DOCKERFILE.read_text(encoding="utf-8")
    acervo = re.search(r"^ARG ACERVO=(\S+)", texto, re.MULTILINE)
    sha = re.search(r"^ARG ACERVO_SHA256=(\S+)", texto, re.MULTILINE)
    assert acervo and sha, "Dockerfile não declara ACERVO e ACERVO_SHA256"
    return acervo.group(1), sha.group(1)


@pytest.fixture(scope="module")
def instalado(tmp_path_factory) -> Path:
    acervo, sha = _declarado()
    destino = tmp_path_factory.mktemp("build") / "mesquita.sqlite"
    resultado = subprocess.run(
        [sys.executable, "instalar_acervo.py", acervo, str(destino), sha],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=UTF8,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "Integridade conferida" in (resultado.stdout + resultado.stderr)
    return destino


def test_o_acervo_declarado_esta_no_repositorio():
    acervo, _ = _declarado()
    assert (RAIZ / acervo).is_file(), (
        f"{acervo} não existe. O Dockerfile aponta para um arquivo ausente, e "
        f"a construção da imagem falharia."
    )


def test_o_passo_do_build_produz_um_acervo_integro(instalado):
    conexao = sqlite3.connect(f"file:{instalado.as_posix()}?mode=ro", uri=True)
    try:
        assert conexao.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        atos = conexao.execute("SELECT COUNT(*) FROM atos").fetchone()[0]
        com_texto = conexao.execute(
            "SELECT COUNT(*) FROM atos WHERE situacao='ok'").fetchone()[0]
        # Um acervo vazio comprime e instala sem erro nenhum — aconteceu em
        # 22/08/2026. O piso aqui é o que impede isso de passar por "verificado".
        assert atos > 4000, f"o acervo tem só {atos} atos"
        assert com_texto > atos * 0.9
        achados = conexao.execute(
            "SELECT COUNT(*) FROM atos_fts WHERE atos_fts MATCH 'ementa:\"poluicao\"'"
        ).fetchone()[0]
        assert achados, "o índice de busca não responde"
    finally:
        conexao.close()


def test_hash_errado_para_a_construcao():
    """A cadeia de integridade tem de falhar FECHADA, não seguir em frente."""
    acervo, _ = _declarado()
    with tempfile.TemporaryDirectory() as tmp:
        resultado = subprocess.run(
            [sys.executable, "instalar_acervo.py", acervo,
             str(Path(tmp) / "x.sqlite"), "0" * 64],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            errors="replace", env=UTF8,
        )
    assert resultado.returncode != 0, "hash errado NÃO parou a construção"
    assert "Conferência falhou" in (resultado.stdout + resultado.stderr)
