# Construir um MCP sobre um acervo — guia para o próximo

Documento para levar a outro chat, outro projeto, outro acervo. Não é resumo do
que foi feito: é o que **se repete**, com os números que justificam cada regra e
os erros que custaram caro.

Construído sobre dois acervos jurídicos — jurisprudência do TCE-RJ e legislação
municipal de Mesquita —, mas quase tudo aqui vale para qualquer corpo documental
que precise virar ferramenta de pesquisa confiável.

---

## Como usar este documento

Cole o bloco abaixo no começo do novo projeto, junto com este arquivo:

> Vamos construir um servidor MCP sobre um acervo de documentos. Leia
> `GUIA-NOVO-ACERVO.md` inteiro antes de escrever a primeira linha. Siga a
> ordem das fases. Não pule a fase 1: ela muda o plano, não o confirma.
> Antes de me propor qualquer correção no extrator, me mostre o diff
> registro a registro contra a versão anterior — total agregado não serve.

---

## A regra que vale mais que todas as outras

**A ferramenta prova o que encontrou, não o que existe.**

Toda decisão de projeto abaixo é consequência disso. O erro que importa nunca é
"não achou" — é **achar e apresentar com mais certeza do que a fonte sustenta**.

E o corolário prático, aprendido caro:

> Correção não se avalia pelo que ela conserta. Avalia-se pelo **diff registro a
> registro**, porque o número agregado sobe enquanto registros reais somem.

---

## Fase 1 — Medir o pressuposto (antes de escrever código)

Toda etapa começa verificando a suposição de que ela depende. Pular isso custou
caro nas duas bases.

**Perguntas obrigatórias, com o método de resposta:**

| Pergunta | Como medir | O que mudou quando medi |
|---|---|---|
| O texto é extraível? | amostra estratificada, `chars/página` | 98% nativo → dispensou todo o pipeline de OCR |
| Quantos documentos existem *de verdade*? | hash de conteúdo | 7.763 arquivos → 3.964 distintos; contar arquivos superdimensionava em 96% |
| **O que é um registro?** | ler os documentos, não a documentação | **33% dos arquivos tinham mais de um ato**; um tinha 17 |
| Há metadados oficiais à parte? | catálogo, CSV, API do portal | a ementa oficial veio do portal; a espécie, só do documento |

A terceira é a mais cara de errar, e a resposta óbvia esteve errada nas duas
bases:

- No TCE-RJ, `espécie+número+ano` **não** identifica um acórdão: 19 acórdãos
  rendem duas ou três ementas cada, com teses distintas.
- Em Mesquita, **um arquivo não é um ato**: a partir de 2017 a Prefeitura
  publica em Diário Oficial, e `Lei_1106_2019.pdf` traz a Lei 1.106 *e* o
  Decreto 2.430, que dispõe sobre orçamento.

> Antes de criar a tabela: *o que é uma linha aqui?* E depois: *duas linhas com
> os mesmos campos são o mesmo objeto?*

**A medição não confirma o plano — ela o muda.** Se a sua medição só confirmou,
provavelmente você mediu a coisa errada.

---

## Fase 2 — Calibrar contra dados reais, em volume pequeno

Colete/processe **centenas antes de milhares**. Os defeitos de formato aparecem
em 400 registros; em 4.000 eles somem na estatística como "quase tudo certo".

Defeitos que só apareceram contra dados reais, nenhum pegável com dado
sintético:

- carimbo de data com `T` não casava o regex → campo vazio em **100%** dos
  registros
- quebra de linha era a sequência literal `\n` → aparecia crua em toda ementa
- `re.IGNORECASE` anulava a exigência de maiúscula → relator capturado de prosa
- número `0` na origem virava "Acórdão 0/2000"

---

## Fase 3 — Separar coletar de processar

O que veio da rede **fica intocado**. Tudo o mais é transformação
determinística sobre ele.

Nas duas bases a ingestão foi refeita entre cinco e oito vezes. Sem essa
separação, cada correção significaria bater de novo no servidor da fonte.

---

## Fase 4 — O extrator, e as armadilhas que ele tem

Esta é a fase onde mais se erra, e onde o erro é mais silencioso.

### 4.1. Valide antes de delimitar

O defeito estrutural mais caro do projeto:

```python
# ERRADO — o candidato inválido já serviu de fronteira
achados = [a for a in PADRAO.finditer(texto) if parece_cabecalho(texto, a)]
for i, a in enumerate(achados):
    if not tem_identidade(a):     # ← descarte tarde demais
        continue
    fim = achados[i+1].start()    # ← o inválido cortou o anterior
```

Um candidato que o parser descarta **depois** já delimitou o registro anterior.
Resultado real: um ato com 152 caracteres, cortado no meio da própria ementa,
por causa de uma ocorrência que o próprio parser considerou inválida em seguida.

### 4.2. Cabeçalho e citação têm a mesma forma

`LEI Nº 460 DE 18 DE JUNHO DE 2008` abre um ato **e** aparece dentro de "Fica
revogada a Lei nº 460 de 18 de junho de 2008". Confundi-los cria registros
inexistentes e atribui texto ao registro errado.

Critérios que funcionaram, em conjunto:

1. **Posição**: começa a linha, e depois da data vem no máximo um ponto
2. **Contexto abaixo**: há fórmula de abertura ou primeiro artigo em seguida
3. **Contexto acima**: a linha anterior não termina em palavra de ligação
4. **Quebras de linha**: no máximo uma dentro do próprio cabeçalho

### 4.3. Cada critério erra para o lado oposto — e o diff é quem mostra

Três correções, cada uma precisa numa direção e cega na outra:

| Problema | Primeira ideia | Efeito colateral | Regra final |
|---|---|---|---|
| Citação virando cabeçalho | proibir quebra de linha | matou cabeçalho legítimo partido em duas | **contar** quebras: no máximo uma |
| Frase continuando | recusar linha terminada em `,` ou `:` | matou `PROMULGO A SEGUINTE LEI:` | só palavras de ligação |
| Palavra virando mês | exigir as doze grafias corretas | matou `OUTRUBRO`, `AGOSOTO`, `DEJUNHO`, `STEMBRO` | raiz de três letras, **ou** a moldura `DE dia DE … DE ano` |

Em nenhuma das três eu teria descoberto por teste: em todas eu estava
consertando algo real, e a métrica agregada subia.

### 4.4. Quantificador de regex custa registros

`(\d{1,3}(?:\.\d{3})*|\d{1,5})` com `*` casa "110" de `1106` e o motor aceita
o resto sem data. Efeitos medidos:

- no cabeçalho: **1.144 registros sem texto** (viraram 118 com `+`)
- no extrator de referências: `Decreto nº 1059` lido como **105**, marcando o
  ato errado como revogado — **norma viva declarada morta**, com trecho de
  aparência impecável

> Perda se percebe contando. Erro de atribuição, não: sai bem formatado.

### 4.5. Procure o fato de domínio antes de sofisticar o padrão

`LEI COMPLEMENTAR 101` — a LRF federal — aparece em considerandos por todo o
acervo e às vezes fica sozinha numa linha, com forma de cabeçalho.

Nenhum ajuste de regex resolve bem. O que resolveu foi um fato: **o Município
foi instalado em 2001**, logo não existe ato municipal anterior. E outro: a
série municipal é sequencial e chega a 3.917; nada dela tem cinco dígitos.

Isso barrou cinco normas federais e uma estadual que tinham entrado como se
fossem municipais — o servidor as citaria como *"Mesquita/RJ, Lei nº 14.133"*.

### 4.6. Fórmula de estilo não é o que ela parece

"Revogam-se as disposições em contrário" fecha quase todo ato e não revoga nada
identificável. Mas costuma vir seguida de ressalva que **é** expressa:
*"…especialmente o Decreto nº 063/2002"*.

Regra: havendo a cláusula genérica **entre** o verbo e a norma citada, só vale
se houver conector de ressalva. Citação **antes** da cláusula é legítima.

E distinga extensão: *"fica revogado o artigo 93 do Decreto nº 127"* **não**
revoga o Decreto 127. Achatar as duas coisas declara morta uma norma viva.
Exceção: *"revoga todos os artigos da Lei nº 899"* é integral — a menção a
artigo, ali, é a forma de dizer "tudo".

---

## Fase 5 — O diff, que é a fase que ninguém planeja

**Toda alteração no extrator exige comparação registro a registro com a versão
anterior.** Guarde o artefato da versão publicada para poder abri-lo.

O que o diff precisa reportar:

```
ganharam conteúdo · perderam conteúdo · encolheram >40% · sumiram · surgiram
```

Números reais das três tentativas de uma mesma correção:

```
tentativa 1:  63 ganharam · 27 perderam · 34 sumiram   ← 7 leis complementares
tentativa 2:  63 ganharam · 26 perderam ·  9 sumiram
tentativa 3:  63 ganharam ·  3 perderam ·  1 sumiu     ← todas verificadas como correção
```

Na primeira tentativa o total de registros com texto **subiu**. Publicar ali
teria trocado 118 buracos por 118 buracos diferentes, com sete normas a menos e
uma tabela de melhorias para justificar.

**Encolher pode ser conserto.** Um registro que encolheu de 23.536 para 4.354
caracteres não perdeu nada: ele estava engolindo o registro seguinte, cujo
cabeçalho não era reconhecido. O teste é olhar se o vizinho passou a existir.

E o diff audita a versão **já publicada**: foi ele que revelou que oito atos em
produção carregavam texto de outro colado ao seu, e que um número apontava para
norma que não existe.

---

## Fase 6 — As quatro categorias de risco

Os erros que importam não são de recuperação — são de **atribuição**. Cada
acervo tem os seus. Descubra os do seu antes de desenhar as ferramentas.

| Categoria | A pergunta que o sistema erra calado | Onde apareceu |
|---|---|---|
| **Autoria** | quem está falando? | acórdão: defesa ou Tribunal |
| **Tempo** | qual redação rege a matéria? | lei alterada: original ou vigente |
| **Origem** | esta norma é do ente pesquisado? | lei federal entrando como municipal |
| **Fronteira** | onde este registro termina? | ato engolindo o seguinte |

**As quatro produzem resposta impecável quando falham** — citação bem
formatada, dispositivo existente, trecho literal. Nenhuma métrica de busca as
apanha, porque do ponto de vista da busca nada falhou.

A ferramenta central do servidor deve atacar a categoria dominante do seu
acervo. Na jurisprudência foi a proveniência (de que parte do documento veio o
trecho). Na legislação foi a vigência (grafo de revogações e alterações
expressas).

### 6.1. Quando o acervo é memória administrativa

Se o acervo for uma memória decisória interna, como documentos da PGM em Google
Docs e Drive próprio/compartilhado, **registro** deve ser entendido em sentido
amplo. Registro é qualquer peça administrativa catalogável: despacho, decisão,
parecer, relatório, manifestação, informação, cota, encaminhamento ou outro
impulso administrativo. Ele normalmente referencia um processo administrativo,
mas não precisa ser a decisão final nem esgotar o caso.

Nesse tipo de acervo, a unidade de análise não pode ser só o documento. Modele
três camadas:

1. **Registro**: peça individual, com tipo, fonte, data, autoria/origem,
   processo referido, texto integral, fundamentos citados, impulso produzido e
   grau de completude.
2. **Caso administrativo**: conjunto de registros ligados ao mesmo processo ou
   ao mesmo conflito material, com fatos relevantes, pedido, questão jurídica,
   andamento e resultado/impulso alcançado.
3. **Linha decisória**: agrupamento analógico de casos semelhantes, com
   convergências, divergências, distinguishing, mudança de entendimento e
   eventual necessidade de uniformização.

Aqui, a categoria dominante de risco é a **atribuição analógica**: o sistema
acha casos parecidos e trata a semelhança como identidade. Evite isso separando,
em todo resultado:

- proximidade factual;
- proximidade jurídica;
- proximidade normativa;
- proximidade temporal/institucional;
- identidade ou diferença do impulso administrativo obtido;
- presença, ausência ou fragilidade dos fundamentos normativos.

Para cada caso recuperado, a resposta deve indicar: qual era o caso, qual fato
ou pedido controlava a solução, em que ano ocorreu, quais registros sustentam a
leitura, qual foi a decisão ou impulso administrativo, quais fundamentos
normativos foram expressos, quais foram apenas inferidos, e por que o caso é
convergente, divergente ou apenas parcialmente análogo.

A finalidade não é responder: "o Município decidiu assim antes, logo deve
decidir assim agora". A finalidade é orientar o raciocínio do aplicador: mostrar
similaridades, divergências, fundamentos existentes ou ausentes, evolução no
tempo e caminhos defensáveis de convergência ou uniformização.

Ferramentas centrais para esse acervo:

```
buscar_casos_semelhantes(caso_concreto)
obter_historico_processo(numero_processo)
mapear_linha_decisoria(questao_juridica)
comparar_fundamentos(casos)
detectar_divergencias(questao_juridica | caso_concreto)
sugerir_uniformizacao(questao_juridica, divergencias)
listar_registros_sem_processo()
listar_casos_baixa_confianca()
```

E a régua epistemológica precisa aparecer no texto final:

- "semelhança elevada" exige fato controlador, questão jurídica e fundamento
  compatíveis;
- "divergência" exige casos suficientemente próximos com soluções ou impulsos
  diferentes;
- "linha predominante" exige pluralidade e recorte temporal explícito;
- "fundamento normativo ausente" não pode virar fundamento presumido;
- "caso representativo" não é precedente vinculante, mas evidência de prática
  administrativa institucional.

---

## Fase 7 — O servidor MCP

### Arquitetura validada duas vezes

```
Python + SDK `mcp` (FastMCP)     stdio para o Claude · streamable-http para o ChatGPT
SQLite + FTS5 conteúdo externo   sem isso o índice guarda 2ª cópia do texto (54% do banco)
duas buscas separadas            resumo oficial × texto integral
OAuth sem estado (HMAC)          hospedagem gratuita reinicia; tabela de sessão se perderia
.mcpb                            Claude Desktop, offline, sem conta
Docker + Render                  ChatGPT, celular, PC desligado
```

### Duas buscas, propositalmente separadas

De onde veio a proposição é **informação de conteúdo**, não detalhe de
implementação. "Consta da ementa" e "consta do voto, à p. 27" pesam diferente.

A busca é literal, e uma só formulação falha por motivo puramente lexical.
Medido: *"erro de projeto básico justifica aditivo?"* não achou nada;
*"deficiência do projeto básico"* achou na primeira tentativa. Instrua o modelo
a reformular, e devolva no resultado a **expressão efetivamente executada**.

### Instrução não move a primeira frase; o dado move

Meça isto cedo, porque custa três rodadas para acreditar. A instrução do
servidor será obedecida — na seção de ressalvas, ao final da resposta —
enquanto a **frase de conclusão** afirma o contrário. E quem lê uma pesquisa lê
a conclusão.

No acervo de legislação a falha foi: *"Sim, o Plano Diretor continua em vigor"*
aberto, e *"não localizei revogação"* no rodapé. Reescrevi a instrução dizendo
onde a ressalva tem de estar e proibindo "hoje" pelo nome. A resposta seguinte
abriu com *"Não — hoje Mesquita não tem Conselho"*.

O que funcionou foi devolver a frase **pronta, dentro do payload da
ferramenta**, com o número da norma já embutido e nada a compor:

```json
"COMECE_A_RESPOSTA_POR_ESTA_FRASE":
  "A Lei nº 460/2008 foi expressamente revogada pela Lei nº 1.106/2019, e não
   localizei no acervo ato posterior que a restabeleça. Ela não serve como base
   atual."
```

Na medição seguinte as duas perguntas abriram com ela, e o padrão se estendeu
sozinho a normas para as quais a frase não fora pedida.

> Se um comportamento tem de acontecer **no momento em que a ferramenta
> responde**, ele pertence ao payload, não ao preâmbulo. Instrução compete com
> todo o resto do contexto; dado chega junto com a resposta.

Vale para qualquer acervo cuja resposta tenha uma forma epistemológica correta
e uma forma tentadora: gere a forma correta e entregue-a montada.

### As instruções do servidor são código, não documentação

É por elas que o modelo raciocina. Regras que valeram:

- **Régua única**: a ferramenta prova o que encontrou. Nunca "está em vigor";
  sempre "não localizei revogação expressa". A diferença é entre uma pesquisa e
  uma garantia.
- **Procure a contradição dentro do próprio texto.** A regra estava escrita e
  correta, e duas frases minhas logo abaixo diziam "a norma continua valendo" —
  afirmando exatamente o que a regra proibia.
- **Não invente hierarquia.** Eu havia escrito `Lei Complementar > Lei
  Ordinária`, que é falso: o que distingue a complementar é a matéria reservada,
  não uma escada. O modelo teria invalidado uma alteração legítima pela espécie.
- **Formato de citação obrigatório**, com link de conferência. Citação sem
  verificação é armadilha; verificação sem citação é inútil.
- **Declare os limites no mesmo lugar em que responde.** Limite não declarado
  vira afirmação falsa na peça de alguém.

### Ferramenta que falta é a que lista os pontos cegos

A cobertura sabia que 118 registros não tinham texto, e nenhuma ferramenta
permitia recuperá-los **como conjunto**. É justamente o conjunto que importa:
uma busca vazia num deles não significa nada.

---

## Fase 8 — Publicar

### Cadeia de integridade

```
versão fixa → sha256 declarado → conferência no build → falha fechada
```

Teste o caminho ruim: com hash errado, o passo tem de sair com código ≠ 0.

E saiba o que ela **não** prova. Cadeia de integridade responde "é o mesmo
arquivo?", nunca "esse arquivo presta?". Um gzip de banco vazio é válido, tem
hash legítimo, descomprime sem erro e passa no `integrity_check` — a cadeia
inteira diria *ok* a um acervo sem um registro dentro. Foi o que quase subiu
aqui, em 117 bytes.

### Piso de sanidade no passo que publica

O passo que comprime tem de recusar o absurdo antes de produzir o artefato:
acervo ilegível, com zero registro, ou menor que ~95% do último publicado. Duas
consultas de `COUNT(*)`, e a contagem impressa **antes** de comprimir.

Vale mais do que parece, e não pelo motivo óbvio. O incidente aqui foi uma
corrida — a rotina agendada apagou o banco para recriá-lo no exato minuto em
que a mão o copiava — e a corrida se resolve com uma trava de PID. Mas a trava
só cobre a causa que aconteceu; o piso de sanidade cobre também o disco cheio,
a cópia interrompida, o caminho digitado ao contrário e a ingestão que rodou
sobre pasta vazia.

> O último passo antes de publicar é o lugar mais barato do projeto para
> desconfiar, porque é o último em que desconfiar ainda tem efeito.

E não apague a versão anterior antes de a nova ter passado. Nenhum código
conserta isso — é ordem de operações, e o que salvou foi o Git.

### Onde o artefato de dados mora

Princípio herdado: "dado não é código-fonte, vai como asset de release". Foi
invertido aqui, e a inversão tem números: 22 MB numa base recoletada uma ou
duas vezes por ano. A release custava três modos de falha — repositório privado
devolvendo 404 no download anônimo, asset errado anexado, URL divergente do nome
do repositório — mais dependência de rede no build.

> Princípio herdado de outro projeto não se aplica por autoridade — se aplica
> pelos números que o produziram. Quando os números mudam, reexamine; o que não
> se admite é inverter sem dizer.

### Armadilhas de hospedagem, todas medidas

| Armadilha | Sintoma | Causa |
|---|---|---|
| `healthCheckPath` num endpoint MCP | deploy nunca fica saudável, sem motivo visível | `GET /mcp` devolve **406**; só POST responde 200 |
| domínio não declarado | **421** em tudo que vem de fora | proteção contra DNS rebinding; comparação de Host é exata, sem curinga |
| segredo OAuth ausente | conector pede autorização o dia inteiro | só é gerado por Blueprint; criando o serviço à mão, é preciso definir |
| plano gratuito | primeira chamada falha por tempo esgotado | a instância hiberna após ~15 min; acordar leva ~50 s |
| conector em cache | responde com dados novos, mas sem as ferramentas novas | a lista de ferramentas fica guardada de quando foi adicionado — **remover e recriar**, reiniciar não basta |

Não invente chave de configuração de terceiro. Um `dockerBuildArgs` que não
existe fez um deploy inteiro falhar por motivo invisível de fora.

---

## Fase 9 — Teste de aceitação

Testes automatizados provam que o código faz o que você mandou. Não provam se o
modelo pesquisa como alguém cuidadoso e diz a verdade sobre o que encontrou.

**Cinco perguntas, em conversa limpa, sem palavra-chave, sem intervenção. O erro
é o dado.**

Regras que fazem o teste valer:

1. **Critério objetivo de versão antes de começar.** Um campo que só existe na
   versão nova. Sem isso, o cliente responde por cache e o teste inteiro é
   inválido — aconteceu, e perdeu-se uma rodada completa.
2. **Cinco modos de falha distintos**, não cinco variantes de busca.
3. **Cada pergunta ancorada num caso real verificado no acervo** — número, data
   e dispositivo conferidos antes de escrever a pergunta.
4. **A melhor pergunta é a que uma resposta lexicalmente perfeita reprova.**
   *"Existe o Conselho Municipal de Transportes?"* — responder "sim, a Lei
   460/2008 o criou" está impecável e é falso: a lei foi revogada em 2019.
5. **Não acrescente a taxonomia de falhas ao documento antes da rodada.** Isso é
   desenhar o teste depois de conhecer as respostas possíveis.

### Classificar a falha, quando vier

1. **Acionamento** — não chamou a ferramenta que devia
2. **Interpretação** — chamou, recebeu o dado certo, não usou
3. **Formulação** — entendeu, mas escreveu com mais certeza do que a fonte permite
4. **Seleção** — pesquisou certo e escolheu a fonte errada entre concorrentes

A 4 só se afirma com prova de que a candidata relevante foi verificada. Sem ver
as chamadas, o registro honesto é "1 ou 4, indeterminado" — não um palpite.

---

## A divisão de trabalho

| O agente | O humano |
|---|---|
| medir, construir, corrigir, verificar | julgar se serve para o uso final |
| executar contra a fonte | criar contas, conceder OAuth, publicar releases |
| gerar material bruto | ler e dizer o que ele significa |

**Duas coisas o agente não faz**, e é bom que estejam ditas desde o começo:

- **Não usa credencial sua.** `git push` funciona porque o Git resolve a
  credencial internamente; criar release exige chamada autenticada à API, e isso
  é seu. Se quiser delegar, instale e autentique o `gh` — o token fica com ele.
- **Não decide o que serve para a peça.** Nenhuma métrica apanha um trecho
  lexicalmente perfeito e juridicamente invertido. Foi um humano lendo material
  bruto que descobriu que o melhor resultado de uma busca eram *razões de defesa*
  — e que o sistema faria o Tribunal "decidir" o que a parte alegava.

---

## Hipóteses testadas e reprovadas

Registradas para não voltarem como novidade daqui a seis meses.

- **Relaxamento progressivo da busca** (remover o termo mais comum e repetir):
  falhou. Os termos raros são raros por serem polissêmicos — `"exigível"` sozinho
  devolve *"Passivo circulante + Exigível a Longo Prazo"*, termo contábil.
- **Remover verbos fracos da consulta**: corrigiu 1 de 6 casos. Implementado
  porque não piora, mas não era a solução que parecia.
- **Exigir caixa alta para distinguir cabeçalho de citação**: descartou 60 dos
  400 primeiros arquivos, todos legítimos. A lição do projeto anterior
  (*desconfiar da caixa*) estava certa; a regra derivada dela (*exigir caixa
  alta*) estava errada.
- **Consolidação temporal por dispositivo** (a "linha do tempo" de cada artigo):
  adiada de propósito. Exige interpretar comandos de alteração — nova redação de
  caput, acréscimo de inciso, renumeração — e errar produz um dispositivo que
  **nunca existiu em data nenhuma**, com a mesma aparência de um verdadeiro. O
  desenho atual erra por omissão; a consolidação erraria por invenção.

---

## Apêndice — Memória administrativa da PGM

Este apêndice é para o acervo em que o usuário submete um caso concreto ao chat,
e o MCP consulta documentos internos da PGM para encontrar casos similares,
linhas convergentes, divergências e caminhos de uniformização. Não é uma base de
jurisprudência externa; é memória decisória administrativa.

Mantenha este acervo isolado de bases de advocacia privada, estudos pessoais e
materiais doutrinários. Documentos compartilhados podem entrar, mas cada item
precisa preservar cadeia mínima de fonte: de onde veio, quem é o proprietário ou
Drive de origem, quando foi lido e se o acesso era próprio ou compartilhado.

Como o serviço será hospedado, aplique minimização desde o índice. A ferramenta
não precisa expor nome de pessoa física ou jurídica para ser útil. Nas respostas
e nos metadados consultáveis, identifique os casos por número do processo
administrativo e por inscrições/cadastros pertinentes: inscrição municipal,
cadastro imobiliário, cadastro econômico ou outro identificador administrativo.
Nome, CPF/CNPJ, endereço, telefone, e-mail e outros dados pessoais devem ser
suprimidos da saída padrão e, quando preservados por necessidade de auditoria,
ficar em camada restrita fora do texto que o modelo recebe para responder.

### O objetivo da resposta

A resposta ideal não resolve só o caso concreto. Ela deve permitir que o
aplicador enxergue:

- quais casos anteriores realmente se aproximam;
- qual foi o impulso administrativo produzido em cada um;
- quais fundamentos normativos foram usados;
- quais fundamentos aparecem só por inferência;
- onde há divergência sem distinguishing;
- se a divergência é contemporânea, histórica ou resultado de mudança de
  orientação;
- qual caminho de convergência ou uniformização é juridicamente defensável.

O sistema não deve esconder a incerteza. Quando só houver semelhança parcial,
fundamento ausente, documento incompleto ou processo sem decisão final, isso
precisa aparecer como dado do resultado.

### Schema mínimo de registro

Cada registro extraído deve carregar, no mínimo:

```json
{
  "registro_id": "...",
  "documento_id": "...",
  "fonte": "google_drive|google_docs|pdf|outro",
  "url_origem": "...",
  "nome_arquivo_ou_titulo": "...",
  "mime_type": "...",
  "proprietario_ou_drive_origem": "...",
  "escopo_acesso": "proprio|compartilhado|indeterminado",
  "hash_texto_extraido": "...",
  "data_leitura": "...",
  "tipo_registro": "despacho|decisao|parecer|relatorio|informacao|cota|outro",
  "processo_administrativo": "...",
  "inscricoes_ou_cadastros": [
    {
      "tipo": "inscricao_municipal|cadastro_imobiliario|cadastro_economico|outro",
      "numero": "..."
    }
  ],
  "dados_pessoais_suprimidos": true,
  "data_documento": "...",
  "ano": 2026,
  "orgao_origem": "...",
  "autor_ou_setor": "...",
  "area": "tributario|servidores|licitacoes|urbanismo|patrimonio|outro",
  "tributo_ou_materia": "...",
  "questoes_juridicas": ["..."],
  "fatos_controladores": ["..."],
  "pedido_ou_providencia": "...",
  "impulso_administrativo": "deferimento|indeferimento|parcial|encaminhamento|diligencia|parecer|outro",
  "resultado_final_conhecido": "sim|nao|indeterminado",
  "fundamentos_normativos_expressos": ["..."],
  "fundamentos_normativos_inferidos": ["..."],
  "trechos_chave": ["..."],
  "resumo_caso": "...",
  "nivel_confianca_extracao": "alto|medio|baixo",
  "motivos_baixa_confianca": ["..."]
}
```

Dois campos merecem disciplina especial:

- `impulso_administrativo` não é sinônimo de decisão final. Um despacho que
  manda apurar, um parecer que sugere deferimento e uma decisão que indefere
  são registros diferentes, ainda que estejam no mesmo processo.
- `inscricoes_ou_cadastros` deve substituir o nome do interessado na resposta
  normal. Se o caso só puder ser explicado com dado pessoal, a ferramenta deve
  declarar limite de acesso, não improvisar exposição.
- `fundamentos_normativos_inferidos` nunca podem ser apresentados como se
  tivessem sido citados. A resposta deve dizer "não encontrei fundamento
  normativo expresso" quando for o caso.

### Schema mínimo de caso administrativo

O caso administrativo é a camada que impede o sistema de comparar despachos
soltos como se fossem decisões completas.

```json
{
  "caso_id": "...",
  "processos_administrativos": ["..."],
  "registros_relacionados": ["..."],
  "area": "...",
  "materia_principal": "...",
  "questao_controladora": "...",
  "fatos_controladores": ["..."],
  "pedido": "...",
  "linha_do_tempo": [
    {
      "data": "...",
      "registro_id": "...",
      "tipo_registro": "...",
      "impulso": "..."
    }
  ],
  "resultado_ou_estado": "...",
  "fundamentos_expressos_consolidados": ["..."],
  "observacoes_de_completude": "..."
}
```

Regras de agrupamento:

1. processo administrativo igual agrupa por padrão;
2. documentos sem número de processo podem agrupar por combinação de inscrição ou
   cadastro administrativo, matéria, datas próximas e fatos controladores;
3. se o vínculo for inferido, marque o caso como baixa confiança;
4. quando dois registros parecem do mesmo processo, mas indicam soluções
   incompatíveis, não corrija silenciosamente: crie alerta de fronteira ou
   duplicidade.

### Schema mínimo de linha decisória

Linha decisória não é tabela de maioria. É reconstrução crítica de prática
administrativa.

```json
{
  "linha_id": "...",
  "questao_juridica": "...",
  "recorte_temporal": "2019-2026",
  "casos_representativos": ["..."],
  "casos_convergentes": ["..."],
  "casos_divergentes": ["..."],
  "casos_inconclusivos": ["..."],
  "tese_ou_orientacao_predominante": "...",
  "fundamentos_recorrentes": ["..."],
  "fundamentos_ausentes_relevantes": ["..."],
  "mudancas_identificadas": ["..."],
  "pontos_para_uniformizacao": ["..."]
}
```

Um caso só deve ser chamado de divergente quando houver proximidade suficiente.
Solução diferente em matéria parecida pode ser apenas distinção factual. Solução
diferente em caso materialmente semelhante, sem distinguishing explícito, é
divergência relevante.

### Pipeline de ingestão

Ordem sugerida:

1. inventariar fontes do Drive: pastas próprias, compartilhadas, Google Docs,
   PDFs e anexos;
2. extrair texto preservando URL, `document_id`, proprietário/compartilhamento
   e data de modificação;
3. detectar candidatos a registro dentro de cada documento;
4. classificar tipo de registro e extrair metadados;
5. vincular registros a processos administrativos;
6. formar casos administrativos;
7. gerar embeddings separados para texto integral, resumo do caso, fatos
   controladores e questão jurídica;
8. construir índices literais e semânticos;
9. rodar diff registro a registro contra a ingestão anterior;
10. publicar só depois de listar ganhos, perdas, registros sem processo, casos de
    baixa confiança e mudanças de agrupamento.

Não comece com milhares. Comece com uma amostra que contenha documentos bons,
ruins, antigos, recentes, próprios e compartilhados. O primeiro objetivo não é
volume; é descobrir quais campos o acervo permite preencher de verdade.

### Consulta: do caso concreto ao resultado

Fluxo obrigatório da ferramenta principal:

1. transformar o caso narrado pelo usuário em representação jurídica;
2. separar fatos controladores de fatos acessórios;
3. identificar área, matéria, pedido, período e possíveis normas;
4. buscar casos por embeddings e por termos literais;
5. agrupar resultados por caso administrativo, não por documento;
6. selecionar casos próximos, parciais, divergentes e inconclusivos;
7. comparar fundamentos expressos, fundamentos ausentes e impulsos obtidos;
8. responder com a régua de confiança.

Formato mínimo de saída:

```text
Questão apresentada
...

Representação do caso concreto
- área:
- matéria:
- fatos controladores:
- pedido/providência:
- normas possivelmente relevantes:

Casos encontrados
- total de registros:
- total de casos administrativos:
- casos de semelhança elevada:
- casos de semelhança parcial:
- casos divergentes:
- casos inconclusivos:

Casos mais próximos
1. PA ...
   Ano:
   Registros usados:
   Semelhança:
   Diferenças relevantes:
   Impulso administrativo:
   Fundamentos expressos:
   Fundamentos inferidos:

Linha administrativa identificada
...

Divergências e pontos de atenção
...

Avaliação crítica
...

Caminho de convergência ou uniformização
...

Limites da pesquisa
...
```

### Testes de aceitação próprios deste acervo

Além dos testes gerais, este acervo precisa de perguntas que reprovem respostas
apenas semanticamente bonitas:

1. caso com muitos documentos no mesmo processo, para ver se o sistema reconstrói
   a cronologia;
2. caso com despacho intermediário e decisão final diferente, para ver se ele não
   confunde impulso com resultado;
3. dois casos muito parecidos com soluções diferentes, para testar divergência;
4. dois casos parecidos na palavra-chave, mas distintos no fato controlador, para
   testar falsa analogia;
5. caso antigo com fundamento superado ou legislação alterada, para testar tempo;
6. documento sem fundamento normativo expresso, para testar se o modelo inventa;
7. registro sem número de processo, para testar baixa confiança e não exclusão
   silenciosa.

Uma resposta que acha o caso certo, mas omite a incerteza, ainda falhou. O erro
desse MCP não é só não encontrar; é orientar uniformização com base numa analogia
que ele não provou.

---

## Ordem de trabalho, em uma tela

```
1  medir: texto extraível? quantos registros reais? o que é um registro?
2  calibrar com centenas; ler as falhas uma a uma
3  separar coleta de processamento
4  extrair: validar antes de delimitar; 4 critérios para cabeçalho
5  DIFF registro a registro a cada mudança — nunca só o total
6  identificar a categoria de risco dominante do acervo
7  servidor: duas buscas, régua epistemológica, ferramenta dos pontos cegos
8  publicar: cadeia de integridade; testar o caminho ruim
9  teste de aceitação com critério objetivo de versão
```

Os itens 1, 5 e 6 são os que separam um bom banco de dados de uma ferramenta de
pesquisa confiável. Os outros são engenharia.
