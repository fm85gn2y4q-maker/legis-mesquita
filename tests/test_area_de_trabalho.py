"""As pastas do próprio projeto podem existir e não abrir.

`dados/`, `acervo/` e `dist/` deixaram de ser pastas reais: a rotina de
arquivamento da máquina as move para o HD externo e deixa junções no lugar.
Com o disco desconectado, a junção continua ocupando o nome e não abre.

Em 26/09/2026 isso derrubou a rotina semanal com um `FileExistsError` levantado
dentro de `legis/trava.py`, três quadros abaixo do que importava — e com um
sintoma contraditório: o `git status` dizia que `dados/` não existia enquanto o
`os.mkdir` dizia que já existia. Os dois estavam certos.

O teste cria uma junção pendurada de verdade. `mklink /J` não exige elevação,
então dá para reproduzir o caso em vez de simulá-lo.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import atualizar

so_windows = pytest.mark.skipif(sys.platform != "win32",
                                reason="junção é conceito do NTFS")


def _juncao_pendurada(onde: Path, nome: str) -> Path:
    """Cria `onde/nome` como junção cujo alvo foi apagado em seguida."""
    alvo = onde / f"{nome}-alvo"
    alvo.mkdir(parents=True)
    link = onde / nome
    feito = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(alvo)],
                           capture_output=True)
    if feito.returncode != 0:
        pytest.skip("mklink indisponível nesta máquina")
    shutil.rmtree(alvo)
    return link


@so_windows
def test_junção_pendurada_e_a_assinatura_do_defeito(tmp_path):
    """Sem isto, nada abaixo faz sentido: o caso É essa contradição."""
    link = _juncao_pendurada(tmp_path, "dados")
    try:
        assert link.exists() is False, "não abre"
        assert link.is_dir() is False
        link.lstat()                       # e ainda assim o nome está ocupado
        with pytest.raises(FileExistsError):
            link.mkdir(parents=True, exist_ok=True)
    finally:
        os.rmdir(link)


@so_windows
def test_queixa_nomeia_a_pasta_e_o_disco(tmp_path, monkeypatch):
    link = _juncao_pendurada(tmp_path, "dados")
    (tmp_path / "acervo").mkdir()
    (tmp_path / "dist").mkdir()
    monkeypatch.setattr(atualizar, "RAIZ", tmp_path)
    try:
        queixa = atualizar.area_de_trabalho_utilizavel()
        assert queixa is not None
        assert str(link) in queixa, "tem de dizer QUAL pasta"
        assert "acervo" not in queixa.split("São junções")[0], \
            "listar a que abre confunde"
        assert "HD externo" in queixa, "tem de dizer a causa provável"
        assert "Git" in queixa, "e que o acervo publicado não se perdeu"
    finally:
        os.rmdir(link)


def test_cala_quando_as_pastas_sao_reais(tmp_path, monkeypatch):
    for nome in ("dados", "acervo", "dist"):
        (tmp_path / nome).mkdir()
    monkeypatch.setattr(atualizar, "RAIZ", tmp_path)
    assert atualizar.area_de_trabalho_utilizavel() is None


def test_cala_quando_as_pastas_simplesmente_nao_existem(tmp_path, monkeypatch):
    """Pasta ausente é criada pela própria rotina — não é o defeito.

    Só o nome OCUPADO e que não abre justifica parar.
    """
    monkeypatch.setattr(atualizar, "RAIZ", tmp_path)
    assert atualizar.area_de_trabalho_utilizavel() is None


def test_ocupado_distingue_nome_tomado_de_nome_livre(tmp_path):
    arquivo = tmp_path / "existe"
    arquivo.write_text("x", encoding="utf-8")
    assert atualizar._ocupado(arquivo) is True
    assert atualizar._ocupado(tmp_path / "nunca-existiu") is False
