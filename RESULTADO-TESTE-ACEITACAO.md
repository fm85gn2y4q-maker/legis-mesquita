# Resultado do teste de aceitação — v1.4.0, 22/08/2026

Cinco perguntas, cinco conversas limpas, sem palavra-chave e sem intervenção.
Cada respondente recebeu **só a pergunta**, nenhuma informação sobre o projeto,
e foi proibido de ler o disco — o repositório com o gabarito estava debaixo
dele. A proibição foi verificada no transcrito: **nenhuma chamada a Bash, Read,
Grep ou Glob nos cinco**.

Portão de versão conferido antes de começar: 4.143 atos · 4.085 com texto ·
10.531 páginas · 84 revogações integrais · 16 parciais.

> **Ressalva de método.** Este é o servidor publicado sob um cliente que não é o
> Claude Desktop nem o ChatGPT. Prova o acervo e o comportamento do modelo; não
> prova os dois clientes. A repetição neles fica pendente, e divergência entre
> eles seria, ela própria, um achado.

---

## Veredito

**Aprovado, com uma ressalva de forma e três defeitos de dados encontrados.**

| | 1 · revogada | 2 · alterada | 3 · parcial | 4 · ementa | 5 · vocabulário |
|---|---|---|---|---|---|
| Chamou `verificar_vigencia` | 4× | 2× | 2× | 1× | 3× |
| Distinguiu integral de parcial | sim | n/a | **sim** | n/a | sim |
| Percebeu redação superada | sim | **sim** | sim | sim | n/a |
| Saiu da ementa para o corpo | sim | sim | sim | **sim** | sim |
| Reformulou a consulta | sim | sim | sim | sim | **sim** |
| Transcreveu dispositivo | sim | sim | sim | sim | sim |
| Declarou os limites | sim | sim | sim | sim | sim |
| Ficou em "não localizei" | **não** | quase | **não** | sim | sim |
| Hierarquia decidida pela espécie | não | **não** | não | não | não |
| Citação inventada | **não** | **não** | **não** | **não** | **não** |

Chamadas: 25, 20, 18, 19 e 27. Todos abriram por `cobertura_do_acervo`.

**Nenhuma citação inventada.** Conferi todas contra o acervo — número, ano,
data e texto do dispositivo. As transcrições batem palavra por palavra, e as
duas que eu tomei por invenção existem: a Lei 628/2010 é real (era o meu grafo
que não a tinha), e o art. 59 da LC 36/2021 diz exatamente o que a resposta 4
transcreveu.

---

## O que falhou: a conclusão categórica

Duas das cinco escorregaram de "não localizei" para uma afirmação sobre o mundo
— e escorregaram **na primeira frase**, que é a que o advogado lê:

| | abertura | rodapé |
|---|---|---|
| 1 | *"Não. …foi extinto em 2019 e não foi recriado."* | *"Antes de afirmar em peça que o conselho não existe, vale conferir a Lei Orgânica e pedir certidão."* |
| 3 | *"Sim, o Plano Diretor continua em vigor"* | *"Não há, na base, nenhum ato que a tenha revogado integralmente."* |

Note o padrão, que é mais interessante que a falha: **as duas sabem a régua e a
aplicam — no lugar errado.** A instrução do servidor está sendo obedecida na
seção de limites e ignorada na frase de conclusão. Quem lê a resposta inteira
não se engana; quem lê a primeira linha e cita, sim.

Isso é conserto de **instrução, não de código**: a ressalva tem de viajar na
conclusão, não no rodapé. O `METODO.md` já registra que declarar o limite no
mesmo lugar em que se responde é o que funciona — falta dizer que "o mesmo
lugar" é a oração principal.

A pergunta 2 chegou perto (abre com "**3%**", sem qualificar) mas se salva: o
corpo diz de onde vem a redação e o que ainda é preciso conferir.

---

## O que passou melhor do que o gabarito

**Pergunta 4.** O gabarito mandava chegar ao art. 39 da LC 17/2014 e ao
dispositivo dos 30 dias, e observar se caía na armadilha da LC 3/2003 — o
Código Tributário anterior, revogado, que também fala em 30 dias. A resposta não
caiu na armadilha, e passou por cima do gabarito: foi à **LC 36/2021, art. 59**,
o Código de Defesa do Contribuinte, que é a norma especial e posterior, com a
exceção do § 1º (carnê anual de IPTU: até 30 de abril). Depois voltou ao art.
328 do Código Tributário como cautela, notando que a LC 36/2021 é posterior e
específica.

Conferi: está certa. **O gabarito é que estava impreciso** — o art. 39 trata da
impugnação da base de cálculo do ITBI, e os "30 dias para pagamento ou
impugnação" que eu tinha em mente são o art. 169, § 1º, sobre taxa de vistoria
de veículos. Corrigido no `TESTE_ACEITACAO.md`.

**Pergunta 2.** Resolveu sozinha o problema que a pergunta plantou: a mesma
norma foi publicada duas vezes, como Lei 1.283/2025 (DOM 02349, de 15/12) e
como Lei Complementar 60/2025 republicada (DOM 02355, de 23/12), e o corpo da
primeira diz "Esta *Lei Complementar* entra em vigor" — denunciando o erro de
espécie. Levantou a questão da anterioridade sem decidir nada pela hierarquia
das espécies, que era a falha específica desta pergunta.

**Pergunta 5.** Traduziu a fala do leigo para o vocabulário do legislador
**antes** de buscar: a primeira consulta já foi "poluição sonora", e a Lei
629/2010 veio como único resultado. Os três atos laterais que o gabarito
previa — dois decretos de desapropriação e uma lei de crédito adicional, que
casam por "faz" e "alto" — nunca chegaram a aparecer.

---

## Três defeitos de dados, encontrados pelo teste

### 1. Norma viva declarada morta — 3 arestas em 84

O extrator lê a cláusula de estilo no **plural** ("revogam-se as disposições em
contrário") e exige um conector de ressalva antes de aceitar a revogação. Não lê
o **singular**, e não trata "revoga dispositivos da Lei X".

| Ato | marca como morta | o que o texto diz |
|---|---|---|
| LC 34/2019 | **LC 15/2011** — Uso, Ocupação e Parcelamento do Solo | *"revogando o disposto em contrário **na** Lei Complementar 15/2011"* |
| Lei 1.125/2019 | **Lei 224/2005** — Quadro Permanente de Pessoal | *"revoga o disposto em contrário **na** Lei nº 224"* |
| Lei 1.246/2024 | **Lei 1.206/2022** — Sistema de Licenciamento Ambiental | *"Altera, acrescenta e revoga **dispositivos** da Lei Municipal nº 1.206"* |

As três estão vivas. As três são normas de consulta corrente. É o pior defeito
possível nesta base — o inverso exato do que ela existe para evitar — e nenhum
dos 107 testes automatizados o pegaria, porque todos medem forma, não domínio.

Encontrado pela resposta 3, que **desconfiou da ferramenta**: leu a LC 34/2019
inteira, viu que ela só altera o art. 15, § 5º, III, e avisou o advogado de que
a sinalização de revogação estava errada. É o comportamento que a rubrica não
pediu porque eu não imaginei que fosse possível pedir.

### 2. Arestas que faltam — 17

`n.º` (com ponto **antes** do `º`) desmontava o casamento: a limpeza de
abreviações transforma "n.º 355" em "n º 355", e o padrão do alvo não tolerava o
espaço entre o `n` e o ordinal. Resultado: a Lei 628/2010 — cuja ementa é
*"Altera dispositivos da Lei Municipal n.º 355 de 25 de outubro de 2006"* — não
tinha **nenhuma** aresta.

Medido no acervo inteiro: **17 arestas ganhas**, entre elas cinco `regulamenta`
e a alteração do Plano Diretor pela Lei 628/2010.

É a terceira vez neste projeto que um detalhe de pontuação apaga milhares de
caracteres ou dezenas de relações sem produzir um único erro — depois do `*` no
separador de milhar e do `n.º` no cabeçalho. A família é sempre a mesma: **a
diagramação do PDF varia mais do que a regex supõe, e a falha é silenciosa por
construção.**

### 3. A ementa genérica sequestra a classificação

Corrigido o item 2, "Altera dispositivos da Lei nº 355" (ementa, genérica,
classificada `total`) passa a casar **antes** de "altera o caput do art. 43 da
Lei nº 355" (art. 1º, específica, `parcial`) — e a deduplicação guarda só a
primeira. Duas arestas pioram de `parcial` para `total`.

Para `altera` isso quase não importa. Para `revoga` importa inteiro, e é o mesmo
mecanismo. A correção do item 2 **não deve ir sozinha**.

---

## O que este teste não cobriu, de novo

Revogação tácita continua fora, pelo motivo já registrado: cobrar o que a
ferramenta declaradamente não faz mede a honestidade de quem escreve a pergunta,
não o comportamento dela.

Observação de graça, que o documento pedia: **os cinco mencionaram
espontaneamente** que a ausência de revogação expressa não prova vigência, que o
texto guardado é o original e que a base não tem a Lei Orgânica. A instrução do
servidor funciona. O que ela não garante é *onde* a ressalva aparece — e é disso
que trata a primeira seção.
