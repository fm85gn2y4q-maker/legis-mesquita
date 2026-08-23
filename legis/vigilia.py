"""Impede o Windows de suspender enquanto a rotina roda.

O Agendador sabe **acordar** a máquina para iniciar a tarefa (`WakeToRun`), e
não sabe mantê-la acordada. Nesta máquina, que usa Modern Standby e entra em
suspensão sozinha o tempo todo, isso mata a rotina no meio.

Medido no registro do próprio `.bat`, que só grava "Fim" se o Python retornar:

    Inicio: 02/08 20:33  →  Fim (codigo 0)     execução manual
    Inicio: 03/08 09:00  →  nada               agendada
    Inicio: 08/08 11:31  →  Fim (codigo 0)     execução manual
    Inicio: 16/08 15:34  →  nada               agendada
    Inicio: 22/08 10:05  →  nada               agendada

As manuais terminam; as agendadas somem. O Agendador registra
`3221225786` (0xC000013A), que é encerramento forçado.

A de 22/08 é a mais instrutiva: ela chegou a apagar `staging.sqlite` para
recriá-lo e morreu antes de terminar. Foi assim que uma publicação manual
encontrou um banco vazio e comprimiu zero ato — o incidente do §20 do
`METODO.md`. Ele foi tratado lá como corrida entre dois processos; era também
um processo morto no meio.

`SetThreadExecutionState` cria um pedido de energia visível em
`powercfg /requests`, na seção SYSTEM. Não impede o usuário de fechar a tampa
nem de mandar suspender — impede a suspensão **por ociosidade**, que é o caso.
"""

from __future__ import annotations

import contextlib
import sys

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


@contextlib.contextmanager
def acordado(motivo: str = ""):
    """Segura a máquina acordada enquanto o bloco roda.

    Fora do Windows, ou se a chamada falhar, não faz nada e não atrapalha: a
    rotina roda igual, apenas sem proteção contra suspensão. Falhar aqui seria
    trocar um defeito intermitente por um impedimento certo.
    """
    if sys.platform != "win32":
        yield False
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # Sem `restype`, ctypes assume `c_int` e 0x80000000 volta negativo. O
        # `!= 0` sobreviveria, mas quem for inspecionar os bits do retorno
        # tropeçaria no sinal.
        kernel32.SetThreadExecutionState.restype = ctypes.c_uint
        anterior = kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        # A função devolve o estado ANTERIOR; zero significa que recusou.
        segurou = anterior != 0
    except Exception as erro:  # noqa: BLE001 — nenhuma falha aqui pode parar a rotina
        print(f"aviso: não consegui impedir a suspensão ({erro}); "
              f"a rotina pode morrer no meio se a máquina dormir.",
              file=sys.stderr)
        yield False
        return

    if segurou and motivo:
        print(f"máquina mantida acordada: {motivo}")

    try:
        yield segurou
    finally:
        with contextlib.suppress(Exception):
            kernel32.SetThreadExecutionState(ES_CONTINUOUS)
