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

## O que este teste continua não cobrindo

Revogação tácita, pelo motivo já registrado. E, agora, uma segunda coisa
conhecida e não coberta: **número de ato reutilizado**. Nenhuma das cinco
perguntas cai sobre um dos três casos medidos em 2026, e a resposta 4 só passou
perto por acaso. Enquanto o identificador for `tipo-número-ano`, uma sexta
pergunta desenhada para isso reprovaria a base — e é por isso que ela está
registrada como a primeira tarefa de uma v2, não como pendência de teste.
