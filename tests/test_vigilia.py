"""Impedir a suspensão enquanto a rotina roda.

Três execuções agendadas morreram no meio — o registro do `.bat` mostra
"Inicio" sem "Fim", e o Agendador anota 0xC000013A, encerramento forçado. As
manuais, nos mesmos dias, terminaram. A máquina usa Modern Standby e dorme
sozinha; o Agendador sabe acordá-la para começar e não sabe mantê-la acordada.

Uma dessas mortes é a de 22/08: a rotina apagou `staging.sqlite` para recriá-lo
e não voltou. O §20 do `METODO.md` tratou aquilo como corrida entre processos —
era também um processo morto no meio.
"""

from __future__ import annotations

import sys

import pytest

from legis.vigilia import ES_CONTINUOUS, ES_SYSTEM_REQUIRED, acordado

so_windows = pytest.mark.skipif(sys.platform != "win32",
                                reason="SetThreadExecutionState é do Windows")


def _estado_atual() -> int:
    """Lê o estado sem alterá-lo: repete o pedido e devolve o anterior."""
    import ctypes

    k = ctypes.windll.kernel32
    k.SetThreadExecutionState.restype = ctypes.c_uint
    return k.SetThreadExecutionState(ES_CONTINUOUS)


@so_windows
def test_segura_e_solta_a_maquina():
    """O Windows aceita o pedido, e o bit some ao sair do bloco.

    `SetThreadExecutionState` devolve o estado ANTERIOR — é o único sinal
    disponível sem privilégio de administrador, já que `powercfg /requests`
    exige elevação.
    """
    with acordado("teste") as segurou:
        assert segurou, "o Windows recusou o pedido de vigília"
        assert _estado_atual() & ES_SYSTEM_REQUIRED, "o bit não ficou de pé"

    assert not (_estado_atual() & ES_SYSTEM_REQUIRED), (
        "o bloco terminou e a máquina continuou proibida de dormir")


@so_windows
def test_solta_mesmo_quando_a_rotina_estoura():
    """Rotina que falha não pode deixar o computador acordado para sempre."""
    with pytest.raises(ZeroDivisionError):
        with acordado("teste"):
            1 / 0

    assert not (_estado_atual() & ES_SYSTEM_REQUIRED)


def test_fora_do_windows_nao_atrapalha(monkeypatch):
    """Falhar aqui seria trocar um defeito intermitente por um impedimento
    certo: sem Windows, a rotina roda igual, apenas sem proteção."""
    monkeypatch.setattr(sys, "platform", "linux")
    with acordado("teste") as segurou:
        assert segurou is False
