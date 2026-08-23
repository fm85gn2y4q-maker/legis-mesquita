"""Onde moram os PDFs que alimentam o acervo.

Eram duas pastas em `~`. Em 23/08/2026 foram para o HD externo — 7,6 GB que não
precisam ocupar o disco do sistema, e que já ficam ao lado dos outros acervos.

O caminho deixou de ser constante por um motivo prático: letra de unidade USB
muda. `LEGIS_FONTES` manda; sem ela, procura-se nos lugares conhecidos, e a
escolha é **impressa** por quem chama. Rotina que lê a pasta errada em silêncio
é o defeito mais caro deste projeto — já custou 13 minutos de reprocessamento
sobre um dicionário vazio, e a única pista foi a contagem de arquivos idêntica.

Não há palpite entre unidades: exige-se que a pasta exista. Com o HD desligado,
a rotina falha dizendo o que procurou, em vez de reconstruir o acervo a partir
do nada — que passaria pela ingestão e só seria pego no diff.
"""

from __future__ import annotations

import os
from pathlib import Path

LEGISLACAO = "Mesquita_Legislacao"
DIARIOS = "Mesquita_Diarios_Oficiais"

# Na ordem em que se procura.
#
# A ordem natural seria o HD externo primeiro — depois da mudança é lá que o
# acervo mora, e uma sobra em `~` seria cópia velha. **Está invertida de
# propósito desde 23/08/2026.**
#
# A mudança para o HD foi tentada nesse dia e reprovou na conferência. Medido
# no mesmo PDF: `C:` lê a 161 MB/s, `D:` a 0,4 MB/s — quatrocentas vezes mais
# lento. O `quick_check` do banco do Diário copiado para lá levou 873 segundos
# e terminou em `Tree 5 page 14956: unable to get the page. error code=266`,
# com falhas de gravação atrasada no log do Windows. O mesmo banco em `C:`
# passa em 2 segundos.
#
# Enquanto for assim, preferir `D:` seria mandar a rotina de sábado ler 3,6 GB
# de PDFs de um disco que não devolve o que gravou. Trocar de cabo, de porta ou
# de gaveta é o primeiro passo; resolvido isso e reconferido, inverta esta
# tupla de volta.
CANDIDATAS = ("~", "D:/")


def raiz_das_fontes(explicita: str | None = None) -> Path:
    """A pasta que contém `Mesquita_Legislacao` e `Mesquita_Diarios_Oficiais`."""
    escolhida = explicita or os.environ.get("LEGIS_FONTES")
    if escolhida:
        return Path(os.path.expanduser(escolhida))

    for candidata in CANDIDATAS:
        raiz = Path(os.path.expanduser(candidata))
        if (raiz / LEGISLACAO).is_dir() or (raiz / DIARIOS).is_dir():
            return raiz

    # Nenhuma existe: devolve a primeira mesmo assim, para que a mensagem de
    # erro de quem chamou mostre um caminho concreto em vez de `None`.
    return Path(os.path.expanduser(CANDIDATAS[0]))


def legislacao(explicita: str | None = None) -> Path:
    return raiz_das_fontes(explicita) / LEGISLACAO


def diarios(explicita: str | None = None) -> Path:
    return raiz_das_fontes(explicita) / DIARIOS


def conferir(*pastas: Path) -> str | None:
    """Devolve a queixa se alguma pasta não existir; `None` se estiver tudo lá.

    Existe para que o erro seja uma frase e não um `FileNotFoundError` no meio
    da ingestão, com o banco já apagado.
    """
    faltando = [p for p in pastas if not p.is_dir()]
    if not faltando:
        return None
    return (
        "Não encontrei as fontes:\n  "
        + "\n  ".join(str(p) for p in faltando)
        + "\n\nO acervo de PDFs está no HD externo. Conecte-o, ou aponte o "
        "caminho:\n  set LEGIS_FONTES=E:\\   (ou o caminho onde as pastas "
        "estiverem)"
    )
