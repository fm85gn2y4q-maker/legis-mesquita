# Hospedagem — tirar o servidor da sua máquina

Três caminhos. O primeiro não exige conta em lugar nenhum; o terceiro deixa o
acervo no ar com o computador desligado, que é o que faz o plugin funcionar no
celular e no ChatGPT.

---

## 1. Extensão do Claude Desktop (.mcpb) — sem rede, sem conta

```bash
python empacotar_mcpb.py
```

Gera `dist/legislacao-mesquita.mcpb` (66,2 MB), que se instala arrastando para
**Configurações → Extensões** do Claude Desktop. O pacote leva as dependências
e o acervo dentro: funciona offline.

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

O `cloudflared` já está instalado nesta máquina. Em outra:

```bash
winget install --id Cloudflare.cloudflared
```

---

## 3. Render — permanente

### O que já está pronto

| | |
|---|---|
| Acervo comprimido | `dist/legislacao-mesquita-v1.0.0.db.gz` — **21,6 MB** (de 69,2) |
| sha256 | `96403c42352342e6c3e9adba7adba0b40e1f54b3536a4d39299280e5a63cded4` |
| `Dockerfile` | URL e hash **já fixados** |
| `render.yaml` | pronto, sem `healthCheckPath` (veja o porquê no próprio arquivo) |

O `Dockerfile` aponta para
`github.com/fm85gn2y4q-maker/legis-mesquita`. **Se o repositório tiver outro
nome, mude aquela linha antes de subir** — é a única que depende do nome.

### 3.1. Criar o repositório e subir o código

No GitHub, crie um repositório **vazio** chamado `legis-mesquita` (sem README,
sem .gitignore — o projeto já tem os seus). Depois:

```bash
git remote add origin https://github.com/fm85gn2y4q-maker/legis-mesquita.git
```

```bash
git push -u origin master && git push origin v1.0.0
```

O `git push` vai pedir autenticação. Não tem `gh` instalado nesta máquina; o
Gerenciador de Credenciais do Windows abre uma janela do GitHub na primeira vez
e resolve. Criar o repositório e autorizar o acesso é você quem faz — conceder
acesso a um terceiro vincula a sua identidade, e isso não se delega.

O banco **não** vai nesse push: o `.gitignore` o mantém fora. São 23 arquivos,
177 KB.

### 3.2. Publicar o acervo como asset de release

O banco é artefato de dados, não código-fonte. Vai à parte, com versão fixa.

No GitHub, em **Releases → Draft a new release**:

- Tag: `acervo-v1.0.0` *(atenção: é diferente da tag `v1.0.0` do código)*
- Anexe o arquivo `dist/legislacao-mesquita-v1.0.0.db.gz`
- Publique

A imagem baixa esse arquivo na construção e **confere o sha256**. Divergindo do
declarado no `Dockerfile`, o build falha em vez de subir um acervo diferente
daquele que você validou.

### 3.3. Aplicar o Blueprint

No Render: **Dashboard → Blueprints → New Blueprint**, apontando para o
repositório. O `render.yaml` já declara o serviço.

Criar a conta e autorizar o GitHub também é você.

### 3.4. Declarar o endereço público — o passo que todo mundo esquece

O endereço só existe depois do primeiro deploy. Até ele ser declarado, o
servidor **recusa toda requisição externa com 421** — é proteção contra DNS
rebinding, e não há curinga: a comparação de Host é exata.

Terminado o primeiro deploy, em **Environment**:

| Variável | Valor |
|---|---|
| `LEGIS_DOMINIOS` | `legislacao-mesquita.onrender.com` *(sem `https://`)* |
| `LEGIS_URL_PUBLICA` | `https://legislacao-mesquita.onrender.com` |

`LEGIS_SEGREDO_OAUTH` o Render gera sozinho.

`LEGIS_URL_PUBLICA` liga o fluxo OAuth, que o **ChatGPT exige** para aceitar um
conector. O Claude conecta sem ele. Salvar as variáveis dispara um novo deploy.

### 3.5. Ligar nos clientes

- **ChatGPT** → Configurações → Conectores → adicionar `https://.../mcp`
- **Claude** → Configurações → Conectores → adicionar a mesma URL

### 3.6. O que esperar do plano gratuito

O serviço **hiberna depois de um período sem uso**. A primeira chamada depois
disso acorda a máquina e pode levar cerca de um minuto — tempo suficiente para
o conector dar erro de tempo esgotado *na primeira tentativa*. Insista uma vez
antes de concluir que a instalação falhou.

---

## Confirmar que subiu o acervo certo

Pergunte ao cliente já conectado:

> *"Quantos atos há no acervo, e quantos têm revogação parcial registrada?"*

A resposta tem de bater com a versão publicada:

| | |
|---|---|
| Atos | **4.129** |
| Com texto integral | 4.011 |
| Páginas indexadas | 10.163 |
| Revogações **integrais** | **76** |
| Revogações **parciais** | **14** |

Não batendo, o conector está com uma versão antiga em cache — **remova e recrie
o conector**. Reiniciar o aplicativo não basta: a lista de ferramentas fica
guardada de quando o conector foi adicionado. Foi assim que uma rodada inteira
de testes se perdeu no projeto anterior.

## Ao publicar um acervo novo, depois

```bash
python preparar_release.py 1.1.0
```

Imprime as duas linhas `ARG` para trocar no `Dockerfile`. Suba o novo `.db.gz`
como release `acervo-v1.1.0`, faça o push, e o Render reconstrói. Depois,
recrie os conectores.
