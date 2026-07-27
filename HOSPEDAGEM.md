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
| Código no GitHub | `fm85gn2y4q-maker/legis-mesquita`, branch `main`, tag `v1.1.0` |
| Acervo | `acervo/legislacao-mesquita-v1.1.0.db.gz` — **22,8 MB**, versionado no repositório |
| sha256 | `b0f971645b8c844718a719de415509b2c8db84e9928e27e94e7e049135159758` |
| `Dockerfile` | descomprime o acervo do repositório, conferindo o hash |
| `render.yaml` | pronto, sem `healthCheckPath` (veja o porquê no próprio arquivo) |

**Não há release a criar.** O acervo viaja no Git; o `Dockerfile` o descomprime
e confere o sha256 antes de usar. A decisão anterior era outra — asset de
release — e a troca está registrada no `METODO.md`.

O passo do build foi verificado fora do Docker: reproduz 4.128 atos, 10.488
páginas, 83 revogações integrais e 15 parciais, com `integrity_check` intacto —
e para a construção quando o hash não bate.

### 3.1. Criar o repositório e subir o código

No GitHub, crie um repositório **vazio** chamado `legis-mesquita` — sem README,
sem .gitignore, sem licença. O projeto já tem os seus, e um repositório que
nasce com arquivos recusa o push por históricas divergentes.

Público ou privado, agora tanto faz — o Render acessa repositório privado pelo
OAuth que você autoriza. Isto **era** uma exigência quando o acervo vinha de um
asset de release: aquele download era anônimo, e num repositório privado o
GitHub devolvia 404 sem dizer que a causa era a visibilidade. Vindo o acervo no
próprio Git, a armadilha deixou de existir. O que foi criado aqui é público.

Depois:

```bash
git remote add origin https://github.com/fm85gn2y4q-maker/legis-mesquita.git
```

```bash
git branch -M main && git push -u origin main && git push --tags
```

O branch local nasceu `master` e o GitHub cria repositório novo com `main` como
padrão. Renomear alinha os dois — sem isso, o repositório fica com um branch
que não é o padrão declarado, e o Render, que constrói a partir do padrão,
não encontraria nada.

O `git push` vai pedir autenticação. Não tem `gh` instalado nesta máquina; o
Gerenciador de Credenciais do Windows abre uma janela do GitHub na primeira vez
e resolve. Criar o repositório e autorizar o acesso é você quem faz — conceder
acesso a um terceiro vincula a sua identidade, e isso não se delega.

O SQLite de 72 MB **não** vai nesse push: o `.gitignore` o mantém fora. Vão o
código e o acervo comprimido, de 22,8 MB.

### 3.2. Aplicar o Blueprint

No Render: **Dashboard → Blueprints → New Blueprint**, apontando para o
repositório. O `render.yaml` já declara o serviço.

Criar a conta e autorizar o GitHub também é você.

### 3.3. Declarar o endereço público — o passo que todo mundo esquece

O endereço só existe depois do primeiro deploy. Até ele ser declarado, o
servidor **recusa toda requisição externa com 421** — é proteção contra DNS
rebinding, e não há curinga: a comparação de Host é exata.

Terminado o primeiro deploy, em **Environment**:

| Variável | Valor |
|---|---|
| `LEGIS_DOMINIOS` | `legis-mesquita-mcp.onrender.com` *(sem `https://`)* |
| `LEGIS_URL_PUBLICA` | `https://legis-mesquita-mcp.onrender.com` |
| `LEGIS_SEGREDO_OAUTH` | valor aleatório longo — use **Generate** no próprio Render |

`LEGIS_URL_PUBLICA` liga o fluxo OAuth, que o **ChatGPT exige** para aceitar um
conector. O Claude conecta sem ele. Salvar as variáveis dispara um novo deploy.

**As três, não duas.** `LEGIS_SEGREDO_OAUTH` só é gerado automaticamente quando
o serviço nasce de um Blueprint (`generateValue: true` no `render.yaml`).
Criando o serviço à mão por **New → Web Service** — que é o caminho mais
transparente e o que usamos —, ela não existe, e o servidor sorteia um segredo
novo a cada partida. Como a instância gratuita hiberna, isso invalida todas as
autorizações do ChatGPT a cada soneca: o conector pede autorização o dia
inteiro, e parece defeito do acervo.

O log diz quando falta:

```
LEGIS_SEGREDO_OAUTH não definido: usando um segredo temporário.
```

### 3.4. Ligar nos clientes

- **ChatGPT** → Configurações → Conectores → adicionar `https://.../mcp`
- **Claude** → Configurações → Conectores → adicionar a mesma URL

### 3.5. O que esperar do plano gratuito

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
| Atos | **4.128** |
| Com texto integral | 4.070 |
| Páginas indexadas | 10.488 |
| Revogações **integrais** | **83** |
| Revogações **parciais** | **15** |

Não batendo, o conector está com uma versão antiga em cache — **remova e recrie
o conector**. Reiniciar o aplicativo não basta: a lista de ferramentas fica
guardada de quando o conector foi adicionado. Foi assim que uma rodada inteira
de testes se perdeu no projeto anterior.

## Ao publicar um acervo novo, depois

```bash
python preparar_release.py 1.2.0
```

Gera `dist/legislacao-mesquita-v1.2.0.db.gz` e imprime o sha256. Então:

1. mova o `.gz` para `acervo/` e **apague o anterior** — senão cada versão fica
   somando ~23 MB à imagem;
2. troque as duas linhas `ARG` do `Dockerfile` pelo novo nome e hash;
3. `git add -A && git commit && git push` — o Render reconstrói sozinho;
4. **recrie os conectores** nos dois clientes.

Apagar o `.gz` antigo tira peso da imagem, não do histórico: o Git guarda todas
as versões para sempre. É o preço de trazer o acervo para dentro do
repositório, e o `METODO.md` registra quando vale voltar ao asset de release —
o `instalar_acervo.py` aceita URL, então essa volta é trocar uma linha.
