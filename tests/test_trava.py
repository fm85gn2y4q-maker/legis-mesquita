"""Testes da trava e do piso de sanidade da publicação.

Os dois nasceram do mesmo incidente, em 22/08/2026: a rotina agendada disparou
às 10h, `construir` apagou o banco para recriá-lo, e cinco minutos depois uma
publicação manual copiou o arquivo vazio. O `.gz` publicado saiu com **zero
ato** — 117 bytes. Nenhum erro foi levantado em ponto algum.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from legis.trava import exclusiva

RAIZ = Path(__file__).resolve().parent.parent


def test_trava_recusa_segunda_execucao(tmp_path):
    trava = tmp_path / ".atualizando"
    with exclusiva(trava, quem="primeira"):
        assert trava.exists()
        with pytest.raises(SystemExit) as erro:
            with exclusiva(trava, quem="segunda"):
                pytest.fail("a segunda execução não deveria ter entrado")
        assert "em andamento" in str(erro.value)
    assert not trava.exists(), "a trava tem de ser solta ao sair"


def test_trava_orfa_e_assumida(tmp_path, capsys):
    """Nesta máquina a rotina morre no meio toda semana, quando o notebook dorme.

    Trava de processo morto não pode bloquear para sempre.
    """
    trava = tmp_path / ".atualizando"
    trava.write_text("999999|processo que não existe", encoding="utf-8")
    with exclusiva(trava, quem="depois"):
        assert int(trava.read_text(encoding="utf-8").split("|")[0]) == os.getpid()
    assert "órfã" in capsys.readouterr().out


def test_trava_e_solta_mesmo_com_erro(tmp_path):
    trava = tmp_path / ".atualizando"
    with pytest.raises(RuntimeError):
        with exclusiva(trava):
            raise RuntimeError("a ingestão explodiu")
    assert not trava.exists()


def _banco(caminho: Path, atos: int) -> Path:
    conexao = sqlite3.connect(caminho)
    conexao.execute("CREATE TABLE atos (id TEXT PRIMARY KEY)")
    conexao.executemany("INSERT INTO atos VALUES (?)",
                        [(f"ato-{n}",) for n in range(atos)])
    conexao.commit()
    conexao.close()
    return caminho


def test_publicacao_recusa_acervo_vazio(tmp_path, monkeypatch, capsys):
    """O cenário exato de 22/08: o banco copiado no meio da reconstrução."""
    import preparar_release

    vazio = _banco(tmp_path / "vazio.sqlite", 0)
    monkeypatch.setattr(preparar_release, "BANCO", vazio)
    assert preparar_release.conferir(vazio) is False
    assert "ZERO atos" in capsys.readouterr().err


def test_publicacao_recusa_acervo_que_encolheu(tmp_path, monkeypatch, capsys):
    import preparar_release

    monkeypatch.setattr(preparar_release, "RAIZ", tmp_path)
    (tmp_path / "acervo").mkdir()
    import gzip
    cheio = _banco(tmp_path / "cheio.sqlite", 1000)
    with cheio.open("rb") as e, gzip.open(
            tmp_path / "acervo" / "publicado-v1.db.gz", "wb") as s:
        s.write(e.read())

    magro = _banco(tmp_path / "magro.sqlite", 500)
    assert preparar_release.conferir(magro) is False
    assert "encolheu" in capsys.readouterr().err


def test_publicacao_aceita_acervo_que_cresceu(tmp_path, monkeypatch, capsys):
    import gzip

    import preparar_release

    monkeypatch.setattr(preparar_release, "RAIZ", tmp_path)
    (tmp_path / "acervo").mkdir()
    cheio = _banco(tmp_path / "cheio.sqlite", 1000)
    with cheio.open("rb") as e, gzip.open(
            tmp_path / "acervo" / "publicado-v1.db.gz", "wb") as s:
        s.write(e.read())

    maior = _banco(tmp_path / "maior.sqlite", 1009)
    assert preparar_release.conferir(maior) is True
    assert "1009 atos" in capsys.readouterr().out
