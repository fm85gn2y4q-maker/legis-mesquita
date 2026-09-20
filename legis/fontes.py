"""Onde moram os PDFs que alimentam o acervo.

Duas pastas, e **não se procura uma raiz comum para as duas**. Essa era a
suposição da primeira versão, e ela quebrou em 20/09/2026: a migração levou os
PDFs por ato para `D:\\Acervos\\Mesquita_Legislacao` e deixou o acervo do Diário
alcançável por `~/Mesquita_Diarios_Oficiais`, que é uma junção para dentro do
projeto `diarios-mesquita` — e lá dentro `municipio` é **outro** link, este sim
para `D:\\Acervos`. Três saltos, duas unidades, nenhuma raiz em comum.

Cada pasta se resolve por conta própria, na ordem declarada abaixo, e quem
chama **imprime** o que foi escolhido. Rotina que lê a pasta errada em silêncio
é o defeito mais caro deste projeto: já custou 13 minutos de reprocessamento
sobre um dicionário vazio, e a única pista foi a contagem de arquivos ter dado
idêntica.

Não há palpite: exige-se que a pasta exista. Faltando, a rotina para dizendo o
que procurou, em vez de reconstruir o acervo a partir do nada — que passaria
pela ingestão inteira e só seria pego lá na frente, pelo diff.

Sobre junções penduradas, que é como este arquivo foi parar aqui: `~` guarda
uma junção `Mesquita_Legislacao` cujo alvo não existe mais, sobra de uma pasta
apagada sem que se olhasse quem apontava para dentro dela. `is_dir()` devolve
False para ela, então a busca segue para a candidata seguinte — que é o
comportamento certo, mas só porque a ordem põe `D:/Acervos` na frente de `~`.
"""

from __future__ import annotations

import os
from pathlib import Path

LEGISLACAO = "Mesquita_Legislacao"
DIARIOS = "Mesquita_Diarios_Oficiais"

# Na ordem em que se procura, por pasta.
#
# `D:/Acervos` vem primeiro porque é para onde a migração levou tudo, e porque
# uma sobra em `~` seria cópia velha — achá-la antes seria reprocessar o
# passado sem avisar.
#
# O HD externo chegou a reprovar em 23/08/2026: lia a 0,4 MB/s contra 161 do
# `C:`, corrompeu o banco copiado e encheu o log do Windows com 13.773 avisos
# em seis horas. Remedido em 20/09, depois da troca: **53,6 MB/s** e 290
# eventos em 24 horas. Voltou a servir.
CANDIDATAS_LEGISLACAO = ("D:/Acervos", "~", "D:/")

# O do Diário fica em `~` de propósito: é lá que estão `baixar_diarios.py` e o
# banco que o coletor usa. Os PDFs em si moram no `D:`, alcançados pelo link
# `municipio` de dentro dessa pasta — quem lê não precisa saber disso.
CANDIDATAS_DIARIOS = ("~", "D:/Acervos", "D:/")


def _resolver(nome: str, candidatas: tuple[str, ...],
              explicita: str | None) -> Path:
    escolhida = explicita or os.environ.get("LEGIS_FONTES")
    if escolhida:
        return Path(os.path.expanduser(escolhida)) / nome

    for candidata in candidatas:
        caminho = Path(os.path.expanduser(candidata)) / nome
        # `is_dir()` é False para junção pendurada, e é o que queremos: a busca
        # segue em frente em vez de devolver um caminho que não abre.
        if caminho.is_dir():
            return caminho

    # Nenhuma existe: devolve a primeira para que a queixa cite um caminho
    # concreto em vez de `None`.
    return Path(os.path.expanduser(candidatas[0])) / nome


def legislacao(explicita: str | None = None) -> Path:
    return _resolver(LEGISLACAO, CANDIDATAS_LEGISLACAO, explicita)


def diarios(explicita: str | None = None) -> Path:
    return _resolver(DIARIOS, CANDIDATAS_DIARIOS, explicita)


def onde_estao(explicita: str | None = None) -> str:
    """Uma linha para a rotina imprimir antes de começar."""
    return f"legislação em {legislacao(explicita)} · Diário em {diarios(explicita)}"


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
        + "\n\nOs PDFs estão no HD externo, em D:\\Acervos. Conecte-o, ou "
        "aponte a raiz:\n  set LEGIS_FONTES=E:\\Acervos   (ou onde as pastas "
        "estiverem)\n\nSe o caminho existe mas não abre, pode ser junção "
        "pendurada — o alvo dela foi apagado."
    )
