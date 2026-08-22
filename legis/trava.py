"""Impede que duas atualizações escrevam no mesmo banco ao mesmo tempo.

Escrito depois de a rotina agendada e o trabalho manual colidirem em
22/08/2026. A tarefa das 10h começou, e `construir` abre apagando o banco para
recriá-lo; cinco minutos depois, uma publicação manual copiou esse arquivo
recém-criado e ainda vazio. O acervo publicado chegou a ser gerado com **zero
ato** — 117 bytes de gzip — e só não foi ao ar porque o número saltou aos olhos.

Nada avisou. Não houve erro: os dois lados fizeram exatamente o que mandava o
código, sobre o mesmo arquivo.

A trava é um arquivo com o PID de quem a tomou. Dono morto significa execução
interrompida — que nesta máquina acontece toda semana, quando o notebook dorme
no meio — e nesse caso a trava é assumida em vez de bloquear para sempre.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


def _vivo(pid: int) -> bool:
    """O processo dono da trava ainda existe?"""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)          # sinal 0 não mata: só pergunta
        return True
    except PermissionError:
        return True              # existe, e é de outro usuário
    except (OSError, ProcessLookupError):
        return False


@contextmanager
def exclusiva(caminho: Path, quem: str = ""):
    """Toma a trava, ou levanta SystemExit dizendo quem a detém."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if caminho.exists():
        try:
            dono, marca = caminho.read_text(encoding="utf-8").split("|", 1)
            pid = int(dono)
        except (ValueError, OSError):
            pid, marca = -1, "ilegível"
        if _vivo(pid):
            raise SystemExit(
                f"Já há uma atualização em andamento (PID {pid}, {marca.strip()}).\n"
                f"Duas ao mesmo tempo corrompem o banco em construção. "
                f"Espere terminar, ou apague {caminho} se tiver certeza de que "
                f"aquele processo morreu."
            )
        print(f"trava órfã de um processo morto (PID {pid}) — assumindo",
              flush=True)
        caminho.unlink(missing_ok=True)

    caminho.write_text(f"{os.getpid()}|{quem}", encoding="utf-8")
    try:
        yield
    finally:
        caminho.unlink(missing_ok=True)
