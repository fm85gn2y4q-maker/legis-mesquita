# Resultado do teste de aceitação

Duas rodadas: **v1.4.0** em 22/08/2026 e **v1.5.0** no mesmo dia, depois das
correções que a primeira motivou. Mesmas cinco perguntas, mesmas restrições.

Cada respondente recebeu **só a pergunta**, nenhuma informação sobre o projeto,
e foi proibido de ler o disco — o repositório com o gabarito estava debaixo
dele. Verificado no transcrito das dez conversas: **nenhuma chamada a Bash,
Read, Grep ou Glob**, em nenhuma delas.

> **Ressalva de método.** É o servidor publicado sob um cliente que não é o
> Claude Desktop nem o ChatGPT. Prova o acervo e o comportamento do modelo; não
> prova os dois clientes.

| portão de versão | v1.4.0 | v1.5.0 |
|---|---|---|
| Atos | 4.143 | 4.143 |
| Páginas | 10.531 | 10.536 |
| Revogações integrais | 84 | **81** |
| Revogações parciais | 16 | **18** |

---

## Veredito

**Aprovado nas duas.** Nenhuma citação inventada em dez respostas. Conferi as
decisivas à mão — número, ano, data e texto do dispositivo, palavra por palavra —
e depois **todas** por programa: 127 ocorrências, uma única apontando para um ato
ausente do acervo, e essa por culpa da base, não da resposta (veja adiante).

| | 1 · revogada | 2 · alterada | 3 · parcial | 4 · ementa | 5 · vocabulário |
|---|---|---|---|---|---|
| `verificar_vigencia` (r1 / r2) | 4 / 3 | 2 / 2 | 2 / 2 | 1 / 1 | 3 / 3 |
| Chamadas totais (r1 / r2) | 25 / 23 | 20 / 19 | 18 / 17 | 19 / 21 | 27 / 25 |
| Ficou em "não localizei" | não / **melhor** | quase / quase | não / não | sim / sim |sim / sim |
| Hierarquia decidida pela espécie | não / não | não / **SIM** | não / não | não / não | não / não |
| Citação inventada | não / não | não / não | não / não | não / não | não / não |

---

## Conferência mecânica das citações

A primeira versão deste documento afirmava "nenhuma citação inventada" com base
em amostragem — eu conferi as que me pareceram arriscadas. Refeito por
programa, sobre o texto das dez respostas, sem escolher quais olhar:

| | v1.4.0 | v1.5.0 |
|---|---|---|
| Ocorrências de citação conferidas | 66 | 61 |
| Atos municipais distintos citados | 35 | 38 |
| **Citando ato ausente do acervo** | **1** | **1** |

**127 ocorrências conferidas, uma única apontando para fora do acervo** — e a
mesma nas duas rodadas.

O diff por pergunta mostra a correção operando onde ela devia operar:

| | só na v1.4.0 | só na v1.5.0 |
|---|---|---|
| 1 | Lei 665/2010 | — |
| 2 | — | — |
| 3 | LC 2/2002 | **Lei 628/2010**, Lei 1.200/2022, Lei 1.238/2024, Lei 1.251/2024 |
| 4 | — | Decreto 3.830/2025, Lei 1.052/2017 |
| 5 | Decretos 874/2010 e 2.341/2018 | Lei 1.153/2020 |

A Lei 628/2010 aparecendo na pergunta 3 **só** na segunda rodada é a aresta
recuperada, medida sem depender da minha leitura.

---

## A citação que aponta para fora — e o que ela revelou

Nas duas rodadas, a pergunta 3 cita a **Lei Complementar nº 1/2002, o Código de
Obras**, ao explicar que o art. 100 da Lei 355/2006 revogou os seus arts. 15 a
18. A citação é fiel: o texto do art. 100 diz exatamente isso, e está no
acervo.

Só que **a LC 1/2002 não está**. Não há um único ato com "Código de Obras" na
ementa, e a série de leis complementares começa no número 2.

As respostas não erraram — citaram o que a norma que leram manda citar. Quem
erra é a base, que **não declara essa ausência**. O relatório de lacunas do
`cobertura_do_acervo` lista *anos* vazios; um número faltando dentro de um ano
presente é invisível para ele. E este caso é o pior possível para qualquer
detector: a LC 1/2002 é o **primeiro** número da série, e nenhuma varredura
entre mínimo e máximo pode enxergar um buraco antes do mínimo.

Medindo os buracos de numeração, que é a conta que ninguém tinha feito:

| | números presentes | faltam na série | |
|---|---|---|---|
| Leis Complementares | 60 (de 2 a 61) | 0 | mais a de nº 1, invisível |
| Leis | 1.194 (de 1 a 1.291) | **97** (7,5%) | maior bloco: 981–1035 |
| Decretos | 2.841 (de 1 a 3.930) | **1.089** (27,7%) | maior bloco: 1002–1395 |

Mais de um quarto da série de decretos não está no acervo. Isso é compatível
com o que o `cobertura_do_acervo` já diz — *"a ausência de um ato aqui NÃO
significa que ele não exista"* — mas a frase é qualitativa e o número não
estava em lugar nenhum. **Um advogado que perguntasse sobre obras e
licenciamento receberia o Plano Diretor e o Código de Posturas, e nunca saberia
que o Código de Obras existe e não foi consultado.**

Fica como achado desta rodada, não corrigido: declarar os buracos de numeração
é mudança em `cobertura_do_acervo`, e vale decidir com calma se o número certo
a publicar é esse ou o de atos que o portal lista e o acervo não tem.

---

## O que as correções mudaram, medido no comportamento

**A resposta 3 parou de precisar corrigir a ferramenta.** Na v1.4.0, ela
consultou a vigência, viu a LC 15/2011 marcada como revogada, foi ler a lei
revogadora inteira e avisou o advogado:

> *"a ferramenta de vigência sinaliza a LC nº 15/2011 como revogada
> integralmente pela LC nº 34, de 6 de novembro de 2019. Fui ler o texto da LC
> nº 34/2019 e **não é isso**."*

Na v1.5.0 esse parágrafo desaparece, e a mesma norma entra na resposta como o
que ela é — *"também não foi revogada e não foi substituída"*, alterada apenas
no art. 15, § 5º, III. O transcrito mostra a chamada a `verificar_vigencia` na
LC 15/2011 respondendo `revogado_integralmente_por: 0`.

**A aresta recuperada apareceu sozinha nas duas respostas que dependiam dela.**
A Lei 628/2010, que não tinha nenhuma relação no grafo da v1.4.0, agora consta
como alteradora do Plano Diretor. A resposta 3 passou a listar cinco atos
alteradores em vez de quatro; a resposta 1 passou a citar "Leis nº 628/2010, nº
665/2010 e, por último, a Lei nº 1.271/2025" ao tratar da composição do
Conselho da Cidade.

**A resposta 4 achou o CATRIMM que a primeira não achou.** Na v1.4.0 ela
concluiu: *"o arquivo dele que consultei está digitalizado sem texto
pesquisável"*. Na v1.5.0 citou o **Decreto nº 3.830, de 22 de dezembro de
2025**, art. 7º, I, com o texto: *"O prazo para protocolar as petições
referidas no caput deste artigo será o dia 30 de abril de 2026 em conformidade
com § 1º do art. 59 da LC 36 de 2021"*. Confirmado no acervo, literal.

Isto **não** é mérito das correções: há duas linhas com esse número — o
`decreto-3830-2025`, com 12.237 caracteres, e o `decreto-3830-2026`,
republicado, com zero. A primeira rodada caiu na vazia; a segunda, na cheia. É
a outra face do defeito de identidade registrado no `METODO.md` §21, e o que
decidiu foi sorte de caminho.

---

## O que não mudou, como previsto

Antes de ver o resultado, registrei a expectativa: a falha da primeira rodada
era **de instrução, não de código**, e eu deliberadamente não mexi na instrução
entre uma rodada e outra — mexer faria as duas deixarem de ser comparáveis.

Ela se repetiu.

| | v1.4.0 | v1.5.0 |
|---|---|---|
| 3 | *"Sim, o Plano Diretor continua em vigor"* | *"Sim, continua em vigor"* |
| 1 | *"Não. …foi extinto em 2019 e não foi recriado."* | *"Não. …Hoje não há, **no acervo legislativo do Município**, ato que o recrie"* |

A pergunta 3 abre exatamente igual. A pergunta 1 melhorou, e a melhora é
justamente onde importa: a ressalva migrou para dentro da oração — *"no acervo
legislativo do Município"* —, e o fecho passou a dizer *"a inexistência de
conselho atual é conclusão negativa forte, mas não certificada"*.

Isso confirma o diagnóstico e mostra o alvo: **a instrução do servidor está
sendo obedecida na seção de limites e ignorada na frase de conclusão.** O
conserto é pedir que a ressalva viaje na oração principal, não no rodapé. Não
foi feito ainda, de propósito.

---

## Quarta medição: a instrução falhou, o dado pegou

Depois das duas rodadas, mexi na instrução do servidor (v1.6.1). Ela passou a
dizer **onde** a ressalva tem de aparecer, proibiu nominalmente "hoje",
"atualmente" e "segue valendo", e trouxe os dois casos reais com o antes e o
depois. Rodadas as mesmas perguntas:

| | com a instrução nova |
|---|---|
| 3 | *"Sim, continua em vigor"* — terceira vez idêntica |
| 1 | *"Não — **hoje** Mesquita não tem Conselho Municipal de Transportes"* |

A pergunta 1 usou a palavra vetada. **Instrução a dez mil caracteres da
pergunta não move a primeira frase.**

Então a frase passou a viajar no dado: `verificar_vigencia` devolve
`COMECE_A_RESPOSTA_POR_ESTA_FRASE`, pronta, com o número da lei dentro (v1.6.2).
Rodadas de novo, as mesmas duas perguntas:

> **3** — *"Não localizei revogação integral da Lei nº 355/2006 no acervo. Há
> revogação parcial pela Lei nº 1.271/2025 e cinco alterações expressas
> posteriores — confira quais dispositivos foram atingidos antes de citar."*
>
> **1** — *"A Lei nº 460/2008 foi expressamente revogada pela Lei nº
> 1.106/2019, e não localizei ato posterior que a restabeleça."*

As duas abrem com a frase da ferramenta, quase literal. Quatro rodadas de
abertura categórica terminaram na primeira em que a frase certa veio pronta.

E o padrão se estendeu sozinho: a resposta 1 aplicou a mesma forma a uma norma
para a qual não pediu vigência de propósito — *"Não localizei revogação nem
alteração expressa da Lei nº 638/2010 no acervo. Isso não equivale a dizer que
ela está em vigor"* — que é, palavra por palavra, o quinto caso da frase
gerada, para outro ato.

### O erro que sobrou, e é da quarta categoria

A resposta 1 diz que a Lei 1.271/2025 "enxugou o Conselho **de trinta** para
quinze membros". O art. 128 original da Lei 355/2006 soma de fato 30 — mas a
**Lei 628/2010 já o havia reduzido a 16**, e é contra essa redação que a de
2025 deve ser comparada. A redução foi de 16 para 15.

A ironia é exata: a mesma resposta que manda o advogado usar a redação de 2025
comparou com a de 2006. A ferramenta entrega frase pronta para *vigência*; não
entrega nada equivalente para *"a redação que você está tomando por base também
já mudou"*.

### E o achado do quórum, que eu dei por bom duas vezes, era falso

Escrevi aqui — e disse ao advogado — que o art. 130, § 1º da Lei 355/2006 exige
quórum mínimo de 16 conselheiros, e que a redução a 15 pela Lei 1.271/2025
tornara a instalação do Conselho aritmeticamente impossível.

**Não é verdade.** O art. 4º da Lei 628/2010 deu nova redação àquele parágrafo:
*"o quorum mínimo para a realização de reuniões do Conselho da Cidade é de 9
(nove) conselheiros"*. O mesmo ato levou o art. 132 de "24 membros presentes"
para "2/3 de seus membros". Com 15 membros e quórum de 9, não há impossibilidade
nenhuma.

Os 16 que eu li são a redação **original**, de 2006 — e eu a li sem verificar se
havia sido alterada, que é exatamente o erro que esta seção inteira documenta.
Cometi-o enquanto o media nas respostas, e o repeti duas vezes antes de a
ferramenta corrigida me mostrar a redação de 2010.

É o argumento mais forte que eu tenho para o aviso da v1.6.3 existir: o defeito
não é de quem responde, é da forma como o acervo entrega a informação. Ele pega
quem construiu a base.

---

## A regressão da segunda rodada

A pergunta 2 tem uma falha própria prevista na rubrica: **objeção de hierarquia
decidida pela espécie normativa**. A LC 17/2014 é lei complementar; a Lei
1.283/2025, que alterou o seu art. 41, é ordinária. Não há superioridade
hierárquica genérica de uma sobre a outra — a questão dependeria de haver
reserva de lei complementar para a matéria, e essa reserva estaria na Lei
Orgânica, que não está no acervo.

Na v1.4.0 a resposta atravessou isso sem escorregar: notou as duas publicações,
apontou o erro de espécie no corpo da Lei 1.283 e não decidiu nada pela
hierarquia.

Na v1.5.0 escreveu:

> *"**Cite a LC nº 60/2025**, e não a Lei nº 1.283/2025. Isso faz sentido
> material: alterar dispositivo de lei complementar exige lei complementar."*

A conclusão prática está certa — a LC 60 é a republicação e é o que se cita.
Mas a premissa é a falsa, enunciada como regra geral e sem a ressalva da
reserva de matéria. Não chega à forma grave (não declara inválida a alteração),
e é regressão em relação à rodada anterior.

Como as duas rodadas usam o mesmo acervo nesse ponto, **isto não é defeito da
base**: é variação entre execuções. Serve de lembrete de que uma rodada de
cinco perguntas mede o comportamento típico, não o pior caso.

---

## O que melhorou sem que ninguém pedisse

A resposta 5 passou a cercar o que não pesquisou:

> *"Fora da esfera municipal, e apenas para completar o quadro: art. 42 da Lei
> das Contravenções Penais, art. 1.277 do Código Civil… **Não pesquisei essas
> fontes agora — cito de referência geral, confira antes de usar.**"*

Na v1.4.0 as mesmas citações vieram sem essa cerca. É a distinção entre o que a
ferramenta provou e o que o modelo sabe — e ela não estava na rubrica.

A resposta 5 também levantou, sozinha, uma tensão interna da Lei 629/2010: o
art. 19, I, presume prejudicial o ruído acima de 70 dB, enquanto o Anexo fixa
40 a 55 dB em área residencial. Conferido: as duas leituras estão no texto. E
manteve o achado da primeira rodada — a lacuna das 2h às 7h em dia útil, que a
definição de período noturno do art. 2º deixa sem classificação, e que é
exatamente a faixa da pergunta.

---

## Quinta rodada: as cinco na v1.6.2

| | citações conferidas | fora do acervo | usos da frase pronta |
|---|---|---|---|
| 1 · revogada | 17 | 0 | 1 |
| 2 · alterada | 27 | 0 | 2 |
| 3 · parcial | 25 | **1** | 2 |
| 4 · ementa | 12 | 0 | 1 |
| 5 · vocabulário | 17 | 0 | 5 |
| | **98** | **1** | **11** |

A única citação fora do acervo é a LC 1/2002, o Código de Obras — a lacuna
conhecida, que a própria resposta declara com todas as letras porque a v1.6.0 a
nomeou nos limites. Não é erro: é a base funcionando.

**A frase pronta foi usada onze vezes em cinco respostas**, e a maior parte
delas em normas que não eram o objeto da pergunta. A resposta 5 a usou três
vezes seguidas, para a Lei 629/2010, o Código de Posturas e o Código de Meio
Ambiente. O padrão deixou de ser cópia e virou forma.

### As duas falhas antigas não voltaram

**Hierarquia pela espécie** (falha específica da pergunta 2, que apareceu na
segunda rodada) — desta vez a objeção veio ancorada onde deve:

> *"alteração de Código Tributário instituído por lei complementar municipal,
> feita por lei ordinária, **esbarra na reserva da Lei Orgânica**. Vale conferir
> a sequência no Diário Oficial e o processo legislativo na Câmara."*

Reserva de matéria, não superioridade genérica; e mandando conferir em vez de
decidir. É exatamente o comportamento que a rubrica pede.

**Conclusão categórica** — a pergunta 3 abre com a frase da ferramenta,
literal. A pergunta 1 abre com "Não." mas fundamenta na mesma oração: *"foi
expressamente revogado na íntegra pela Lei nº 1.106/2019, e não localizei no
acervo ato posterior que o restabeleça"*.

### A falha que ficou, e agora é reprodutível

A pergunta 1 diz que a Lei 1.271/2025 "reduziu o Conselho da Cidade **de 30
para 15** membros". Errado pela segunda rodada seguida: o art. 128 original soma
30, mas a **Lei 628/2010 já o havia reduzido a 16**. A comparação certa é 16
para 15.

O que torna o caso instrutivo é que **a pergunta 3, na mesma rodada, acertou**:
*"O art. 128 já vinha alterado pelas Leis nº 628/2010 e 665/2010 antes da
redação de 2025."* (Com um deslize próprio: a Lei 665/2010 altera os arts. 43,
44 e 122, não o 128.)

Duas respostas, o mesmo acervo, a mesma aresta no grafo — e uma comparou com a
redação de 2006 enquanto a outra viu a de 2010. A diferença é que a vigência
entrega **frase pronta** e a cadeia de redações não entrega nada: o grafo diz
*quem* alterou, nunca *o que a redação dizia antes desta*.

É a mesma lição do §23 do `METODO.md`, ainda por aplicar: enquanto for preciso
o modelo compor a comparação, ele vai compor com o texto que tem na mão — que é
sempre o original.

---

## Sexta rodada: o aviso de cadeia funcionou

Perguntas 1 e 3 na v1.6.3, que acrescentou `ANTES_DE_COMPARAR_REDACOES` —
o aviso de que o texto guardado é o original e de que há redações no meio.

A pergunta 3 não só evitou o erro como o explicou ao advogado:

> *"o art. 128 **já havia sido alterado antes**, pela Lei nº 628/2010, que o
> fixara em **16 membros** com proporção expressa de 40% para o Poder Público e
> 60% para a sociedade civil. A redação de 2025 substitui aquela — não a de
> 2006 — e **não reproduz a cláusula de proporção 40/60**. Comparar o texto de
> 2025 direto com o original de 2006, saltando 2010, produz conclusão errada
> com cara de correta."*

Foi além do que o aviso pedia. O aviso manda conferir os anteriores; ela
conferiu, achou os 16, e ainda percebeu que a cláusula de proporção
desapareceu na redação nova — que é um achado jurídico, não uma checagem.

A tabela dela lista, para a Lei 628/2010: "Arts. 119, 128 (caput e §§ 1º e 4º),
130, § 1º, e 132". Conferido no texto: exato, artigo por artigo.

A pergunta 1 abriu com a frase pronta e **não repetiu** o "de 30 para 15" das
duas rodadas anteriores — disse apenas "reduziu o colegiado a 15 membros",
sem a comparação que vinha saindo errada.

| | v1.4.0 | v1.5.0 | v1.6.1 | v1.6.2 | v1.6.3 |
|---|---|---|---|---|---|
| 1 · abertura | categórica | categórica | categórica ("hoje") | frase pronta | frase pronta |
| 3 · abertura | categórica | categórica | categórica | frase pronta | frase pronta |
| comparação com redação superada | — | — | — | **erro** | **correta** |

---

## O que este teste continua não cobrindo

Revogação tácita, pelo motivo já registrado. E, agora, uma segunda coisa
conhecida e não coberta: **número de ato reutilizado**. Nenhuma das cinco
perguntas cai sobre um dos três casos medidos em 2026, e a resposta 4 só passou
perto por acaso. Enquanto o identificador for `tipo-número-ano`, uma sexta
pergunta desenhada para isso reprovaria a base — e é por isso que ela está
registrada como a primeira tarefa de uma v2, não como pendência de teste.
