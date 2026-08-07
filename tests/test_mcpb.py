"""O pacote .mcpb construído realmente sobe?

O Claude Desktop não usa o interpretador do projeto: pega o primeiro `python`
do PATH dele e executa `server/main.py`, que precisa achar as dependências
dentro do próprio pacote. Empacotar não prova isso — só rodar prova.

Foi assim que passou despercebido que o empacotador pedia `mcp` sem teto de
versão e levava a 2.0.0, sem `mcp.server.fastmcp`: o pacote zipava, instalava,
e só quebrava na primeira pergunta do usuário.

Pula quando não houver pacote construído (`python empacotar_mcpb.py`).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONSTRUCAO = Path(__file__).resolve().parent.parent / "build" / "mcpb"
ENTRADA = CONSTRUCAO / "server" / "main.py"
MANIFESTO = CONSTRUCAO / "manifest.json"

pytestmark = pytest.mark.skipif(not ENTRADA.exists(),
                                reason="pacote não construído")


def test_manifesto_declara_as_ferramentas_que_existem():
    """Manifesto que anuncia ferramenta inexistente instala igual e frustra o
    usuário na primeira pergunta."""
    from legis.servidor import construir

    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    declaradas = {f["name"] for f in manifesto["tools"]}
    reais = set(construir()._tool_manager._tools)
    assert declaradas <= reais, declaradas - reais


def test_acervo_viaja_dentro_do_pacote():
    banco = CONSTRUCAO / "dados" / "mesquita.sqlite"
    assert banco.exists(), "a extensão não funcionaria sozinha"
    assert banco.stat().st_size > 50_000_000


@pytest.mark.anyio
async def test_pacote_sobe_com_o_python_do_PATH():
    python = shutil.which("python") or shutil.which("python3")
    assert python, "sem python no PATH — é o que o Claude Desktop usaria"

    parametros = StdioServerParameters(command=python, args=[str(ENTRADA)])
    async with stdio_client(parametros) as (ler, escrever):
        async with ClientSession(ler, escrever) as s:
            init = await s.initialize()
            assert init.serverInfo.name == "legislacao-mesquita"
            r = await s.call_tool("cobertura_do_acervo", {})
            assert json.loads(r.content[0].text)["total_de_atos"] > 1_000
