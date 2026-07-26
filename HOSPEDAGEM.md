# Hospedagem — tirar o servidor da sua máquina

Três caminhos, do mais simples ao mais duradouro. O primeiro não exige conta em
lugar nenhum; o terceiro deixa o acervo no ar com o computador desligado.

---

## 1. Extensão do Claude Desktop (.mcpb) — sem rede, sem conta

```bash
python empacotar_mcpb.py
```

Gera `dist/legislacao-mesquita.mcpb`, que se instala arrastando para
**Configurações → Extensões** do Claude Desktop. O pacote leva as dependências
e o acervo dentro: funciona offline.

O acervo tem ~70 MB, então o `.mcpb` fica nessa ordem de grandeza.

Se o Claude reclamar do interpretador, fixe um sem espaços no caminho:

```bash
python empacotar_mcpb.py --python C:\Python312\python.exe
```

## 2. Túnel temporário — para testar no ChatGPT hoje

O ChatGPT não enxerga `localhost`: só conversa com servidor remoto.

```bash
python -m legis.publicar
```

Levanta um túnel do Cloudflare e o servidor por trás dele, e imprime a URL para
colar em **Configurações → Conectores**. Vale enquanto a janela estiver aberta;
ao reabrir, o Cloudflare sorteia outro endereço.

Precisa do `cloudflared`:

```bash
winget install --id Cloudflare.cloudflared
```

## 3. Render — permanente

### 3.1. Publicar o acervo como asset de release

O banco não vai no Git: passa de 50 MB, é gerado por programa e mudaria o
histórico a cada coleta.

```bash
python preparar_release.py 1.0.0
```

O comando comprime `dados/mesquita.sqlite`, imprime o `sha256` e as duas linhas
`ARG` prontas. Então:

1. No GitHub, crie a release com a tag `acervo-v1.0.0`.
2. Suba `dist/legislacao-mesquita-v1.0.0.db.gz` como asset.
3. Troque no `Dockerfile` as linhas `ARG ACERVO_URL` e `ARG ACERVO_SHA256`.

A conferência do hash acontece na construção da imagem. Divergindo o arquivo
publicado do declarado, **o build falha** em vez de subir um acervo diferente
daquele que você testou.

### 3.2. Aplicar o Blueprint

No Render: **Dashboard → Blueprints → New Blueprint**, apontando para o
repositório. O `render.yaml` já declara o serviço.

Criar a conta e autorizar o GitHub é você quem faz: conceder acesso OAuth
vincula a sua identidade a um terceiro.

### 3.3. Declarar o endereço público — o passo que todo mundo esquece

O endereço só existe depois do primeiro deploy. Enquanto ele não for declarado,
o servidor **recusa toda requisição externa com 421** — é proteção contra DNS
rebinding, e não há curinga: a comparação de Host é exata.

Terminado o primeiro deploy, em **Environment**, defina:

| Variável | Valor |
|---|---|
| `LEGIS_DOMINIOS` | `seu-servico.onrender.com` |
| `LEGIS_URL_PUBLICA` | `https://seu-servico.onrender.com` |

`LEGIS_SEGREDO_OAUTH` o Render gera sozinho.

`LEGIS_URL_PUBLICA` liga o fluxo OAuth, que o **ChatGPT exige** para aceitar um
conector. O Claude conecta sem ele.

### 3.4. Ligar nos clientes

- **ChatGPT** → Configurações → Conectores → adicionar `https://.../mcp`
- **Claude** → Configurações → Conectores → adicionar a mesma URL

---

## Ao publicar uma versão nova do acervo

Os conectores guardam a lista de ferramentas de quando foram adicionados.
Depois de trocar o acervo ou acrescentar ferramenta, **remova e recrie o
conector** nos dois clientes. Reiniciar o aplicativo não basta — foi assim que
uma rodada inteira de testes se perdeu no projeto anterior, com os dois
clientes respondendo pela versão antiga.

O `TESTE_ACEITACAO.md` traz um critério objetivo para confirmar que o cliente
carregou a versão certa, antes de valer qualquer avaliação.
