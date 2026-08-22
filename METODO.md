# Método — como este acervo foi construído

Registro do que funcionou, do que falhou e do que descartei depois de testar.
Não é manual de boas práticas: é o relato do que **esta** base exigiu, com os
números que sustentam cada decisão.

O acervo do TCE-RJ ensinou dez lições gerais. Esta base repetiu algumas e
acrescentou três que não apareceriam lá, porque legislação não é
jurisprudência.

---

## 1. O que muda quando a base é de normas, e não de julgados

**O precedente envelhece; a norma morre.** Um acórdão de 2008 continua sendo o
que era. A Lei 460/2008, que criou o Conselho Municipal de Transportes, foi
revogada pela Lei 1.106/2019 — e citá-la hoje é erro, não imprecisão.

A busca textual não distingue: devolve a lei revogada com a mesma confiança com
que devolve a vigente, e **nada no texto de uma lei revogada avisa que ela
foi**. Onde o acervo do Tribunal precisava de regras de proveniência (de que
parte do documento veio o trecho), este precisa de um grafo de vigência.

Daí a tabela `referencias`: quem revoga quem, quem altera quem, extraído do
texto dos próprios atos, com o trecho que sustenta cada aresta.

E daí, também, o limite declarado em toda resposta: a ferramenta mostra
revogação **expressa**; ela não certifica vigência. Revogação tácita, norma
superveniente e declaração de inconstitucionalidade estão fora do alcance de
qualquer base montada assim, e prometer o contrário seria a pior coisa que este
servidor poderia fazer.

## 2. Medir o pressuposto antes de escrever a primeira linha

**O texto era extraível?** 143 PDFs amostrados em todos os anos e nas duas
espécies: **98% com texto nativo**, média de 1.000 a 6.000 caracteres por
página. Só 2 eram digitalização sem OCR. A medição autorizou seguir sem
construir pipeline de OCR — que teria sido o maior pedaço do projeto.

**Quantos documentos havia, de verdade?** 7.763 PDFs no disco, mas o download
salvava `_v2`, `_v3` a cada tentativa. Por hash de conteúdo: 3.964 arquivos
distintos, para cerca de 4.000 atos. Contar arquivos teria superdimensionado o
acervo em 96%.

## 3. Perguntar o que é um registro — de novo, e a resposta de novo surpreendeu

No TCE-RJ, o erro caro foi supor que espécie+número+ano identifica um acórdão
(não identificava: um acórdão rende várias ementas).

Aqui o erro seria supor que **um arquivo é um ato**. A partir de 2017 a
Prefeitura publica em Diário Oficial, e o arquivo `Lei_1106_2019.pdf` traz, na
mesma página, a Lei 1.106 **e** o Decreto 2.430 — que dispõe sobre orçamento.

Medido em amostra de 189 arquivos:

```
126 arquivos com 1 ato
 33 arquivos com 2 atos
 11 arquivos com 3 atos
  6 arquivos com 4 atos
  3 arquivos com 8 ou mais — um deles com 17
```

**33% dos arquivos contêm mais de um ato.** Indexar o arquivo sob o nome do
arquivo faria a Lei 1.106 "dispor sobre o quadro de detalhamento orçamentário".
Erro de sentido, não de precisão — e invisível para qualquer métrica de busca,
porque o texto casaria perfeitamente.

Por isso a unidade de registro é o **ato**, segmentado pelo próprio cabeçalho,
e não o PDF.

## 4. Hipótese testada e reprovada: a caixa alta não separa cabeçalho de citação

Cabeçalho e citação têm a mesma forma. `LEI Nº 460 DE 18 DE JUNHO DE 2008` abre
um ato; a mesma cadeia aparece dentro de "Fica revogada a Lei nº 460 de 18 de
junho de 2008". Confundir os dois cria atos inexistentes e atribui texto ao ato
errado.

Primeira hipótese, herdada do projeto anterior (onde `re.IGNORECASE` tinha
anulado a exigência de maiúscula no nome do relator): **exigir caixa alta na
espécie e no mês.**

Reprovada contra os dados. No modelo antigo o próprio cabeçalho vem em caixa
mista — `LEI Nº 013, DE 07 DE maio DE 2001`, e até `Lei nº 005 de 05 de março
de 2001`. A regra descartava **60 dos 400 primeiros arquivos**, todos
legítimos.

O que funcionou foi a **posição**, em duas exigências:

1. O cabeçalho ocupa a linha sozinho — depois da data vem, no máximo, um
   ponto. A citação continua a oração, e é isso que a denuncia mesmo quando a
   quebra de linha do PDF a joga para o início de uma linha.
2. Abaixo do cabeçalho há fórmula de promulgação ou primeiro artigo. Um anexo
   que liste normas revogadas passa pelo critério 1 e não passa por este.

Resultado: arquivos sem cabeçalho reconhecido caíram de **23% para 0,8%** na
amostra de calibração.

> A lição do projeto anterior estava certa como lição e errada como regra. O
> que se transporta entre bases é *desconfiar da caixa*, não *exigir caixa
> alta*.

## 5. O mesmo defeito, duas vezes, e a segunda custou mais caro

O padrão do número era `(\d{1,3}(?:\.\d{3})*|\d{1,5})`. Com `*`, a primeira
alternativa casa "110" de `LEI Nº 1106` e o motor aceita — o ato fica sem ano e
é descartado em silêncio.

No cabeçalho, o efeito foi perda: **1.144 atos sem texto**. Corrigido o
quantificador para `+`, caiu para 118 — de 2.957 para **4.016 atos com texto
integral**.

O mesmo padrão estava no extrator de referências, e lá o efeito não foi perda,
foi **mentira**:

```
"Decreto nº 1059, de 11 de novembro de 2011"  →  lido como Decreto 105
"Decreto nº 2529 de 05 de julho de 2019"      →  lido como Decreto 252
```

O número truncado resolvia para um ato que existe, e o grafo passava a
registrar que o Decreto 252/2005 fora revogado em 2020. Falso — e sustentado
por um trecho de aparência impecável.

> Perda se percebe contando. Mentira, não: ela sai bem formatada, com citação e
> tudo. Foi preciso auditar 130 arestas uma a uma para achar três.

## 6. Cláusula de estilo não é revogação

"Revogam-se as disposições em contrário" fecha quase todo ato do Município e
não revoga nada identificável. Mas ela costuma vir seguida de uma ressalva que
**é** expressa:

```
"revogadas as disposições em contrário, especialmente o Decreto nº 063/2002"
```

Das 130 revogações extraídas, 25 continham a cláusula. Lidas uma a uma: quase
todas traziam conector de ressalva — *especialmente*, *em especial*,
*notadamente* — e eram legítimas. As que não traziam eram citações vizinhas,
sem relação.

Regra final: havendo a cláusula **entre** o verbo e a norma citada, só vale se
houver conector de ressalva. Citação **antes** da cláusula ("revogando o
Decreto nº 792/09 e as demais disposições em contrário") é legítima e não cai
na regra.

## 7. O acervo aceitou leis que não são do Município

Este defeito só apareceu quando alguém foi olhar os dados por outro motivo — eu
procurava casos para o teste de aceitação, e um ID destoou na lista.

O corpo de um decreto de Mesquita cita normas federais e estaduais o tempo
todo, e a diagramação às vezes deixa a citação sozinha numa linha, com forma de
cabeçalho e o corpo do ato logo abaixo. Passa nos dois critérios de posição.
Entraram cinco:

```
Lei federal 14.133/2021    (Licitações)     ← Decreto_3730_2025.pdf
Lei federal 10.520/2002    (Pregão)         ← Decreto_2017_2017.pdf
Lei federal 14.434/2022    (piso enfermagem)← Decreto_3469_2023.pdf
Decreto federal 10.282/2020                 ← Decreto_2742_2020.pdf
Decreto estadual 46.984/2020                ← Decreto_2718_2020.pdf
```

O servidor as citaria como **"Mesquita/RJ, Lei nº 14.133, de 1º de abril de
2021"**. Não é imprecisão: é erro de competência — atribui ao Município uma lei
que ele não poderia ter feito, e que ninguém corrige lendo a resposta, porque a
citação sai bem formatada.

A regra que resolveu é a mesma do item 8, aplicada de novo: **um fato sobre o
mundo, não um ajuste de padrão.** A série municipal é sequencial. Pelo catálogo
do portal, ela chega a 1.288 (leis) e 3.917 (decretos); nada de Mesquita tem
cinco dígitos. O teto vem dos dados e cresce sozinho quando o portal publicar
mais.

Sobra um caso que o teto não pega: **a lei complementar federal tem número
baixo**, dentro da faixa municipal. LC 101, 116, 123, 173. Essas ficam por
conta de uma lista nominal — solução pior, e assumida como tal.

> Custo de não ter feito antes: nenhum, porque foi pego. Custo se não tivesse
> sido pego: um parecer citando a Lei de Licitações como norma de Mesquita.

E, no mesmo exame, um erro de classificação: `REVOGA TODOS OS ARTIGOS DA LEI Nº
899/2015` estava marcado como revogação **parcial**, porque a palavra "artigos"
aparece. Revogar todos os artigos é revogar a lei — e dizer "parcial" ali faria
a ferramenta afirmar que a norma subsiste.

## 8. O catálogo do portal e o cabeçalho do ato discordam — e o cabeçalho ganha

O relatório de download cataloga **Lei Complementar como "Lei"**: a LC 2/2002
aparece como Lei 2/2002. Quem sabe a espécie é o cabeçalho do próprio ato.

Sem reconciliar, nasciam duas entradas para a mesma norma — uma com ementa e
sem texto, outra com texto e sem ementa. É a lição do "o que é um registro?"
aplicada ao encontro de duas fontes que descrevem o mesmo objeto com
vocabulários diferentes.

Do portal veio o que ele sabe melhor: a **ementa oficial** e a URL de origem.
Do PDF veio o que só ele sabe: a **espécie**, a data e o texto.

## 9. Uma regra de domínio vale mais que dez de higiene

`LEI COMPLEMENTAR 101` — a LRF — aparece citada em considerandos por todo o
acervo, e a diagramação às vezes a deixa sozinha numa linha, com forma de
cabeçalho.

Nenhum ajuste de regex resolveria isso bem. O que resolveu foi um fato:
**Mesquita se emancipou de Nova Iguaçu e foi instalada em 2001**, logo não
existe ato municipal anterior. Piso em 2001, e a norma federal de 2000 sai
sozinha.

> Antes de sofisticar o padrão, perguntar se há um fato sobre o mundo que
> torna o caso impossível.

## 10. O que se manteve do projeto anterior, sem alteração

- **Separar coletar de processar.** Os PDFs vieram do portal e ficaram
  intocados; a ingestão foi refeita três vezes, de graça, sem tocar na fonte.
- **Conteúdo externo no FTS5**, para o índice não guardar segunda cópia do
  texto.
- **Cadeia de integridade na publicação**: versão fixa → sha256 declarado →
  conferência no build → falha fechada.
- **Duas buscas separadas** — ementa e corpo do ato —, porque de onde veio a
  proposição é informação jurídica, não detalhe de implementação.
- **Teste de aceitação comportamental**, com critério objetivo de que o cliente
  carregou a versão nova antes de valer.

## 11. O que ainda depende de quem entende do assunto

O grafo de vigência resolve o caso fácil: revogação expressa, citada com número
e data. Não resolve:

- **Revogação tácita** — lei nova incompatível com a antiga, sem dizê-lo.
- **Revogação parcial** — "ficam revogados os arts. 3º e 4º" deixa a lei viva,
  e o grafo hoje marca a relação sem qualificar a extensão.
- **Texto compilado** — o acervo guarda a redação original; lei alterada dez
  vezes aparece como foi promulgada.

Nenhuma das três se resolve com mais engenharia sobre o mesmo material. As duas
primeiras exigem leitura jurídica; a terceira, uma fonte que o Município não
publica.

Estão declaradas em `cobertura_do_acervo` e nas instruções do servidor, porque
limite não declarado vira afirmação falsa na peça de alguém.

## 12. Escrevi uma hierarquia que não existe

As instruções do servidor diziam, em letra de fôrma:

```
Lei Orgânica > Lei Complementar > Lei Ordinária > Decreto
```

A primeira e a última relações estão certas. A do meio é falsa: **não há
superioridade hierárquica genérica da lei complementar sobre a ordinária**. O
que distingue a complementar é o processo legislativo e, sobretudo, a matéria a
ela reservada.

O erro não era decorativo. O próprio teste do ITBI põe o caso na mesa: a LC
17/2014 é complementar, e quem alterou o seu art. 41 foi a **Lei ordinária
1.283/2025**. Com a escada escrita daquele jeito, o modelo tinha tudo para
concluir que a alteração seria inválida *pela espécie* — objeção que não se
decide assim, e que dependeria de saber se a matéria está reservada à lei
complementar. A norma que fixa essas reservas no Município é a Lei Orgânica, e
ela **não está no acervo**.

Eu teria reprovado ou aprovado o modelo por uma premissa jurídica minha, errada.

> A instrução do servidor não é documentação: é a regra pela qual o modelo
> raciocina. Um erro de direito ali propaga com a autoridade da ferramenta —
> e não aparece em teste nenhum, porque o teste também foi escrito por mim.

## 13. A régua epistemológica tem de valer em todo lugar, inclusive nos textos auxiliares

A regra central estava escrita e correta: *diga "não localizei revogação
expressa", nunca "está em vigor"*. Mas duas frases minhas, poucas linhas
abaixo, faziam exatamente o contrário:

```
revogado_parcialmente_por → "a norma continua valendo"
alterado_por              → "o texto NÃO reflete a redação em vigor"
```

As duas afirmam o estado da norma. A primeira diz que ela vale; a segunda,
que existe uma redação vigente diferente da guardada. Nenhuma das duas é
sustentada por um grafo de revogações expressas — e estavam no mesmo campo que
o modelo lê como limite autoritativo.

Reescritas para a régua única: *a revogação localizada é parcial e não autoriza
tratar a norma como integralmente revogada; quanto ao restante, não foi
localizada revogação expressa*.

> Regra declarada num lugar e contrariada em outro não é regra: é preferência.
> Ao escrever um limite, procurar no mesmo documento as frases que o violam.

## 14. Três categorias de risco, e todas produzem resposta impecável

Somando o que as duas bases ensinaram, os erros que importam não são de
recuperação — são de atribuição, e cada acervo tem o seu:

| Base | A pergunta que o sistema erra calado |
|---|---|
| Jurisprudência (TCE-RJ) | **quem está falando?** — defesa ou Tribunal |
| Legislação, no tempo | **qual redação rege a matéria?** — original ou alterada |
| Legislação, na origem | **essa norma é sequer do ente pesquisado?** |

A terceira só apareceu neste projeto, e por acaso: eu procurava casos para o
teste de aceitação quando um identificador destoou na lista.

O que as três têm em comum é o que as torna perigosas: **quando dão errado, a
resposta sai perfeita** — citação bem formatada, dispositivo existente, trecho
literal. Nenhuma métrica de busca as apanha, porque, do ponto de vista da
busca, nada falhou.

## 15. O acervo voltou para dentro do Git — e por quê

O projeto anterior tirou o banco do Git com um princípio claro: *artefato de
dados não é código-fonte*. Aqui a decisão foi invertida, e a inversão precisa
ficar registrada com o motivo, senão vira desleixo aos olhos de quem ler depois.

**O que mudou nos números.** Lá eram 81,3 MB comprimidos para 24,0, num acervo
que se recoletava com frequência. Aqui são 69,2 MB para **21,6**, numa base
municipal que se recoleta uma ou duas vezes por ano. O princípio pesava por
*tamanho* e por *churn*; os dois encolheram.

**O que a release custava.** Ela introduzia três modos de falha, e dois deles
nos apareceram de fato:

| Falha | Como se manifestava |
|---|---|
| Repositório privado | download anônimo do asset recebe 404, e o log não diz que a causa é a visibilidade |
| Asset errado anexado | conferência de sha256 barra — mas só depois de um build inteiro |
| Nome do repositório | a URL fica dentro do `Dockerfile` e tem de bater com o que se criou no GitHub |

Somava-se a isso uma dependência de rede no meio da construção da imagem.

**O que não mudou.** A cadeia de integridade continua inteira: `versão fixa →
sha256 declarado → conferência antes de descomprimir → falha fechada`. Foi
verificada fora do Docker, inclusive o caminho ruim — com hash errado, o passo
sai com código diferente de zero e a construção para.

**O custo, dito com clareza.** Cada versão do acervo deixa ~21,6 MB permanentes
no histórico do Git. Apagar o `.gz` antigo alivia a imagem, não o histórico.
Quando isso incomodar, a volta é uma linha: o `instalar_acervo.py` aceita
caminho local **ou** URL, e o `preparar_release.py` imprime as duas formas.

> Princípio herdado de outro projeto não se aplica por autoridade — se aplica
> pelos números que o produziram. Quando os números mudam, a decisão se
> reexamina; o que não se admite é inverter sem dizer.

## 16. O diff contra a versão anterior, e por que ele salvou o projeto

A pergunta que abriu isto foi simples: *quais atos estão sem texto?* Eram 118.
Medindo a causa, 104 tinham texto no PDF — não era digitalização, era o parser.

Corrigi. A métrica agregada melhorou. E eu quase publiquei.

O que impediu foi comparar **ato a ato** com a versão anterior, em vez de
comparar totais:

```
tentativa 1:  63 ganharam · 27 perderam · 34 sumiram  ← 7 leis complementares
tentativa 2:  63 ganharam · 26 perderam ·  9 sumiram
tentativa 3:  63 ganharam ·  4 perderam ·  1 sumiu
```

Na primeira tentativa o total de atos com texto **subiu**. Se eu tivesse olhado
só isso, teria publicado uma versão sem a LC 18/2015 — que altera o Código
Tributário — e com uma tabela de melhorias para justificar.

### As três correções, e o padrão entre elas

Cada uma foi precisa numa direção e cega na oposta:

| Problema | Primeira ideia | Efeito colateral | Regra final |
|---|---|---|---|
| Citação virando cabeçalho | proibir quebra de linha | matou `LEI COMPLEMENTAR` partida em duas | **contar** quebras: no máximo uma |
| Frase continuando | recusar linha terminada em `,` ou `:` | matou `PROMULGO A SEGUINTE LEI:` | só palavras de ligação |
| Palavra virando mês | exigir as doze grafias | matou `OUTRUBRO`, `AGOSOTO`, `DEJUNHO` | raiz de três letras, **ou** a moldura `DE dia DE … DE ano` |

Nenhuma das três teria aparecido em teste: em todas eu estava consertando algo
real, e o número agregado subia.

> Correção não se avalia pelo que ela conserta. Avalia-se pelo diff — e o diff
> tem de ser por registro, não por total.

### O que o diff revelou sobre a versão que já estava no ar

O achado mais desconfortável não foi sobre as correções: foi sobre `v1.0.0`,
publicada e em produção.

- A **Lei 418/2008** tinha 23.536 caracteres porque **engolia a Lei 419
  inteira**, cujo cabeçalho não era reconhecido. Quem pedisse uma recebia duas.
- O **Decreto 1.995/2017** servia o corpo do **Decreto 1.998**, capturado de
  uma citação — `"nos termos do Decreto nº1995/2017; CONSIDERANDO…"`.
- A **"Lei 95/2003"** não existe. Era um fantasma nascido de uma citação, e não
  consta do catálogo do portal nem tem PDF.

Oito atos estavam com texto de outro colado ao seu, e um número apontava para
norma inexistente. Nada disso apareceu em 67 testes, nem na conferência de
cobertura, nem no teste de aceitação — porque a busca funcionava, a citação
saía formatada e o texto era real. Só era de outro ato.

> É a quarta categoria de risco desta série, e a mais silenciosa: não é "quem
> está falando", nem "qual redação vige", nem "de que ente é a norma". É **onde
> este ato termina**.

## 17. Onde o ato termina — a fronteira, e o corte que não pode ser feito

Descoberto ao atualizar o acervo com o Diário Oficial: a **Lei 1.290/2026, que
renomeia uma rua, tinha 24.108 caracteres**. O ato acaba em 718; os 23 mil
seguintes eram extratos de ata de registro de preços, portarias do DPMM e
decisões de IPTU publicadas na mesma edição.

Numa página de Diário o ato acaba e a edição continua. Sem fechar a fronteira,
o segmento vai até o próximo cabeçalho de LEI ou DECRETO — que pode estar vinte
mil caracteres adiante.

### O corte óbvio é o errado

A tentação é cortar na assinatura: `Mesquita, <data> / <nome> / Prefeito`. Uma
medição rápida sugeria 614 atos "inflados" por esse critério.

**Esse número era falso**, e olhar os maiores mostrou por quê:

```
decreto-2001-2017  "Aprova, na forma do Anexo I, o Quadro de Detalhamento"
                    848 caracteres de ato · 190.150 de anexo
lei-1251-2024      "INSTITUI A POLÍTICA DE RESÍDUOS SÓLIDOS ... E O PLANO"
                  4.571 caracteres de ato ·  76.187 de plano anexo
```

**O anexo vem depois da assinatura, e é o conteúdo que o ato aprova.** Cortar
ali destruiria Quadros de Detalhamento, tabelas de classificação de atividades
econômicas e planos municipais inteiros — justamente o que se consulta.

### A regra: cortar só o que se identifica positivamente

Fui ler o que aparece depois da assinatura, e são três coisas:

| O que vem | Exemplos reais | É do ato? |
|---|---|---|
| Anexo | `ANEXO I – CLASSIFICAÇÃO DE ATIVIDADES`, `ANEXO 01 TABELA DE MULTAS` | sim |
| Mobília da página | `www.mesquita.rj.gov.br`, `Nº 00434`, traços | inofensivo |
| Outro documento | `EXTRATO DE TERMO ADITIVO`, `PORTARIA Nº 131/2014`, `DECISÃO PROCESSO` | **não** |

O corte acontece **só no terceiro caso**, identificado pelo cabeçalho do outro
documento em início de linha. Nunca na assinatura.

### Validar antes de aplicar, contra o acervo inteiro

A regra foi rodada sobre os 4.075 atos **sem gravar nada**:

```
intactos: 3.054      cortados: 1.021      removidos: 1.821.182 caracteres
```

E os seis controles que terminam em anexo ficaram intactos, byte a byte.

Depois, o diff contra produção: 588 atos encolheram, e as 30 referências que
saíram do grafo de vigência foram conferidas uma a uma. **Todas vinham de
documento alheio** — a maioria de decisões de IPTU cuja ementa cita `LEI
COMPLEMENTAR MUNICIPAL 017/2014, ALTERADO PELA 018/2015`, e uma de um edital
de convocação cujo preâmbulo cita competência. Nenhuma perda legítima.

> A fronteira precisa valer também para a tabela de páginas, não só para o
> texto. É ela que alimenta a busca por dispositivo: cortar só o texto deixaria
> a portaria alheia pesquisável dentro do ato.

### Por que isto é a quarta categoria de risco

Não é "não achou" nem "achou o errado": é **achou o certo e entregou junto o
que não é dele**. A Lei 1.290 responderia a uma busca por "registro de preços"
ou "perícia médica" — assuntos que ela não trata —, com citação impecável.

## 18. Código correto que não faz nada

Ao ligar o Diário Oficial à ingestão, dei ao parâmetro novo o nome de uma
variável local que já existia:

```python
def construir(..., diarios: Path | None = None):
    ...
    diarios: dict[str, tuple[str, str]] = {}     # ← sobrescreve, oito linhas depois
    ...
    edicoes_do_diario(diarios, desde) if diarios else iter(())
```

O dicionário vazio substituía o caminho da pasta, e `if {}` é falso. **Nenhuma
exceção, nenhum aviso, 90 testes passando.** A ingestão rodou treze minutos e
reportou `lidos 3964 arquivos` — o mesmo número da rodada anterior, que foi a
única pista de que nada havia sido lido.

> Código que quebra se acha pelo erro. Código correto que não faz nada só se
> acha pelo número que deveria ter mudado e não mudou.

## 19. Consolidação temporal: adiada de propósito

O salto seguinte desta base seria a **linha do tempo por dispositivo**. Hoje o
acervo sabe:

```
LC 17/2014  — texto original
LC 23/2018  — altera o art. 3º
Lei 1.283/2025 — dá nova redação ao art. 41
```

O que ele não produz, e seria o passo natural:

```
Art. 41 da LC 17/2014
  2014–2025 → redação original
  2025–?    → 3%, redação dada pela Lei 1.283/2025
```

**Não construir isto agora é decisão, não pendência.** Montar texto consolidado
exige interpretar comandos de alteração: nova redação de caput, acréscimo de
inciso, renumeração, revogação de alínea, alteração de anexo. Errar qualquer um
produz um artigo que **nunca existiu em nenhuma data** — e que sai da ferramenta
com a mesma aparência de um artigo verdadeiro.

O desenho atual — texto publicado + grafo de alterações + obrigação de conferir
— erra por omissão: manda o advogado ler dois atos. A consolidação automática
erraria por invenção. Numa base jurídica, as duas falhas não têm o mesmo peso.

> Registrado aqui para que a ideia não volte daqui a seis meses como novidade,
> e para que, quando voltar, volte com o problema certo à frente: não é
> "juntar os textos", é *interpretar comandos de alteração sem inventar*.

---

## 20. A automação e a mão colidiram, e quase publicaram um acervo vazio

Dia 22/08/2026, 10h. A tarefa agendada de sábado dispara sozinha e começa a
reconstruir `dados/staging.sqlite` — e a ingestão, como sempre fez, **apaga o
banco antes de recriá-lo**. Às 10h05, sem saber disso, eu copio o arquivo por
cima do acervo publicado e mando comprimir. O `preparar_release.py` obedece:
gera 117 bytes de gzip com **zero ato** dentro, sem uma linha de reclamação. O
artefato da v1.3.0 eu já tinha apagado.

O acervo voltou com `git checkout -- acervo/` — 4.134 atos, sha256 conferido,
`integrity_check` intacto. É o único motivo pelo qual isto é uma anedota e não
uma perda.

Três coisas erradas ao mesmo tempo, e vale separá-las porque só a primeira é
sobre concorrência:

1. **Nada impedia dois processos de escreverem o mesmo banco.** Agora impede:
   `legis/trava.py` grava um arquivo com o PID e o dono, recusa começar se o
   dono ainda estiver vivo, e assume a trava se o PID estiver morto — trava
   órfã de máquina desligada no meio não pode bloquear o sábado seguinte para
   sempre.

2. **O passo de publicar acreditava no que recebia.** `conferir()` agora recusa
   comprimir acervo ilegível, com zero ato, ou menor que 95% do último
   publicado, e imprime a contagem **antes** de comprimir. A trava evita a
   corrida; esta conferência evita a consequência, venha ela de onde vier — e
   custa uma consulta de `COUNT(*)`.

3. **Eu apaguei a versão anterior antes de a nova estar pronta.** Nenhum código
   conserta isso. Ficou como regra no `HOSPEDAGEM.md`: o `.gz` antigo sai
   depois que o novo passou, não antes.

O que este caso ensina não é "ponha um mutex". É que **um piso de sanidade no
último passo pega a falha inteira de classes de causa que você não previu.**
A trava resolve a corrida que aconteceu; `conferir()` teria pego essa e também
o disco cheio, a cópia interrompida, o caminho errado e o meu dedo trocando
`staging` por `mesquita` na direção contrária. O passo que publica é o lugar
mais barato do projeto para desconfiar, porque é o último em que desconfiar
ainda tem efeito.

E o defeito era **silencioso por construção**: gzip de banco vazio é um arquivo
válido, com hash legítimo, que descomprime sem erro e sobe no Docker sem
reclamar. A cadeia de integridade inteira — sha256 declarado, conferido,
`integrity_check` — teria dito *ok* a um acervo sem nenhuma lei dentro. Cadeia
de integridade prova que o arquivo é o mesmo; não prova que ele presta.

---

## 21. O teste de aceitação achou o que 107 testes automatizados não achavam

Rodado em 22/08/2026 sobre a v1.4.0. Cinco conversas limpas, cada uma com uma
pergunta e nada mais, proibidas de ler o disco. Resultado em
`RESULTADO-TESTE-ACEITACAO.md`: aprovado, sem nenhuma citação inventada.

O que importa aqui é o que ele encontrou **na base**, não nas respostas.

### Três normas vivas marcadas como mortas

| marcada como morta | a cláusula que a matou |
|---|---|
| LC 15/2011 — Uso, Ocupação e Parcelamento do Solo | "revogando o disposto em contrário **na** LC 15/2011" |
| Lei 224/2005 — Quadro Permanente de Pessoal | "revoga o disposto em contrário **na** Lei nº 224" |
| Lei 1.206/2022 — Licenciamento Ambiental | "revoga **dispositivos** da Lei nº 1.206" |

O §6 deste documento já dizia que cláusula de estilo não é revogação, e a
guarda estava escrita — só que no plural. "Revogam-se as disposições em
contrário" era reconhecido; "revoga o disposto em contrário" não. E a
preposição, que parece detalhe, inverte o sentido: *"em especial **a** Lei X"*
revoga a Lei X inteira; *"o disposto em contrário **na** Lei X"* preserva a Lei
X e alcança só o que nela conflitar — que é revogação tácita, declaradamente
fora do alcance desta base.

> Uma regra escrita para uma redação não é uma regra sobre o fenômeno. O
> fenômeno aqui é "o legislador fecha o ato mandando cair o que conflitar", e
> ele o escreve de pelo menos quatro maneiras. Eu tinha coberto uma.

### Quem achou não foi a rubrica: foi a desconfiança

A pergunta 3 era sobre o Plano Diretor. A resposta consultou a vigência, viu a
LC 15/2011 sinalizada como revogada, **foi ler a lei revogadora inteira**, viu
que ela só altera um inciso sobre plantio de árvores no "Habite-se", e avisou o
advogado de que a ferramenta estava errada.

Nenhuma linha da rubrica pedia isso. Eu não imaginei que fosse possível pedir.
Vale como lição sobre o que um teste de aceitação é: **não é uma checagem das
hipóteses de quem escreveu o teste** — é a única etapa em que alguém que não
conhece o projeto olha para ele.

### E dois defeitos que só apareceram porque tentei consertar os primeiros

**A janela de releitura estava ancorada na ponta errada.** A rotina semanal
relia o Diário a partir de `MAX(data) − 21 dias`. Mas quem corre risco de sumir
não é o ato mais novo: é o mais **antigo** que existe *só* no acervo do Diário,
porque o portal ainda não o publicou como PDF individual. A janela deslizava
para a frente toda semana e deixava esses para trás. Na reconstrução, três atos
sumiram — dois decretos e a LDO de 2027. O diff os pegou e a rotina parou, que
é o desenho funcionando; mas parar toda semana no mesmo defeito é convite a
promover sem ler. A âncora passou a ser `MIN(data)` entre os atos cujo arquivo
vem de `DOM/`.

**A Prefeitura reutiliza número de ato.** Existem dois Decretos 3.914/2026: um
de 26 de junho, sobre mudança de simbologia de cargo em comissão, e outro de 8
de julho, que abre crédito suplementar. Ambos publicados no Diário, ambos com
esse número no próprio cabeçalho. Medido nas 152 edições de 2026: **três
números reutilizados em 104 atos identificados**.

A chave do acervo é `tipo-número-ano`. Ela pressupõe unicidade que o Município
não pratica, e o resultado é uma quimera: um ato fica com o corpo de um e a
ementa do outro. **Isto não foi consertado na v1.5.0** — consertar exige mudar
o identificador de todos os atos, e com ele as URLs e o contrato das
ferramentas. Fica registrado, medido, e é a primeira coisa a resolver numa v2.

> É a quarta categoria de risco do §14 — *fronteira*: onde termina este ato e
> começa o outro. Eu a tinha tratado dentro do arquivo. Ela também existe entre
> arquivos, quando dois documentos reivindicam a mesma identidade.

---

## 22. Duas contas para "o que falta", e uma delas é a errada

A conferência mecânica das citações do teste de aceitação — 127 ocorrências nas
dez respostas — encontrou exatamente uma apontando para fora do acervo: a
**Lei Complementar nº 1/2002, o Código de Obras**, citada porque o art. 100 da
Lei 355/2006 revoga os seus arts. 15 a 18.

A resposta estava certa. A base é que não avisava.

Ao medir o buraco, quase publiquei o número errado. A primeira conta que fiz
foi a dos **números que faltam na série**: 97 leis e 1.089 decretos, 27,7% da
série de decretos. É um número grande, verdadeiro e **imprestável para
orientar** — ninguém sabe se aqueles decretos existem, e o advogado que o
lesse concluiria que a coleta falhou.

A segunda conta é a que responde à pergunta: **quanto do que a fonte publica
chegou até aqui.** Medida contra o catálogo do Portal da Transparência:

```
catalogados pelo portal      4.074
desses, ausentes do acervo       0
achados só no Diário Oficial    69
```

Zero. O acervo tem tudo o que a fonte publica, e ainda 69 atos que a fonte não
cataloga. Os 1.089 decretos faltam **na fonte**, não na coleta — e o Código de
Obras também: o portal não o publica.

As duas foram para o `cobertura_do_acervo`, porque separadas elas dizem coisas
diferentes e juntas dizem a verdade inteira: *o limite é a transparência do
Município, não a nossa coleta.* Publicar só a primeira teria acusado o próprio
trabalho; publicar só a segunda teria dito que não falta nada.

> Antes de publicar um número sobre uma falha, pergunte o que o leitor vai
> decidir com ele. "Faltam 1.089 decretos" e "temos 4.074 de 4.074" descrevem
> o mesmo acervo e levam a decisões opostas.

### E o caso que nenhuma das duas pega

A LC 1/2002 é o **primeiro** número da série de leis complementares, que no
acervo começa em 2. Buraco só se mede entre o primeiro e o último existentes —
uma ausência antes do mínimo é invisível por construção. Por isso
`buracos_na_numeracao` declara `primeiro_numero`, e por isso o Código de Obras
está nomeado, com todas as letras, entre os `limites_do_acervo`: em matéria de
obras e licenciamento, o silêncio desta base não significa nada.

> Toda métrica de completude tem uma borda que ela não enxerga. Vale procurar
> qual é a sua e declará-la ao lado do número — senão o número vira promessa.

---

## 23. Instrução não move a primeira frase; o dado move

O teste de aceitação mediu, duas vezes, a mesma falha: a ressalva correta na
seção de limites, ao final, e a afirmação categórica na frase de conclusão —
*"Sim, o Plano Diretor continua em vigor"*, *"Não, o Conselho foi extinto em
2019"*. Quem lê a resposta inteira não se engana. Quem lê a conclusão e cita,
sim, e é assim que se lê uma pesquisa.

Diagnostiquei como conserto de instrução, e consertei a instrução. Ela passou a
dizer onde a ressalva tem de aparecer, a proibir "hoje", "atualmente" e "segue
valendo" pelo nome, e a trazer os dois casos reais com o antes e o depois.

A resposta seguinte abriu com **"Não — hoje Mesquita não tem Conselho
Municipal de Transportes"**.

O que funcionou foi mover a frase para dentro do dado. `verificar_vigencia`
passou a devolver `COMECE_A_RESPOSTA_POR_ESTA_FRASE`, montada com o número da
lei dentro, sem nada para compor:

```
A Lei nº 460/2008 foi expressamente revogada pela Lei nº 1.106/2019, e não
localizei no acervo ato posterior que a restabeleça. Ela não serve como base
atual.
```

Na medição seguinte, as duas perguntas abriram com essa frase, quase literal. E
o padrão se estendeu sozinho a uma norma para a qual a frase não havia sido
pedida.

> **Instrução compete com dez mil caracteres de contexto; dado chega junto com
> a resposta.** Se um comportamento tem de acontecer no momento em que a
> ferramenta responde, ele pertence ao *payload*, não ao preâmbulo. Foi assim
> que a `advertencia` pegou desde o começo — e eu levei três medições para
> perceber que era o mesmo mecanismo.

O corolário incomoda: **instrução que descreve o certo não é conserto, é
esperança.** A diferença entre as duas versões não é conteúdo — as duas dizem a
mesma coisa. É posição.

### O passo seguinte, e a extração que eu não publiquei

A frase pronta cobre *vigência*. Ela não cobre o erro que apareceu em duas
rodadas seguidas: a resposta lê o art. 128 da Lei 355/2006 (30 membros,
redação de 2006), lê a Lei 1.271/2025 (15 membros) e conclui "reduziu de 30
para 15". A Lei 628/2010 já o havia levado a 16.

Na quinta rodada, uma resposta errou e outra acertou — mesmo acervo, mesma
aresta. A diferença é estrutural: **o grafo diz QUEM alterou; nunca o que a
redação dizia antes desta.**

O conserto óbvio era extrair, do ato alterador, qual dispositivo do alvo ele
atinge — assim a ferramenta poderia dizer "o art. 128 já foi mexido em 2010".
Escrevi o extrator e o medi contra oito atos cujo alvo eu conhecia:

```
Lei 628/2010    extraiu [119, 128, 132]   correto: 119, 128, 130
LC 47/2023      extraiu [20]              correto: 20 a 23
LC 52/2024      misturou artigos da LC 36 com artigos do Código Tributário
```

Inventou um artigo, perdeu outro, e leu "arts. 20 a 23" como só o 20. **Não
publiquei.** Número de artigo errado é precisamente o erro de aparência
impecável contra o qual esta base inteira foi construída, e uma etiqueta
dizendo "extraído automaticamente, pode estar incompleto" não protege contra
uma entrada *errada* — só contra as que faltam.

O que foi publicado é o aviso que não depende de extração nenhuma, e por isso é
verdadeiro por construção:

> São 5 atos alteradores de 2009 a 2025, e o texto guardado aqui é o ORIGINAL.
> Antes de dizer o que a alteração mais recente mudou, verifique se aquele
> mesmo dispositivo já não havia sido alterado por um dos anteriores.

Ele aparece só quando há duas ou mais alterações — com uma só não existe
redação do meio para saltar, e aviso que aparece sempre é ruído que ninguém lê.

> A tentação, depois de um conserto que funcionou, é aplicar o mesmo molde ao
> problema seguinte sem medir. Medi, e o molde não coube: a frase de vigência é
> derivada de fatos que o acervo tem: a lista de dispositivos exigiria fatos
> que ele não tem. **Entregar pronto só é honesto quando o que se entrega é
> certo** — do contrário, é dar autoridade a um palpite.

---

## O que eu repetiria em outra base

1. Medir o pressuposto antes da primeira linha — aqui, se havia texto extraível.
2. Perguntar o que é um registro, e conferir contra os dados. A resposta óbvia
   ("um arquivo, um ato") estava errada em 33% dos casos.
3. Calibrar com centenas antes de milhares: os defeitos de formato aparecem em
   400 arquivos, não em 4.000.
4. Auditar as arestas do grafo uma a uma. Perda se percebe contando; erro de
   atribuição, só lendo.
5. Procurar o fato de domínio que dispensa a sofisticação do padrão.
6. Declarar o que a ferramenta **não** faz, no mesmo lugar em que ela responde.
7. Pôr um piso de sanidade no passo que publica — contagem mínima, não
   encolhimento. É o último lugar em que desconfiar ainda adianta, e ele pega
   as causas que ninguém previu.
