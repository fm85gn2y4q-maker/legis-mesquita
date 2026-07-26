"""Empacota a legislação de Mesquita como extensão do Claude Desktop (.mcpb).

Plano B para quando o conector HTTP não estiver disponível na conta: a extensão
roda o servidor localmente por stdio, instalada com um duplo clique, sem túnel
e sem depender de o PC estar publicando nada.

O pacote leva as dependências junto (`server/lib`), porque o Claude Desktop não
instala nada: só executa o que está dentro. Leva também o acervo, para a
extensão funcionar sozinha.

    python empacotar_mcpb.py

Gera `dist/legislacao-mesquita.mcpb`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CONSTRUCAO = RAIZ / "build" / "mcpb"
DESTINO = RAIZ / "dist" / "legislacao-mesquita.mcpb"
BANCO = RAIZ / "dados" / "mesquita.sqlite"

# Versões de Python para as quais as dependências são empacotadas. O Claude
# Desktop não usa o interpretador do projeto: pega o primeiro `python` do PATH
# dele. Como `pydantic_core` é binário compilado, um .pyd de cp312 não carrega
# no 3.13 — daí um conjunto por versão.
VERSOES = ("3.12", "3.13", "3.14")

ENTRADA = '''"""Ponto de entrada da extensão: sobe o servidor por stdio."""
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# As dependências viajam dentro do pacote, separadas por versão de Python:
# `pydantic_core` é compilado, e o binário de uma versão não serve para outra.
MARCA = f"py{sys.version_info.major}{sys.version_info.minor}"
BIBLIOTECAS = AQUI / "lib" / MARCA
if not BIBLIOTECAS.is_dir():
    disponiveis = sorted(p.name for p in (AQUI / "lib").glob("py*"))
    print(
        f"Legislação de Mesquita: sem dependências para Python "
        f"{sys.version_info.major}.{sys.version_info.minor}. "
        f"O pacote traz: {', '.join(disponiveis) or 'nenhuma'}.",
        file=sys.stderr,
    )
    raise SystemExit(1)

sys.path.insert(0, str(BIBLIOTECAS))
sys.path.insert(0, str(AQUI))

# O `mcp` importa `pywintypes` no Windows. Instalado com `pip --target`, o
# pywin32 não roda seu pós-instalação: os módulos ficam em `win32/lib` e as
# DLLs em `pywin32_system32`, nenhum dos dois alcançável por padrão.
for _extra in ("win32", "pythonwin"):
    _caminho = BIBLIOTECAS / _extra
    if _caminho.is_dir():
        sys.path.insert(0, str(_caminho))
_lib_win32 = BIBLIOTECAS / "win32" / "lib"
if _lib_win32.is_dir():
    sys.path.insert(0, str(_lib_win32))

_dlls = BIBLIOTECAS / "pywin32_system32"
if _dlls.is_dir():
    os.add_dll_directory(str(_dlls))
    os.environ["PATH"] = str(_dlls) + os.pathsep + os.environ.get("PATH", "")

os.environ.setdefault("LEGIS_BANCO", str(AQUI.parent / "dados" / "mesquita.sqlite"))

from legis.servidor import construir  # noqa: E402

construir().run(transport="stdio")
'''

MANIFESTO = {
    "manifest_version": "0.2",
    "name": "legislacao-mesquita",
    "display_name": "Legislação de Mesquita",
    "version": "1.0.0",
    "description": "Leis e decretos do Município de Mesquita/RJ, com verificação "
                   "de revogação.",
    "long_description": (
        "Consulta a legislação municipal de Mesquita/RJ coletada do Portal da "
        "Transparência — leis ordinárias, leis complementares e decretos, com o "
        "texto integral pesquisável artigo a artigo. Cada resultado traz a "
        "citação no formato de peça, a publicação no Diário Oficial e o que "
        "outros atos fizeram com aquela norma: revogações e alterações "
        "expressas, com o trecho que as indica."
    ),
    "author": {"name": "Matheus Menegatti"},
    "server": {
        "type": "python",
        "entry_point": "server/main.py",
        "mcp_config": {
            # Trocado por caminho absoluto quando se passa --python. O Claude
            # Desktop resolve "python" pelo PATH dele, e o primeiro encontrado
            # pode não servir.
            "command": "python",
            "args": ["${__dirname}/server/main.py"],
            "env": {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        },
    },
    "tools": [
        {"name": "pesquisar_legislacao",
         "description": "Procura normas de Mesquita pela ementa."},
        {"name": "pesquisar_dispositivos",
         "description": "Procura dentro do texto dos atos e devolve a página."},
        {"name": "verificar_vigencia",
         "description": "Mostra revogações e alterações expressas de uma norma."},
        {"name": "localizar_norma",
         "description": "Localiza um ato por espécie, número e ano."},
        {"name": "ler_texto", "description": "Lê o texto do ato, página a página."},
        {"name": "obter_ato", "description": "Dados completos de um ato localizado."},
        {"name": "listar_atos", "description": "Lista atos por espécie e ano."},
        {"name": "cobertura_do_acervo",
         "description": "Volumes, período, lacunas e limites da base."},
        {"name": "search", "description": "Busca compatível com pesquisa profunda."},
        {"name": "fetch", "description": "Recupera um ato pelo identificador."},
    ],
    "keywords": ["legislação", "Mesquita", "direito municipal", "leis", "decretos"],
    # `compatibility` fica de fora de propósito: é opcional, e foi o único
    # ponto que o Claude Desktop recusou no projeto anterior ("Unrecognized
    # key(s): python_version"). Sem validador para conferir a forma correta,
    # declarar menos é mais seguro do que chutar outra chave e falhar na
    # instalação — que é onde o erro aparece para o usuário.
}


def validar(pasta: Path) -> bool:
    """Passa o manifesto pelo validador oficial, se houver Node por perto.

    Empacotar não prova nada: um manifesto com uma chave fora do lugar zipa
    igual e só falha na hora de instalar, com mensagem que aparece na tela do
    usuário e não no build.

    Validador indisponível não é manifesto inválido: se o `npx` não roda, o que
    se sabe é que não se sabe — o pacote sai, com aviso.
    """
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        print("  aviso: npx ausente, manifesto NÃO validado.")
        return True

    resultado = subprocess.run(
        [npx, "--yes", "@anthropic-ai/mcpb", "validate", str(pasta / "manifest.json")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    saida = (resultado.stdout + resultado.stderr).strip()
    if resultado.returncode == 0:
        print("  manifesto válido.")
        return True

    veredito = any(
        marca in saida.lower()
        for marca in ("invalid manifest", "unrecognized key", "validation")
    )
    if veredito:
        print("  " + "\n  ".join(saida.splitlines()[-8:]))
        return False

    print("  aviso: o validador não pôde ser executado; manifesto NÃO validado.")
    return True


def sem_espacos(caminho: str) -> str | None:
    """Devolve o caminho na forma curta 8.3 quando ele tiver espaços.

    O Claude Desktop quebra o `command` do manifesto nos espaços: um
    interpretador em "C:\\Users\\Fulano Silva\\..." vira o comando
    "C:\\Users\\Fulano" com o resto virando argumento.
    """
    if " " not in caminho:
        return caminho

    import ctypes

    buffer = ctypes.create_unicode_buffer(1024)
    tamanho = ctypes.windll.kernel32.GetShortPathNameW(caminho, buffer, 1024)
    curto = buffer.value if tamanho else ""
    # A geração de nomes 8.3 pode estar desligada no volume: sem conferir, o
    # que sai é um caminho que não existe.
    if curto and " " not in curto and Path(curto).exists():
        return curto
    return None


def conferir_interpretador(exe: str) -> bool:
    """Recusa um interpretador que não consiga importar o que o servidor usa.

    Um Python com biblioteca padrão incompleta instala e roda `--version` sem
    reclamar, e só falha quando o servidor sobe — dentro do Claude, onde o erro
    fica escondido num log.
    """
    prova = "import html.entities, sqlite3, asyncio, json; print('ok')"
    resultado = subprocess.run([exe, "-I", "-c", prova], capture_output=True, text=True)
    if resultado.returncode == 0:
        return True
    print(f"  {exe}\n  não serve: "
          f"{resultado.stderr.strip().splitlines()[-1][:110]}", file=sys.stderr)
    return False


def empacotar(python: str | None = None) -> int:
    if python:
        if not Path(python).exists():
            print(f"Interpretador não encontrado: {python}", file=sys.stderr)
            return 1
        print("Conferindo o interpretador escolhido…")
        if not conferir_interpretador(python):
            return 1

        comando = sem_espacos(python)
        if comando is None:
            print(
                f"  O caminho tem espaços e não há nome curto 8.3 para ele:\n"
                f"    {python}\n"
                f"  O Claude Desktop quebraria o comando no primeiro espaço. "
                f"Aponte um interpretador em caminho sem espaços.",
                file=sys.stderr,
            )
            return 1
        if comando != python:
            print(f"  caminho tem espaço; usando o nome curto: {comando}")
            if not conferir_interpretador(comando):
                return 1

        MANIFESTO["server"]["mcp_config"]["command"] = comando
        versao = subprocess.run([comando, "--version"], capture_output=True,
                                text=True).stdout.strip()
        print(f"  fixado em {versao}")

    if not BANCO.exists():
        print(f"Acervo não encontrado em {BANCO}. Rode a ingestão antes.",
              file=sys.stderr)
        return 1

    if CONSTRUCAO.exists():
        shutil.rmtree(CONSTRUCAO)
    servidor = CONSTRUCAO / "server"
    servidor.mkdir(parents=True)

    print("Copiando o pacote…")
    shutil.copytree(
        RAIZ / "legis", servidor / "legis",
        ignore=shutil.ignore_patterns("__pycache__", "publicar.py", "ingestao.py"),
    )
    (servidor / "main.py").write_text(ENTRADA, encoding="utf-8")

    for versao in VERSOES:
        marca = "py" + versao.replace(".", "")
        print(f"Instalando as dependências para Python {versao}…")
        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet",
             "--target", str(servidor / "lib" / marca),
             "--python-version", versao, "--only-binary=:all:", "mcp>=1.28"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if resultado.returncode != 0:
            # Uma versão sem rodas publicadas não é motivo para desistir: o
            # pacote continua servindo as demais.
            print(f"  aviso: sem pacotes para {versao}, seguindo sem ela.")
            shutil.rmtree(servidor / "lib" / marca, ignore_errors=True)

    disponiveis = sorted(p.name for p in (servidor / "lib").glob("py*"))
    if not disponiveis:
        print("Nenhuma dependência empacotada.", file=sys.stderr)
        return 1
    print("  versões no pacote:", ", ".join(disponiveis))

    print("Copiando o acervo…")
    (CONSTRUCAO / "dados").mkdir()
    shutil.copy2(BANCO, CONSTRUCAO / "dados" / "mesquita.sqlite")

    (CONSTRUCAO / "manifest.json").write_text(
        json.dumps(MANIFESTO, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("Validando o manifesto…")
    if not validar(CONSTRUCAO):
        print("\nManifesto inválido; nada foi empacotado.", file=sys.stderr)
        return 1

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    if DESTINO.exists():
        DESTINO.unlink()
    print("Compactando…")
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as pacote:
        for caminho in sorted(CONSTRUCAO.rglob("*")):
            if caminho.is_file() and "__pycache__" not in caminho.parts:
                pacote.write(caminho, caminho.relative_to(CONSTRUCAO))

    tamanho = DESTINO.stat().st_size / 1024 / 1024
    print(f"\n{DESTINO}  ({tamanho:.1f} MB)")
    print("Instale arrastando o arquivo para Configurações → Extensões do Claude.")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python empacotar_mcpb.py",
        description="Empacota a legislação de Mesquita como extensão do Claude.",
    )
    parser.add_argument(
        "--python",
        metavar="EXE",
        help="fixa o interpretador no manifesto, em vez de deixar o Claude "
             "escolher pelo PATH. Use quando o Python que ele acha primeiro "
             "não servir.",
    )
    raise SystemExit(empacotar(parser.parse_args().python))
