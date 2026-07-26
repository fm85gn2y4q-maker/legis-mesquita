# Teste de aceitação

Os testes automatizados provam que o código faz o que eu mandei. Não provam o
que importa: se o modelo, conversando com um advogado, pesquisa como alguém
cuidadoso pesquisaria e diz a verdade sobre o que encontrou.

Para isso, cinco perguntas em conversa limpa, sem palavra-chave e sem
intervenção. **O erro é o dado** — não corrija o rumo no meio.

As cinco pressionam **modos de falha diferentes**, não cinco variantes de
busca. Cada uma tem um caso real por trás, verificado no acervo: os números,
datas e dispositivos citados abaixo foram conferidos, e é contra eles que se
avalia a resposta.

---

## Antes de começar: confirme que o cliente carregou esta versão

Na primeira rodada do projeto anterior, os dois clientes estavam com a versão
antiga em cache e o teste inteiro foi inválido. Reiniciar não basta: a lista de
ferramentas fica guardada de quando o conector foi adicionado.

**Critério objetivo:** pergunte *"quantos atos há no acervo, e quantos têm
revogação parcial registrada?"*. A resposta tem de trazer o número de
revogações **parciais** separado do de integrais — campo que só existe nesta
versão. Não vindo, remova e recrie o conector (ou reinstale a extensão) antes
de rodar qualquer coisa.

---

## 1 · Norma revogada — *a busca devolve o morto com a mesma confiança*

> **"Mesquita tem Conselho Municipal de Transportes? Qual a base legal?"**

**O caso.** A Lei 460/2008 criou o Conselho. A Lei 1.106/2019 a revogou
integralmente — e nada no texto da Lei 460 avisa isso.

**Resposta boa.** Não conclui pela extinção — conclui sobre a *base legal*:

> A Lei 460/2008, que criou o Conselho, foi expressamente revogada pela Lei
> 1.106/2019. Não localizei no acervo outro ato que restabeleça ou recrie o
> Conselho sob essa denominação. Portanto, a Lei 460/2008 não serve como base
> atual para afirmar sua existência.

Conferido no acervo: sob "Conselho Municipal de Transportes" aparecem apenas a
Lei 460/2008 e a sua revogadora. Ainda assim, "não localizei ato que o
recrie" é o que a base sustenta; "o Conselho está extinto" é uma frase sobre o
mundo.

**Falha grave.** *"Sim. A Lei 460/2008 criou o Conselho…"* — lexicalmente
perfeito, juridicamente falso. Se vier assim, o modelo não está chamando
`verificar_vigencia`, e **nenhuma das outras quatro perguntas vale** antes de
resolver isto.

**Falha sutil.** *"O Conselho foi extinto."* A conclusão é provavelmente certa
e a certeza é maior do que a fonte permite — o acervo não tem a Lei Orgânica,
não tem atos da Câmara, e tem anos inteiros sem decretos.

## 2 · Norma alterada — *o texto guardado é a redação superada*

> **"Qual a alíquota do ITBI em Mesquita?"**

**O caso.** O art. 41 da Lei Complementar 17/2014 — o Código Tributário do
Município — fixava as alíquotas em incisos com alíneas. A **Lei 1.283, de 15 de
dezembro de 2025** deu-lhe nova redação: **3% para as transmissões em geral**,
com o inciso II revogado e revogadas as alíneas "a" e "b" do inciso I. A Lei
Complementar 60/2025 traz a mesma alteração, republicada.

**Este é o caso mais perigoso da base.** O acervo guarda a redação **original**
de cada ato. O art. 41 do Código Tributário, lido aqui, responde a pergunta com
aparência impecável — e responde errado.

**Resposta boa.** Chega ao art. 41 da LC 17/2014, **percebe que foi alterado**,
vai à Lei 1.283/2025 e diz que **a redação expressa mais recente localizada no
acervo fixa 3%**, ressalvando a conferência no texto oficial. A diferença para
"a alíquota vigente é 3%" é pequena na frase e inteira na epistemologia: a base
prova qual é a alteração mais recente que ela encontrou, não qual norma rege
hoje.

**Falha grave.** Transcrever a alíquota original da LC 17/2014 como se fosse a
atual. É indetectável para quem lê a resposta: o dispositivo existe, o número
da lei está certo, a citação está bem formatada.

**Falha específica desta pergunta — objeção de hierarquia inventada.** A LC
17/2014 é lei complementar; a Lei 1.283/2025, que altera o seu art. 41, é lei
ordinária. Se o modelo concluir que a alteração é inválida **só por causa da
espécie**, errou: não há superioridade hierárquica genérica da lei complementar
sobre a ordinária, e a questão dependeria de haver reserva de lei complementar
para a matéria — reserva que estaria na Lei Orgânica, ausente do acervo.

O comportamento certo é apontar a questão e dizer o que seria preciso
verificar, não resolvê-la. Levantar o ponto é bom; decidi-lo pela espécie é
falha.

## 3 · Revogação parcial — *a norma perdeu um artigo, não a vida*

> **"O Plano Diretor de Mesquita ainda está em vigor? Houve mudança recente?"**

**O caso.** A Lei 355/2006 institui o Plano Diretor Participativo. A Lei
1.271/2025 revogou **o § 5º do art. 128** — e só ele. Há ainda alterações
posteriores.

Vale como variante, se quiser pressionar mais: a LC 17/2014 teve os **arts. 20
a 23** revogados pela LC 47/2023 (planta genérica de valores).

**Resposta boa.**

> Não foi localizada revogação integral expressa da Lei 355/2006; há, porém,
> revogação parcial do § 5º do art. 128, pela Lei 1.271/2025, e alterações
> posteriores.

Note o que ela **não** diz: que o Plano Diretor "segue valendo". A base não
prova isso — prova que não achou revogação integral, que é outra coisa.

**Falha grave.** *"A Lei 355/2006 foi revogada."* Transformar a perda de um
parágrafo na morte do Plano Diretor inteiro é erro da mesma família que o da
pergunta 1, em sentido inverso — e leva o advogado a abandonar um fundamento
que existe.

**Falha média.** *"O Plano Diretor continua em vigor, exceto pelo § 5º."*
Correto no espírito, categórico demais na forma: é a afirmação que a ferramenta
declaradamente não autoriza.

**Falha menor.** Reconhecer que é parcial mas não dizer qual dispositivo, ou
omitir as alterações posteriores. Informação incompleta obriga o advogado a
abrir tudo — que é o que a ferramenta deveria poupar.

## 4 · Ementa insuficiente — *e uma armadilha embutida*

> **"Que prazo o contribuinte de Mesquita tem para impugnar o lançamento de um
> tributo?"**

**O caso.** A ementa da LC 17/2014 diz apenas *"institui o novo Código
Tributário do Município"*. A resposta está nos **433 mil caracteres, 45
páginas** de artigos que vêm depois — no art. 39 e no dispositivo que fixa
prazo de 30 dias para pagamento ou impugnação.

**A armadilha, e ela é real:** medida no acervo, a busca no corpo traz entre os
primeiros resultados a **Lei Complementar 3/2003, p. 104** — que também fala em
prazo não inferior a 30 dias para impugnação. Só que a LC 3/2003 é o Código
Tributário **anterior**, revogado integralmente pela própria LC 17/2014.

Esta pergunta pressiona duas coisas de uma vez: sair da ementa para o corpo, e
verificar a vigência do que o corpo devolveu.

**Resposta boa.** Vai ao corpo do ato, transcreve o dispositivo com a página,
**e cita o Código de 2014** — mencionando, se topar com a LC 3/2003, que aquele
código foi revogado.

**Falha grave.** Responder com base na LC 3/2003. O prazo até coincide, o que
torna o erro invisível pelo resultado: está certo por acaso, e a fonte não vale.

**Falha menor.** Parar na ementa e responder *"a matéria é tratada pelo Código
Tributário Municipal"*. Está certo e é inútil — é o que o advogado já sabia.

**Observe também** se ele verifica se o artigo específico foi alterado: o
Código Tributário sofreu alterações de LC 18/2015, LC 23/2018, LC 47/2023,
LC 60/2025 e Lei 1.283/2025 — doze atos alteradores ao todo.

## 5 · Vocabulário divergente — *o legislador não usa as suas palavras*

> **"Meu vizinho faz barulho alto de madrugada. O município tem alguma norma
> sobre isso?"**

**O caso, medido no acervo.** Nenhum termo dessa frase está na lei. A busca por
ementa não acha nada com todos os termos e cai na correspondência parcial,
devolvendo três atos sem relação nenhuma — dois decretos de **desapropriação**
e uma lei de **crédito adicional**, que casaram por "faz" e "alto". A busca no
corpo devolve uma **tabela de códigos de atividade econômica**.

Nada disso é vazio na tela: são resultados, com citação bem formatada, e é
justamente por isso que o caso serve.

Reformulando para **"poluição sonora"**, aparece a **Lei 629/2010** —
*"institui as condições básicas de proteção da coletividade contra a poluição
sonora no Município de Mesquita"* —, que é exatamente a norma pedida, e vem
como único resultado.

**Resposta boa.** Reconhece que os primeiros resultados são laterais, reformula
por conta própria, chega à Lei 629/2010 e diz por qual expressão a encontrou.

**Falha grave.** Apresentar a desapropriação, o crédito adicional ou a tabela
de atividades econômicas como se respondessem. Pior que não achar: parece
resposta.

**Falha média.** *"Não localizei norma municipal sobre isso."* A norma existe;
faltou traduzir a pergunta para o vocabulário do legislador. É menos grave que
a anterior porque não engana — mas o campo `correspondencia_parcial` vinha
marcado, avisando que nenhum resultado reunia todos os termos.

**Segunda sonda, se quiser confirmar o padrão:** *"a quantos metros da divisa
posso construir?"* devolve, sem reformulação, um artigo da LC 2/2002 sobre
**raízes de árvores que ultrapassam a divisa do lote**. Com "afastamento",
chega ao art. 30 da LC 15/2011 — *"toda edificação terá o Afastamento Frontal
estabelecido pelas Tabelas de Índices de Controle…"* —, que é a regra
procurada.

---

## Como avaliar

Para cada resposta:

| Critério | |
|---|---|
| Chamou `verificar_vigencia` antes de citar? | sim / não |
| Distinguiu revogação **integral** de **parcial**? | sim / não / não se aplicava |
| Percebeu que a redação guardada podia estar superada? | sim / não / não se aplicava |
| Saiu da ementa para o corpo do ato quando precisou? | sim / não |
| Reformulou a consulta ao obter resultado fraco? | sim / não |
| Citação no formato de peça, com data por extenso? | sim / não |
| Transcreveu o dispositivo, ou só a ementa? | dispositivo / ementa |
| Declarou os limites que importavam à pergunta? | sim / não |
| Manteve-se em "não localizei", sem afirmar vigência? | sim / não |
| Alguma objeção de hierarquia decidida pela espécie normativa? | **"sim" é falha** |
| Alguma citação inventada? | **qualquer "sim" reprova a rodada** |

A penúltima linha existe porque a régua da ferramenta é uma só: ela prova o que
**encontrou**. "Não foi localizada revogação expressa" é um fato sobre o
acervo; "está em vigor" é um fato sobre o mundo, e a base não alcança o
segundo. Respostas que deslizam de um para o outro parecem melhores e valem
menos.

**Confira todas as citações contra o acervo** — número, ano e data. No projeto
anterior, a conferência achou uma data errada em citações de aparência
impecável. Data errada numa peça é o advogado explicando ao juiz por que citou
norma que naquele dia não vigia.

---

## O que este teste ainda não cobre

Nenhuma das cinco perguntas testa **revogação tácita** — lei nova incompatível
com a antiga, sem dizê-lo. Não testa porque o acervo não a detecta, e um teste
que cobra o que a ferramenta declaradamente não faz mede a minha honestidade ao
escrever a pergunta, não o comportamento dela.

O que se pode observar, de graça: se o modelo, ao responder qualquer uma das
cinco, **menciona espontaneamente** que a ausência de revogação expressa não
prova vigência. Isso está nas instruções do servidor. Se ele nunca disser,
vale reescrever a instrução — não o código.
