# Legislação de Mesquita — servidor MCP

Leis ordinárias, leis complementares e decretos do Município de Mesquita/RJ,
expostos como ferramenta de pesquisa para o Claude e o ChatGPT.

Feito sobre os PDFs já baixados do Portal da Transparência da Prefeitura, em
`~/Mesquita_Legislacao`.

---

## O que ele faz de diferente de uma busca por palavra

**Separa o ato do arquivo.** A partir de 2017 a Prefeitura publica em Diário
Oficial, e um arquivo chamado `Lei_1106_2019.pdf` traz, na mesma página, a Lei
1.106 *e* o Decreto 2.430. Medido em amostra de 189 arquivos: **33% contêm dois
ou mais atos**, um deles contém 17. Indexar o arquivo inteiro sob o nome do
arquivo faria a Lei "dispor" sobre orçamento. Aqui cada ato é segmentado pelo
próprio cabeçalho.

**Avisa quando a norma foi revogada.** Uma busca textual devolve norma viva e
norma revogada com a mesma confiança — nada no texto de uma lei revogada avisa
que ela foi. O acervo guarda o grafo de revogações e alterações **expressas**,
extraído do texto dos próprios atos, e `verificar_vigencia` mostra quem mexeu
naquela norma, com o trecho que o indica.

O que ele **não** faz, e diz isso com todas as letras: afirmar que uma norma
está em vigor. Revogação tácita, norma superveniente e declaração de
inconstitucionalidade estão fora do alcance de qualquer base montada assim.

---

## O que há no acervo

| | |
|---|---|
| Atos | **4.133** — 2001 a 2026 |
| Com texto integral pesquisável | 4.075 (98,6%) |
| Sem texto | 58 — constam com ementa; veja `listar_atos_sem_texto` |
| Páginas indexadas | 10.512 |
| Caracteres | 20,3 milhões |
| Referências entre atos resolvidas | 712 |
| Atos com revogação integral expressa | 83 |
| Atos com revogação parcial expressa | 16 |

O acervo se mantém em dia pelo Diário Oficial: `python -m legis.ingestao` lê,
além dos PDFs por ato, as edições do DOM a partir de `--desde`.

---

## Rotina semanal

```bash
python atualizar.py
```

Baixa as edições novas do Diário, reprocessa em `dados/staging.sqlite` e compara
com o acervo publicado. **Não publica.** O acervo no ar não é tocado, e a
decisão de promover o novo é humana.

O código de saída é o aviso:

| | |
|---|---|
| `0` | nada exige leitura — só acréscimo, ou nada mudou |
| `1` | algo sumiu, perdeu texto ou encolheu — **alguém precisa olhar** |
| `2` | a coleta ou o reprocessamento falhou |

O relatório fica em `dist/diferenca-<data>.md`.

A separação é deliberada, e tem motivo registrado no `METODO.md`: três vezes
neste projeto uma correção do extrator fez o número de atos com texto **subir**
enquanto atos reais desapareciam — numa delas, sete leis complementares. Um
pipeline que publicasse sozinho teria levado isso ao ar.

Está agendada no Windows para **segunda-feira às 9h**:

```bash
Get-ScheduledTask -TaskName "Legislacao Mesquita - atualizacao semanal"
```

Para comparar dois acervos quaisquer, fora da rotina:

```bash
python -m legis.comparar acervo/legislacao-mesquita-v1.2.0.db.gz dados/mesquita.sqlite
```

Construído a partir de 7.763 PDFs (3.964 distintos por hash), 3,6 GB.

Cinco normas foram **recusadas nominalmente** por não pertencerem à série
municipal — as Leis federais 14.133/2021, 10.520/2002 e 14.434/2022, o Decreto
federal 10.282/2020 e o Decreto estadual 46.984/2020. Citadas no corpo de
decretos de Mesquita, a diagramação as deixava com forma de cabeçalho, e elas
entravam como se fossem atos do Município.

---

## Ferramentas expostas

| Ferramenta | Para quê |
|---|---|
| `pesquisar_legislacao` | busca na **ementa** — achar qual norma trata do assunto |
| `pesquisar_dispositivos` | busca no **corpo do ato**, devolve a página — achar a regra |
| `verificar_vigencia` | revogações e alterações expressas recebidas pela norma |
| `localizar_norma` | pela referência em mãos: "Lei 1.106/2019" |
| `ler_texto` | lê o ato página a página |
| `obter_ato`, `listar_atos` | acesso direto e varredura |
| `cobertura_do_acervo` | volumes, período, lacunas e limites |
| `search` / `fetch` | compatibilidade com a pesquisa profunda do ChatGPT |

---

## Uso

### Construir o acervo

```bash
python -m legis.ingestao
```

Lê os PDFs de `~/Mesquita_Legislacao`, segmenta os atos e grava
`dados/mesquita.sqlite`. Aceita `--pasta`, `--banco` e `--limite`.

### Rodar

```bash
python -m legis
```

Servidor por stdio, para o Claude Desktop. Para o ChatGPT, que só fala com
servidor remoto:

```bash
python -m legis --http
```

### Instalar como extensão do Claude Desktop

```bash
python empacotar_mcpb.py
```

Gera `dist/legislacao-mesquita.mcpb`, que se instala arrastando para
Configurações → Extensões. O pacote leva as dependências e o acervo dentro:
funciona sem rede e sem nada publicado.

Se o Claude reclamar do interpretador, fixe um:

```bash
python empacotar_mcpb.py --python C:\Python312\python.exe
```

### Publicar

Túnel temporário, para testar no ChatGPT sem hospedar nada:

```bash
python -m legis.publicar
```

Hospedagem permanente: o `Dockerfile` e o `render.yaml` estão prontos, e o
acervo comprimido viaja no repositório (`acervo/`, 21,6 MB). A imagem o
descomprime conferindo o sha256 declarado — divergindo, a construção falha em
vez de subir acervo diferente do testado.

Para gerar a versão comprimida de um acervo recém-coletado:

```bash
python preparar_release.py 1.1.0
```

O comando imprime o sha256 para as duas linhas `ARG` do `Dockerfile`. Depois do
primeiro deploy, defina `LEGIS_DOMINIOS` e `LEGIS_URL_PUBLICA` com o endereço
que o serviço atribuiu — sem isso o servidor recusa toda requisição externa.
O passo a passo completo está em [HOSPEDAGEM.md](HOSPEDAGEM.md).

### Testes

```bash
python -m pytest
```

---

## Limites do acervo

Estão declarados em `cobertura_do_acervo` e o servidor instrui o modelo a
repeti-los quando importarem:

- É **cópia de trabalho** do Portal da Transparência, não o repositório
  oficial. Para protocolar, confira no Diário Oficial do Município.
- O texto é o **original** de cada ato. Não há redação consolidada: lei
  alterada dez vezes aparece como foi promulgada.
- Há **anos sem nenhum decreto** e anos com pouquíssimos. Ausência aqui não é
  prova de inexistência.
- **Não estão no acervo**: Lei Orgânica do Município, portarias, resoluções,
  instruções normativas e atos da Câmara Municipal.
- Alguns PDFs são digitalizações sem camada de texto: o ato consta com ementa,
  mas sem texto pesquisável.
