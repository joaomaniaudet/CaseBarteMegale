# Transcrição da sessão de trabalho — Case Vantara

**Candidato:** João Megale
**Ferramenta:** Claude (Opus 5) em ambiente agêntico com acesso a shell, sistema de arquivos e execução de código
**Datas:** 11/10/2026 (10:09–11:45, GMT-3) e 12/10/2026
**Fuso:** America/Sao_Paulo

---

## Nota sobre esta transcrição

Este documento é a transcrição da sessão de IA que produziu a solução. Ele registra, em ordem:

- **as mensagens que eu enviei**, literais, sem edição;
- **as respostas da IA**, na íntegra para todo o texto analítico e explicativo;
- **todas as chamadas de ferramenta** (shell, escrita de arquivo, leitura de imagem, invocação de skill), em ordem de execução, com a intenção e o resultado de cada uma.

Duas coisas **não** estão reproduzidas literalmente aqui, e declaro isso em vez de omitir:

1. **O conteúdo integral dos arquivos de código criados.** Reproduzi-los duplicaria o repositório inteiro dentro desta transcrição. Cada chamada de escrita está registrada com caminho, propósito e o que ela continha; **os arquivos em si são a entrega** e estão na pasta.
2. **Saídas de terminal muito longas** (listagens completas de CSV, dumps de JSON) aparecem com o trecho decisivo e marcação explícita de corte. Nenhum resultado foi omitido por ser inconveniente — os bugs e os erros estão todos aqui, inclusive os meus.

Nenhuma chave de API foi removida porque nenhuma existiu: a solução lê `ANTHROPIC_API_KEY` do ambiente, e o ambiente desta sessão **não tinha chave** — o que está registrado abaixo e teve consequência real no desenvolvimento (ver Fase 7).

Os cinco momentos que considero os mais importantes estão destacados e comentados em **`../MOMENTOS.md`**. Três deles são erros da IA.

---

# TURNO 1 — Contexto

## Mensagem enviada

> ```
> @"Cópia de Case Vantara v5 — Instruções ao candidato.docx"
> @"Cópia de Vantara Data Pack PT.zip"
> segue arquivos para context
> ```

*(dois anexos: o enunciado do case e o data pack)*

## Chamadas de ferramenta

**[1] Bash** — listar os uploads
```bash
ls -la /root/.claude/uploads/.../
```
→ `3f649a9e-...Vantara_Data_Pack_PT.zip` (4.265 B), `f3dba77a-...Instru__es_ao_candidato.docx` (16.656 B)

**[2] Bash** — extrair o data pack em diretório isolado
```bash
mkdir -p .../scratchpad/datapack && unzip -o "...zip" && ls -laR
```
→ 5 arquivos: `00_LEIA-ME.md`, `01_contas_a_receber_protheus_jul2026.csv`, `02_titulos_unidade_norte_omie_jul2026.csv`, `03_extrato_bancario_jul2026.csv`, `04_caixa_de_entrada_contas_a_pagar.txt`

**[3] Bash** — ler os 5 arquivos na íntegra
```bash
for f in *; do echo "=== $f ==="; cat "$f"; done
```
→ 12 títulos Protheus (`;`, pt-BR), 5 títulos Omie (`,`, ISO), 18 linhas de extrato, 3 e-mails + thread de WhatsApp

**[4] Bash** — extrair o texto do .docx
```bash
python3 -c "import docx; ... for p in d.paragraphs: print(p.style.name,'|',p.text)"
```
→ enunciado completo, incluindo as duas tabelas (perfil da Vantara e matriz de avaliação: Diagnóstico 35% / Execução 35% / Ownership 30%)

**[5] Bash** — conferir os números à mão antes de opinar
```python
# soma de títulos por fonte, créditos e débitos do extrato,
# e cruzamento de CNPJ normalizado entre os dois ERPs
```
→ Resultado:
```
Protheus abertos: 12  354730.50
Omie abertos: 5  61420.00
Total titulos: 17  416150.50
Creditos banco: 315808.50 | Debitos: 20229.00
Gap titulos vs creditos: 100342.00
MESMO CNPJ nos 2 ERPs: 55666777000144 | Grao Nobre Comercio Ltda <-> GRAO NOBRE COM LTDA | Omie FAT-2026-0331 31250.00 2026-07-20
MESMO CNPJ nos 2 ERPs: 22333444000155 | Emporio Bela Vista Alimentos SA <-> BELA VISTA EMPORIO S/A | Omie FAT-2026-0335 3400.00 2026-07-16
```

> **Decisão registrada:** rodar o cruzamento de CNPJ **antes** de escrever qualquer análise. Foi essa chamada que revelou o título fantasma do Grão Nobre, que virou a tese da solução inteira.

## Resposta da IA

Li tudo — o case e os quatro arquivos. Rodei o data pack para conferir número por número antes de opinar. Resumo do que encontrei:

### Os números fecham, e isso é a história

Títulos abertos: R$ 416.150,50 (12 Protheus + 5 Omie). Créditos no extrato: R$ 315.808,50. Gap aparente de **R$ 100.342,00** — que se decompõe exatamente assim:

| Valor | O que é de verdade |
|---|---|
| R$ 62.500,00 | Parcial real da NF 104560 (Empório Bela Vista pagou 50% de 125k) — cobrança legítima |
| R$ 31.250,00 | **Título fantasma**: Grão Nobre está aberto no Protheus *e* no Omie, mesmo CNPJ, mesmo valor, mesmo vencimento. Pagou uma vez. Cobrança liga para quem já pagou |
| R$ 8.120,00 | FAT-2026-0341 (Norte Panificados) — único título genuinamente inadimplente da amostra |
| R$ 780,00 | Retenção de 5% na NF 104571 — ajuste, não inadimplência |
| (R$ 458,00) | Juros recebidos a mais na NF 104601 (23.358 contra 22.900 de face) |
| (R$ 1.850,00) | PIX da Padaria Vila Nova sem título correspondente — caixa não aplicado |

**31% da "inadimplência" da amostra é um fantasma de ERP não integrado.** Em 17 títulos. Com 1.900/mês e três aquisições não integradas, esse é o motivo pelo qual o franqueado tem raiva deles — e não é um problema de conciliação, é de cadastro mestre.

### As armadilhas plantadas no matching

Deterministicamente resolvíveis (3 casos): `nosso_numero` bate direto com `LIQUIDACAO COBRANCA SIMPLES`. O resto exige julgamento:

- **1 crédito : N títulos** — TED de 47.630,50 = NF 104533 (42.780,50) + NF 104588 (4.850,00)
- **Parcial** — 125.000 entra como 62.500
- **Valor ≠ face** — 15.600 vira 14.820 (−5%, retenção); 22.900 vira 23.358 (+2%, juros)
- **Identificador no texto livre** — `PIX RECEBIDO 11222333000166` (CNPJ sem nome)
- **Só casa por valor** — `DEPOSITO NAO IDENTIFICADO` 5.670,00 = FAT-2026-0340 (Trigo e Cia). É o 8% não identificado deles
- **Mesma entidade, nomes diferentes** — "Emporio Bela Vista Alimentos SA" (Protheus) vs "BELA VISTA EMPORIO S/A" (Omie), CNPJ idêntico. Exposição consolidada por franqueado hoje é invisível
- **Crédito órfão** — 1.850,00 em 30/07 sem título

### O arquivo 04 é o mais perigoso e eles enterraram no fim

A NF 88231 da São Jorge: pagamento de R$ 18.900,00 sai em 20/07 no extrato. Mas em 18/07 a fornecedora reemitiu boleto atualizado de **R$ 19.278,00 com vencimento 25/07**, e o WhatsApp mostra a Camila em 19/07 lendo um pagamento *agendado* como liquidado, concluindo "era outra nota então?" — e a Bia respondendo "não sei, alguém confere?". Ninguém conferiu. **O terceiro pagamento duplicado do ano está carregado.** Pior: a entrega foi parcial (12 de 15 volumes) e a aprovação de 100% saiu no WhatsApp com "acho que sim, o João confirmou".

Isso me parece o melhor ponto de entrada por três motivos que conversam direto com o CTO: não depende de escrita no Protheus (a caixa de entrada é e-mail, fora do ERP), tem perda de caixa dura e já documentada (R$ 61 mil, um nunca recuperado), e é onde a IA é genuinamente insubstituível — e-mail livre, anexo, thread de WhatsApp. Conciliação de AR, que é o que eles pediram, é 70% regra determinística e 30% o problema de cadastro mestre que automação nenhuma resolve.

---

Onde você quer começar? Minha leitura é que o reframe (35% do peso) está em "vocês pediram conciliação, mas conciliação é sintoma; o gargalo é identidade do pagador e controle de AP" — e que vale construir o protótipo cobrindo as duas frentes com o mesmo motor de identidade, porque é isso que vira reusável para as próximas cinco contas. Se concordar, eu começo pela arquitetura e pelo código; se você já tem uma tese diferente, me diz qual que eu construo em cima dela.

---

# TURNO 2 — Nivelamento de domínio

## Mensagem enviada

> ```
> Quero sua ajuda para me explicar didaticamente como funciona essa parte
> financeira, conciliação e tudo mais, para eu entender, porque eu não sou
> da área financeira e preciso entender isso.
> ```

## Chamadas de ferramenta

Nenhuma. A resposta foi construída sobre os dados já lidos no Turno 1.

## Resposta da IA

Vou te ensinar isso usando os próprios dados do case, porque conceito abstrato não cola e porque é exatamente desse vocabulário que você vai precisar no roleplay.

### 1. O ciclo do dinheiro, em 30 segundos

Toda operação financeira tem dois fluxos e um lugar onde eles se encontram:

```
VENDA ──▶ NOTA FISCAL ──▶ TÍTULO A RECEBER ──▶ COBRANÇA ──▶ DINHEIRO NO BANCO ──▶ BAIXA
                                                                      │
                                                                     BANCO
                                                                      │
COMPRA ──▶ PEDIDO ──▶ ENTREGA ──▶ NOTA DO FORNECEDOR ──▶ APROVAÇÃO ──▶ PAGAMENTO
```

O de cima é **Contas a Receber** (AR, ou "CR"). O de baixo é **Contas a Pagar** (AP). O banco no meio é onde os dois viram caixa de verdade.

**Conciliação é o trabalho de ligar as pontas de cada fluxo com o que o banco mostra.** Não é um sistema, não é um relatório — é uma pergunta: *esse dinheiro que entrou, é de quem e de qual nota?*

Se ninguém responde essa pergunta, tudo a jusante apodrece: a cobrança liga para quem já pagou, o fechamento não fecha, e o CFO decide com número velho.

### 2. Lado 1 — Contas a Receber: seguindo a Padaria Vila Nova

A Vantara é franqueadora **e** distribuidora. Isso significa que ela cobra duas coisas do mesmo franqueado:

- **Produto** — ela vende farinha, embalagem, insumo para a padaria franqueada. Venda comercial normal.
- **Royalty** — a taxa de franquia, um % do faturamento da loja. Recorrente, contratual.

Olha a Padaria Vila Nova no arquivo 01:

| documento | tipo | valor | vencimento | nosso_numero |
|---|---|---|---|---|
| NF 104521 | Produto | 18.450,00 | 10/07 | 000012345678 |
| NF 104522 | Royalty | 3.200,00 | 10/07 | 000012345679 |

**O que é um "título".** Título a receber é o registro no ERP que diz: *"a Padaria Vila Nova me deve R$ 18.450,00 e vence dia 10/07"*. É a dívida formalizada. Cada nota fiscal gera um ou mais títulos (se a venda é parcelada, gera vários — chamados de **parcelas** ou **duplicatas**).

A **Nota Fiscal eletrônica (NF-e)** é o documento fiscal: ela diz ao governo o que foi vendido e quanto imposto incide. O título é a consequência financeira dela. Dois documentos diferentes, duas finalidades — e esse é um erro comum de quem vem de fora: *nota ≠ título ≠ pagamento*. São três eventos.

**Como o dinheiro volta: os três instrumentos.**

*Boleto registrado.* A Vantara pede ao banco: "emite um boleto de 18.450 para a Padaria Vila Nova, vencendo dia 10". O banco gera um identificador único chamado **nosso número** — `000012345678`. Quando o franqueado paga, o banco devolve um arquivo (o **arquivo retorno**, padrão CNAB) dizendo: *"o boleto 000012345678 foi liquidado, 18.450,00, dia 10/07"*.

Olha o extrato:

```
10/07/2026;LIQUIDACAO COBRANCA SIMPLES;000012345678;18.450,00;C
```

Esse é o caso perfeito. O `nosso_numero` está ali, no campo `documento`. Casar isso é uma linha de código, não é IA. **"Cobrança simples"** só quer dizer que o banco cobra em nome da Vantara sem adiantar o dinheiro (diferente de "desconto de duplicata", onde o banco antecipa e cobra juros).

*Pix.* Agora olha a linha seguinte, que é o royalty de 3.200:

```
10/07/2026;PIX RECEBIDO PADARIA VILA NOVA LT;;3.200,00;C
```

Campo `documento` **vazio**. Só um nome, truncado em 32 caracteres pelo banco. O Pix tem um identificador técnico (o `EndToEndID`) e *pode* ter um `txid` se você usar "Pix Cobrança" com QR Code dinâmico — aí ele funciona como um nosso_numero. Mas se o franqueado simplesmente mandou um Pix para a chave da Vantara, como aqui, **não existe nenhum vínculo com o título.** Você tem um nome mutilado e um valor.

*TED.* Mesmo problema, às vezes pior:

```
23/07/2026;TED RECEBIDA CNPJ 66777888000199;;23.358,00;C
```

Esse nem nome tem — só o CNPJ no meio de texto livre.

**A lição central:**

> **O Pix resolveu a vida de quem paga e destruiu a vida de quem recebe.**

Antes, boleto era o padrão e a conciliação era quase automática. Hoje o franqueado paga por Pix porque é instantâneo e sem tarifa, e o financeiro ganhou um problema de identificação que o banco não resolve. É literalmente a origem dos "8% dos pagamentos entram sem identificação" da Vantara.

### 3. O que é conciliação, exatamente — e os três tipos que todo mundo confunde

Quando o cliente diz "automatiza a nossa conciliação", ele pode estar falando de três coisas diferentes. Saber distinguir isso no roleplay te separa de quem só repete o pedido:

1. **Conciliação de recebíveis (ou "de títulos").** Casar cada crédito do extrato com o título que ele quita. É o que a Vantara mais dói. Pergunta: *esse dinheiro é de qual nota?*
2. **Conciliação bancária.** Casar cada linha do extrato com um lançamento na contabilidade. Pergunta: *todo movimento do banco está registrado no livro, e o saldo contábil bate com o saldo bancário?* É obrigação contábil, mais ampla, inclui tarifas, impostos, transferências entre contas próprias.
3. **Conciliação de adquirência (cartão).** Casar venda no cartão com o repasse da adquirente (Cielo, Stone), que chega líquido de taxa e em D+30. A Vantara tem cartão no mix, então existe — mas não está no data pack.

Quando o Controller diz "duas analistas passam mais da metade do mês batendo pagamento", ele está falando do tipo 1. Quando ele diz "o fechamento leva 12 dias", o gargalo inclui o tipo 2.

### 4. A baixa — o ato que fecha o ciclo (e o verdadeiro nó técnico do case)

**Dar baixa** num título é marcá-lo como pago no ERP. É o que transforma "a Padaria me deve 18.450" em "a Padaria me pagou 18.450 no dia 10/07".

Enquanto a baixa não acontece, para todos os sistemas e todas as pessoas da empresa **aquele título continua em aberto**. Consequências em cascata:

- A régua de cobrança dispara: e-mail, ligação, bloqueio de pedido.
- O relatório de inadimplência conta aquele valor como não recebido.
- O DSO sobe.
- O fechamento não bate.

Isso é exatamente o que o Head de Operações de Franquias descreveu: *"meu time liga para quem já pagou"*. Não é incompetência do time de cobrança — é que a informação de que o cara pagou nunca chegou ao sistema que a cobrança consulta.

**Por que o veto de escrita no Protheus é o fato técnico mais importante do case.**

A baixa é uma **escrita** no ERP. O CTO liberou só **leitura e exportação** por 90 dias.

Isso significa que, nos primeiros 90 dias, **nenhuma solução sua consegue fechar o ciclo sozinha.** O máximo que ela pode fazer é:

- **propor** as baixas, com evidência e grau de confiança, para alguém aplicar; ou
- gerar um **arquivo de baixa em lote** no layout que o Protheus importa (normalmente CNAB ou uma rotina de importação própria), que o time da Vantara roda.

Isso não é um defeito do seu projeto — é uma restrição que você precisa desenhar *de propósito* e levar como argumento. Inclusive porque é um presente: **"eu não preciso de escrita no seu Protheus para entregar valor nos primeiros 30 dias"** é a frase que desarma o CTO. A solução vira um motor de decisão que cospe uma fila revisada; a aplicação continua nas mãos dele.

### 5. Os sete jeitos de o valor não bater (todos estão nos seus dados)

Esta é a parte que ninguém de fora de finanças imagina. Pagamento quase nunca chega igual ao título. Cada caso abaixo é uma linha real do data pack:

**(a) Casamento perfeito — 3 casos.** `nosso_numero` + valor idênticos. Regra determinística resolve. Exemplo: NF 104521.

**(b) Um crédito, vários títulos — agregação.**
```
14/07 TED RECEBIDA DOCE PONTO COM ALIME ... 47.630,50
```
Não existe nenhum título de 47.630,50. Existem dois: NF 104533 — 42.780,50 e NF 104588 — 4.850,00 (royalty). **Soma: 47.630,50** ✓

O franqueado juntou produto + royalty num TED só. Para resolver, você precisa testar **combinações** de títulos do mesmo CNPJ — e isso explode combinatorialmente se você não limitar bem o espaço de busca (mesmo pagador, janela de data, subset sum).

**(c) Pagamento parcial.**
```
NF 104560 — Empório Bela Vista — 125.000,00
16/07 LIQUIDACAO COBRANCA SIMPLES 000012345720 ... 62.500,00
```
Pagou exatamente metade. O título **não** vira "pago" — vira "parcialmente liquidado" com saldo de 62.500 em aberto. Se seu sistema der baixa total, você acabou de perder 62,5 mil de cobrança. Se marcar como não-pago, você cobra os 125 mil de novo e irrita o franqueado. **Tem que existir o conceito de baixa parcial.**

**(d) Chegou menos — retenção de imposto.**
```
NF 104571 — Cantinho Mineiro — Serviço — 15.600,00
17/07 PIX RECEBIDO CANTINHO MINEIRO FRA ... 14.820,00
```
Diferença: 780,00 = **exatamente 5%**. E repara que o `tipo` é **Serviço**, não Produto.

Em nota de serviço, quem contrata ("tomador") é frequentemente obrigado a **reter o ISS na fonte** e recolher direto para a prefeitura. Então o Cantinho Mineiro pagou 14.820 para a Vantara e 780 para a prefeitura, em nome da Vantara.

**Esse título está 100% quitado.** Os 780 não são inadimplência — são um crédito tributário da Vantara. Se o sistema tratar como "falta 780", o time de cobrança vai ligar cobrando imposto que o cliente já pagou. Esse é o tipo de regra que precisa estar explícita.

**(e) Chegou mais — multa e juros.**
```
NF 104601 — Padoca Central — 22.900,00 — vence 22/07
23/07 TED RECEBIDA CNPJ 66777888000199 ... 23.358,00
```
Diferença: +458,00 = **exatamente 2%**. Venceu dia 22, pagou dia 23. É a **multa de mora de 2%** prevista em contrato (normalmente 2% de multa + 1% ao mês de juros pro rata; com 1 dia de atraso o juros é centavos, então o que aparece é a multa).

O título quita, e os 458 são receita financeira — vão para outra conta contábil. Se o sistema exigir valor exato, essa linha cai na exceção para sempre.

**(f) Identificador escondido em texto livre.**
```
22/07 PIX RECEBIDO 11222333000166 ... 7.430,00
```
Não tem nome, tem CNPJ sem formatação dentro do histórico. Normalizando (`11.222.333/0001-66` → `11222333000166`) bate com a Sabor Express. **Regex resolve, não precisa de IA.** Importante saber a diferença: muita coisa que parece exigir IA é só normalização de string.

**(g) Só casa por valor.**
```
28/07 DEPOSITO NAO IDENTIFICADO ... 5.670,00
```
Zero informação de quem pagou. O único título de 5.670,00 no universo é a FAT-2026-0340 (Trigo e Cia Norte, Omie). Casa — mas **por eliminação**, o que é frágil: com 1.900 títulos/mês, colisão de valor vira comum. Esse caso **tem que sair com confiança baixa e ir para revisão humana.**

**(h) Bônus: dinheiro sem dono.**
```
30/07 PIX RECEBIDO PADARIA VILA NOVA LT ... 1.850,00
```
Não existe nenhum título de 1.850. Pode ser adiantamento, pode ser pagamento de uma nota de junho, pode ser erro do franqueado. Em finanças isso se chama **caixa não aplicado** (*unapplied cash*) e fica numa **conta transitória** até alguém investigar.

### 6. O achado mais importante: o título fantasma

Esse não é um problema de conciliação. É pior, e é o seu reframe.

```
Protheus  — NF 104580  — Grao Nobre Comercio Ltda — CNPJ 55.666.777/0001-44 — 31.250,00 — venc 20/07
Omie      — FAT-2026-0331 — GRAO NOBRE COM LTDA   — CNPJ 55666777000144     — 31.250,00 — venc 20/07
Banco     — 21/07 LIQUIDACAO 000012345740         — 31.250,00
```

**Mesma empresa. Mesma dívida. Dois ERPs. Um pagamento.**

Uma das três aquisições não integradas fez o cliente ser cadastrado nos dois sistemas, e o título foi lançado duas vezes. O franqueado pagou uma vez (corretamente). Resultado: **um título de 31.250 fica eternamente em aberto no Omie** e a régua de cobrança vai perseguir um franqueado que não deve nada.

Isso não tem solução no motor de conciliação. Nenhum algoritmo de matching conserta isso, porque não há dinheiro faltando — há dívida sobrando. O problema é **cadastro mestre** (*master data*).

Tem um segundo caso, mais sutil:
```
"Emporio Bela Vista Alimentos SA"  (Protheus) — 22.333.444/0001-55
"BELA VISTA EMPORIO S/A"           (Omie)     — 22333444000155
```
Mesmo CNPJ, nomes trocados de ordem e abreviados. Não é título duplicado (valores diferentes, são vendas distintas), mas **nenhum relatório da Vantara hoje consegue dizer quanto o Empório Bela Vista deve no total.** É aqui que a IA ganha de regra.

### 7. Os números que o CFO olha

**DSO (Days Sales Outstanding) — prazo médio de recebimento**

```
DSO = (Saldo de Contas a Receber ÷ Receita do período) × dias do período
```

Em português: **quantos dias, em média, a empresa espera para receber depois de vender.**

A Vantara tem **DSO de 62 dias contra 41 contratuais**. São **21 dias de capital de giro parado**.

Dimensionando com R$ 480M de faturamento:

```
480.000.000 ÷ 365 ≈ R$ 1,32M por dia de faturamento
21 dias × 1,32M     ≈ R$ 27,6M presos em recebíveis
```

A R$ 27,6M, com custo de capital de ~14% a.a. no Brasil, isso custa **~R$ 3,9M por ano** só para financiar o atraso. Esse é o número que faz o CFO ouvir.

**E aqui está o truque que você usa no roleplay:** DSO não mede só franqueado que atrasa. Ele mede **título que o ERP acha que está aberto**. Título fantasma, baixa não feita e pagamento não identificado inflam o DSO exatamente como inadimplência real.

Na sua amostra de 17 títulos, o gap aparente é R$ 100.342 — e só **R$ 8.120 é atraso de verdade**. Isso é **8% de inadimplência real contra 92% de problema de informação.**

**Inadimplência vs. atraso.** Vale separar no vocabulário: **atraso** é pagar depois do vencimento; **inadimplência** é a provisão de que não vai pagar (vira PCLD — provisão para crédito de liquidação duvidosa, normalmente após 90 ou 180 dias).

### 8. Lado 2 — Contas a Pagar, e como nasce um pagamento duplicado

Aqui o fluxo é o inverso, e o controle se chama **three-way match** (conferência tripla). Antes de pagar, três documentos têm que concordar:

```
1. PEDIDO DE COMPRA (PC)     — o que eu autorizei comprar e por quanto
2. RECEBIMENTO                — o que de fato chegou no estoque
3. NOTA DO FORNECEDOR         — o que ele está me cobrando
```

Se os três batem, paga. Se não batem, trava. É um controle antigo, chato e inteiramente eficaz — quando existe.

**Agora leia o arquivo 04 com esses olhos.**

**06/07** — São Jorge manda a NF 88231, R$ 18.900,00, vencimento 20/07, referente ao **PC 4471**.

WhatsApp, 06/07:
```
[11:02] Compras - Rafael: pessoal, NF 88231 Sao Jorge, 18.900, ok pra pagar?
[11:40] Controladoria - Bia: entrou o material completo?
[14:18] Compras - Rafael: acho que sim, o Joao confirmou
[14:19] Controladoria - Bia: ok, aprovado
```

A Bia fez a pergunta **certa** — ela está pedindo a etapa 2 do three-way match. E recebeu *"acho que sim, o João confirmou"*. Aprovou em cima disso.

**18/07** — A própria São Jorge revela, no corpo de um e-mail de cobrança, que *"o pedido PC 4471 foi entregue parcialmente (12 de 15 volumes)"*. Ou seja: **a Vantara aprovou 100% de uma entrega de 80%.** Pagou R$ 18.900 por R$ 15.120 de mercadoria. O controle existia, a pessoa certa perguntou, e o processo atropelou.

**E aí vem a parte perigosa.** No mesmo e-mail de 18/07, a fornecedora diz que não identificou o pagamento e **reemite o boleto atualizado: R$ 19.278,00, vencimento 25/07**, com linha digitável nova.

WhatsApp, 19/07:
```
[08:33] Fin - Camila: gente a Sao Jorge cobrando de novo a 88231, ja pagamos?
[08:35] Fin - Camila: achei, pagou dia 20. era outra nota entao?
[09:02] Controladoria - Bia: nao sei, alguem confere?
```

Olha a data. É **dia 19**. A Camila olhou o sistema, viu o pagamento **agendado** para dia 20, e leu como *já pago*. Concluiu que a cobrança deve ser de outra nota. A Bia perguntou "alguém confere?" e **ninguém respondeu**.

O extrato confirma que o pagamento de 18.900 saiu dia 20/07. Mas **o boleto atualizado de R$ 19.278,00, vencimento 25/07, continua vivo na caixa de entrada**, parecendo uma pendência legítima, com uma linha digitável válida.

> **Isso não é risco teórico. Isso é o terceiro pagamento duplicado do ano em formação.** Os dois primeiros custaram R$ 61 mil, e R$ 20 mil nunca voltaram.

**Por que pagamento duplicado é tão comum.** Porque o fornecedor reemite o título com **outro número, outro valor e outro vencimento** — e para o sistema é um documento novo. O cérebro humano não casa "NF 88231 / 18.900 / venc 20" com "NF 088231 / 19.278 / venc 25" quando passam 340 e-mails por mês pela caixa. Repara até no detalhe: um e-mail diz `88231`, o outro diz `088231` com zero à esquerda. É o mesmo documento com duas grafias.

**Por que essa é a frente mais fácil de defender com o CTO:**

1. **Não toca no Protheus.** A caixa de entrada é e-mail. Você não precisa do acesso que ele vetou.
2. **A perda é dura e já documentada.** R$ 61 mil, um nunca recuperado. Não é "ganho de eficiência estimado".
3. **É onde IA é insubstituível.** E-mail em prosa, PDF anexo, thread de WhatsApp — nenhuma regra determinística lê isso. Já conciliação de AR é ~70% regra.
4. **O resultado é verificável em dias**, não em trimestres.

### 9. Fechamento contábil: por que 12 dias úteis

**Fechamento** é apurar o resultado do mês: quanto a empresa faturou, quanto gastou, quanto lucrou, e emitir DRE e balanço.

A razão de ser lento começa num conceito: a contabilidade roda em **regime de competência** — a receita é reconhecida quando a venda acontece, não quando o dinheiro entra. Já a tesouraria roda em **regime de caixa**. Fechar o mês é, em boa parte, **reconciliar essas duas visões**. E isso exige:

- todo título a receber identificado e com baixa correta;
- toda despesa do mês provisionada (inclusive nota que ainda não chegou);
- todas as 4 contas bancárias conciliadas, linha por linha;
- nenhum valor dormindo em conta transitória.

Cada pagamento não identificado é um **bloqueador individual** de fechamento. Alguém precisa caçar, perguntar ao franqueado, achar e lançar. Com 8% de 1.900 títulos, são **~150 investigações manuais por mês** — e elas são seriais, não paralelas, porque dependem de resposta de terceiro.

Daí os 12 dias úteis. E daí a frase do CFO, que é a melhor frase do documento:

> *"Eu tomo decisão com número de três semanas atrás. Quando o fechamento sai, eu já decidi."*

Traduzido: **o produto do fechamento não é informação, é arquivo morto.** Ele já decidiu por instinto. Essa é a dor de negócio real — não "conciliação é chata", mas "a empresa de R$ 480M dirige olhando o retrovisor".

### 10. Glossário para o roleplay

| Termo | O que é |
|---|---|
| **Título** | Registro da dívida no ERP. Uma NF pode gerar vários (parcelas). |
| **Baixa** | Marcar o título como pago. É uma **escrita** no ERP — o que o CTO vetou. |
| **Baixa parcial** | Quitar só parte do título, mantendo saldo em aberto. |
| **Nosso número** | Identificador único do boleto, gerado pelo banco. O que torna boleto fácil de conciliar. |
| **Linha digitável** | Os 47 dígitos do boleto. Carrega banco, valor e vencimento. |
| **Arquivo retorno / CNAB** | Arquivo que o banco manda com os boletos liquidados. Base da baixa automática. |
| **Cobrança simples** | Banco cobra em nome da empresa, sem antecipar dinheiro. |
| **Desconto de duplicata** | Banco antecipa o recebível cobrando juros. Não é o caso aqui. |
| **DSO** | Dias médios para receber. 62 na Vantara, 41 no contrato. |
| **Régua de cobrança** | Sequência automática de ações por dias de atraso (e-mail → ligação → bloqueio). |
| **PCLD** | Provisão para créditos de liquidação duvidosa. O que você assume que não vai receber. |
| **Retenção na fonte** | Imposto (ISS, IRRF, PIS/COFINS/CSLL) que o pagador recolhe e desconta do valor. Faz o título "chegar menos" sem estar em aberto. |
| **Mora** | Multa + juros por atraso. Faz o título "chegar mais". |
| **Caixa não aplicado** | Dinheiro recebido sem título identificado. Fica em conta transitória. |
| **Three-way match** | Conferir pedido × recebimento × nota antes de pagar. |
| **PC / PO** | Pedido de compra. A autorização prévia do gasto. |
| **Regime de competência** | Reconhecer receita/despesa no fato gerador, não no caixa. |
| **Fechamento** | Apurar o mês e emitir DRE/balanço. 12 dias úteis na Vantara. |
| **Cadastro mestre** | A tabela de "quem é cada cliente/fornecedor". Onde nasce o título fantasma. |

### 11. O resumo que importa

Se eu tivesse que te dar uma única frase para carregar no roleplay, é esta:

> **A Vantara não tem um problema de conciliação. Tem um problema de identidade — de pagador e de documento — e conciliação é só onde esse problema fica visível.**

Tudo que você viu encaixa nisso:

- O franqueado é **duas entidades diferentes** em dois ERPs → título fantasma, cobrança indevida, DSO inflado.
- O pagamento **não carrega identidade** quando vem por Pix/TED → 8% não identificado, 150 investigações/mês, fechamento de 12 dias.
- A nota do fornecedor é **dois documentos diferentes** para o sistema quando reemitida → pagamento duplicado, R$ 61 mil.

E é por isso que o pedido literal deles — *"uma IA que bate pagamento"* — é a resposta errada: um motor de matching perfeito ainda cobraria os R$ 31.250 do Grão Nobre, porque o erro não está no matching, está um nível acima.

É também, provavelmente, a razão pela qual a ferramenta de IA do ano passado está parada: ela resolveu o sintoma visível, exigiu que as pessoas trabalhassem num lugar novo, e não mudou nada no sistema onde o trabalho realmente acontece.

---

Se quiser, o próximo passo natural é eu montar isso como um guia de estudo que você consulta até a reunião — ou podemos ir direto para a arquitetura da solução, agora que o vocabulário está no lugar. Qual dos dois te serve mais?

---

# TURNO 3 — Construção

## Mensagem enviada

> ```
> Vamos para a solução
> ```

## Resposta inicial da IA

> Vamos construir. Arquitetura primeiro, decidida e defensável, depois o código rodando.
>
> A decisão central: **o motor não é de conciliação, é de identidade.** Um só núcleo resolve "quem é essa entidade" e "qual documento é esse", e ele alimenta tanto o Contas a Receber quanto o Contas a Pagar. É isso que vira reusável para as próximas cinco contas — o conector do Protheus não vira.

## Log de execução

Toda chamada de ferramenta, em ordem. Nove tarefas foram criadas e acompanhadas em
um quadro de progresso; os marcos aparecem como `[TAREFA]`.

### Fase 1 — Esqueleto e contratos

**[6] TaskCreate ×9** — plano de trabalho: arquitetura, ingestão, identidade, motor AR,
camada de IA, detector de AP, saídas, observabilidade+testes, README+verificação.

**[7] TaskUpdate** — tarefa 1 em progresso.
**[8] Bash** — criar estrutura e copiar o data pack intocado
```bash
mkdir -p vantara-concilia/{config,src/{ingest,identidade,ia,ar,ap,saida},tests,data_pack,out}
cp .../data_pack/* vantara-concilia/data_pack/
python3 --version   # 3.13.16
```

**[9] Write** `config/regras.yaml` — toda a política financeira fora do código:
confianças por tier, ajustes por classe de valor, faixas de decisão, travas de
automação, faixas de retenção (ISS 2/3/5%, IRRF 1,5%, PIS/COFINS/CSLL 4,65%, INSS 11%),
fórmula de mora, limites de agregação, janela de crédito, stopwords e ruído de
histórico, parâmetros de fantasma, de AP, de observabilidade e de IA.

**[10] Write** `src/canonico.py` — schema canônico: `Entidade`, `Titulo`,
`MovimentoBancario`, `Evidencia`, `Conciliacao`, `MovimentoOrfao`, `TituloEmAberto`,
`Alerta`, `ResultadoExecucao`, e os enums `TierIdentidade`, `ClasseValor`, `Decisao`,
`Severidade`.

**[11] Write** `src/normalizacao.py` — CNPJ, nome, valor pt-BR/ISO, data, documento,
linha digitável, e a classe `NormalizadorNome` com cobertura por containment e
casamento do último token por prefixo.

**[12] Edit** `src/normalizacao.py` — troca de `valor_da_linha_digitavel` por
`valores_possiveis_da_linha_digitavel`.

> **Decisão registrada.** Ao implementar a leitura do campo de valor da linha digitável
> (posições 38-47, padrão FEBRABAN), o valor da São Jorge dá R$ 192,78 em centavos,
> mas o corpo do e-mail diz R$ 19.278,00. O autor do case escreveu o valor em reais.
> Em vez de gerar um alerta de divergência — que seria **falso positivo em cima de
> artefato do dado de teste** — passei a aceitar as duas leituras e registrei isso em
> "Limitações conhecidas" do README. Falso positivo é o que faz a analista desligar a
> ferramenta.

### Fase 2 — Ingestão

**[13] Write** `src/ingest/__init__.py` e **[14] Write** `src/ingest/base.py` —
leitura tolerante a encoding (utf-8-sig → utf-8 → cp1252 → latin-1), detecção de
delimitador por `csv.Sniffer`, normalização de cabeçalho, `primeiro_campo()` para
absorver variação de layout.

**[15] Write** `src/ingest/protheus.py` e **[16] Write** `src/ingest/omie.py`
**[17] Write** `src/ingest/banco_itau.py`
**[18] Edit** `src/canonico.py` — acrescenta `CobrancaRecebida` e `MensagemAprovacao`.
**[19] Write** `src/ingest/inbox_ap.py` — parser do e-mail em prosa + thread de WhatsApp.

**[20] Bash** — testar os quatro adapters antes de construir qualquer coisa em cima
```
protheus 12 omie 5 mov 18 cobrancas 3 aprovacoes 7
--- COBRANCA inbox_ap:e_mail_2 | doc 088231 -> 88231 | cobrado 19278.00 | original 18900.00 | venc None | reemissao True
    parcial: 278 Obs: o pedido PC 4471 foi entregue parcialmente (12 de 15 volumes), o restante sai na proxima semana. [anexo: ...
```

> ### MOMENTO 1 — a IA errou, e errou em silêncio
>
> Dois bugs apareceram aqui, e nenhum dos dois levantou exceção:
>
> **(a) `venc` vazio no e-mail 2.** O regex gerado era
> `r"\bvenc(?:imento|\.)?\b[\s:]*(\d{2}/\d{2}(?:/\d{4})?)"`. Parece correto. Mas depois
> de casar `venc.`, o `\b` final exige fronteira de palavra — e entre `.` e espaço
> **não há fronteira**, porque ambos são não-palavra. Então `(venc. 25/07/2026)`
> falhava silenciosamente e devolvia `None`.
>
> **25/07/2026 é a data de vencimento do boleto reemitido da São Jorge** — a data mais
> importante do data pack inteiro, porque é o que diz que um boleto de R$ 19.278,00 de
> nota já paga ainda está vivo e pagável.
>
> **(b) trecho de entrega parcial cortado no meio de um número.** A extração usava
> janela de caracteres e produzia `"278 Obs: o pedido PC 4471..."`.
>
> **Como peguei:** antes de construir a segunda camada, imprimi a saída da ingestão
> campo por campo e conferi contra os arquivos à mão. Dois dos três e-mails tinham
> `venc` e só um saiu com data.

**[21] Edit** `inbox_ap.py` — remove o `\b` final do regex de vencimento (com comentário
explicando o motivo, para ninguém "limpar" depois) e acrescenta `_RE_LOTE_ANEXO`.

**[22] Edit** `inbox_ap.py` — `_trecho` passa a devolver a frase, não a janela.

**[23] Edit** `inbox_ap.py` — nota de premissa para cobrança em lote (46 CT-e em anexo ausente).

**[24] Bash** — reteste: vencimento `2026-07-25` ✓, trecho ainda ruim (sem ponto final
antes de `Obs:`, o achatamento juntava a linha digitável à frase).

**[25] Edit** `inbox_ap.py` — `_trecho` isola o **parágrafo** primeiro (quebra por linha
em branco), só depois corta em frase.

**[26] Bash** — verificação:
```
parcial e-mail 2 -> 'Obs: o pedido PC 4471 foi entregue parcialmente (12 de 15 volumes), o restante sai na proxima semana'
```

### Fase 3 — Núcleo de identidade

**[27] TaskUpdate** — tarefas 1 e 2 concluídas, 3 em progresso.

**[28] Write** `src/identidade/resolver.py` — agrupamento de entidades por CNPJ
normalizado (determinístico, sempre vence) e por chave canônica de nome. Devolve
**todos** os candidatos por nome, não o melhor, para permitir detecção de empate.

> **Decisão registrada.** Deliberadamente **sem IA** nesta camada. Unificação de
> cadastro precisa ser reproduzível: se rodar duas vezes e der entidade diferente, a
> controladoria perde a confiança no primeiro mês. A IA entra depois, para desempatar,
> nunca para criar entidade.

**[29] Write** `src/identidade/fantasma.py` — detector de título duplicado entre ERPs.
Chave de colisão: entidade + valor + vencimento na folga, **sem** número de documento —
porque é justamente ele que difere entre os sistemas, e usá-lo é o que faz o ERP não
enxergar a duplicidade. Roda **antes** do matching.

**[30] Write** `src/ar/valor.py` — eixo valor: retenção, mora, parcial, agregado,
inexplicado, com a aritmética que justifica cada classificação e busca de subconjunto
para agregação.

**[31] Bash** — confere PyYAML disponível (6.0.3).

**[32] Bash** — smoke test do motor AR. Resultado: 11 entidades para 17 títulos,
1 alerta de fantasma, 2 de nomes divergentes, 14 conciliações, 1 órfão, 3 em aberto —
todos os casos exatamente como a análise manual do Turno 1 previa. Uma anomalia:

```
10/07/2026     3.200,00 | NOME_PARCIAL EXATO    conf=0.75 CONFIRMAR  -> NF 104522
ORFAO 30/07/2026 1.850,00 | PIX RECEBIDO PADARIA VILA NOVA LT | None
```

**[33] Write** `src/ia/cliente.py` — lista fechada, abstenção de primeira classe, cache
em disco, degradação sem chave, `_extrair_json` tolerante a ```` ```json ```` e prosa.

**[34] Edit** `config/regras.yaml` — acrescenta `bonus_unicidade: 0.15`.

**[35] Write** `src/ar/matcher.py` — a cascata de cinco passes, o modelo de confiança,
as travas e a classificação do que sobra.

**[36] Bash** — smoke test. O caso `PADARIA VILA NOVA LT` continuava rebaixado.

> ### MOMENTO 2 — lógica correta, resultado de negócio errado
>
> ```
> 'PIX RECEBIDO PADARIA VILA NOVA LT'  →  [PADARIA, VILA, NOVA, LT]
> 'Padaria Vila Nova Ltda'             →  [PADARIA, VILA, NOVA]
> cobertura: 3/4 = 75%  →  NOME_PARCIAL  →  0,75  →  CONFIRMAR
> ```
>
> Um Pix com o **nome completo** do franqueado e valor **exatamente igual** ao título
> foi rebaixado para revisão manual. `LT` é um `LTDA` cortado em 32 caracteres pelo
> extrato; como `LTDA` é stopword societária, foi removido do lado do título e o
> fragmento ficou sem par, contando como falha.
>
> Um teste de "a função calcula o que diz calcular" passaria. O erro só aparece
> perguntando *"esse resultado faz sentido para a operação?"*. Foi daqui que vieram os
> testes nomeados por caso de negócio em vez de por função.

**[37] Edit** `src/normalizacao.py` — `tokens_do_historico` descarta fragmento final que
é prefixo de stopword.

**[38] Bash** — reteste. `NOME_FORTE`, conf 0,93, `AUTO_APLICAR`. E o mesmo ajuste
resolveu de graça o órfão:
```
ORFAO 30/07/2026 1.850,00 | PIX RECEBIDO PADARIA VILA NOVA LT | Padaria Vila Nova Ltda (12.345.678/0001-90)
```

### Fase 4 — Contas a pagar

**[39] TaskUpdate** — tarefas 3, 4 e 5 concluídas; 6 em progresso.

**[40] Write** `src/ap/duplicidade.py` — identificação de pagamentos nos débitos,
agrupamento por domínio + documento normalizado, detecção de reemissão de nota já paga,
gap de three-way match com a aritmética do devido, e análise da trilha de aprovação
(confirmação vaga e conferência contra data futura).

**[41] Bash** — teste. Cinco achados, todos corretos:

```
AP-001 CRITICO RISCO DE PAGAMENTO EM DUPLICIDADE          risco 19.278,00
AP-004 CRITICO Conferência baseada em agendamento          risco 19.278,00
AP-002 ALTO    Gap de three-way match                      risco  3.780,00
AP-003 ALTO    Aprovação sem evidência de recebimento
AP-005 MEDIO   Cobrança sem documento identificável        risco 34.117,82
```

### Fase 5 — Observabilidade e saídas

**[42] Write** `src/observabilidade.py` — conferência de fechamento (duas invariantes),
drift vs baseline, decomposição do gap.

> **Decisão registrada.** A segunda invariante só fechou depois de eu perceber que
> créditos com decisão `INVESTIGAR` não consomem saldo e, portanto, precisavam entrar
> como pendentes do lado do caixa. Foi a própria verificação que me ensinou isso.

**[43] Write** `src/saida/planilhas.py` — cinco CSVs em `;` com vírgula decimal e BOM.

**[44] Skill: dataviz** — carregada antes de escrever uma linha do relatório.
**[45] Bash ×2** — leitura de `references/palette.md` (paleta categórica, status, superfícies).
**[46] Bash** — validação da paleta, conforme a disciplina manda (rodar, não raciocinar):
```
node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light --pairs all
  [PASS] Lightness band / Chroma floor / CVD separation (ΔE 9.2) / Normal-vision (ΔE 24.0)
  [WARN] Contrast vs surface — relief required: #1baf7a 2.74
→ ALL CHECKS PASS
(dark: todos PASS)
```
O WARN obriga rótulos diretos visíveis ou vista em tabela — o relatório traz os dois.

**[47] Write** `src/saida/relatorio.py` — relatório HTML com tema claro/escuro, faixa de
confiança no topo, barra de composição com rótulo direto e tooltip, barras ranqueadas
por tier, tabelas de decisão e de invariantes.

**[48] Write** `src/pipeline.py` — orquestração em 7 etapas.
**[49] Write** `run.py` — CLI com `--sem-ia`, `--dados`, `--saida`, `--config`,
`--resumo`, e **código de saída 1** quando a conferência falha.

**[50] Bash** — primeira execução ponta a ponta. `exit=0`, invariantes em 0,00. Mas:

> ### MOMENTO 4 — o número inflado que eu quase levei para a reunião
>
> O terminal imprimiu `Valor total em risco: 107.703,82`. Errado de duas formas:
>
> 1. `AP-001` (o boleto de R$ 19.278,00) e `AP-004` (a conferência que o deixou passar)
>    são **dois alertas sobre o mesmo dinheiro**. A soma contava R$ 38.556,00.
> 2. Os R$ 34.117,82 da transportadora entraram como "risco" junto com perda
>    comprovada — mas aquilo é cobrança que **não dá para verificar**, porque o anexo
>    com as 46 CT-e não veio.
>
> Um número inflado desmontado em trinta segundos de reunião não custa só o número:
> custa a credibilidade de tudo o que vier depois.

**[51] Edit** `src/canonico.py` — acrescenta `grupo_risco` e `tipo_risco` a `Alerta`.
**[52] Bash** — script de patch marcando grupos de risco em `fantasma.py` e `duplicidade.py`.
**[53-55] Edit ×3** `src/observabilidade.py` — `_agregar_risco`: máximo por grupo, não soma.
**[56] Bash** — patch de `run.py` e `relatorio.py` para exibir os dois números separados:
```
Exposição confirmada: 54.308,00
Exposição sem controle: 34.117,82
7 grupo(s) de exposição distintos em 8 alertas
```

### Fase 6 — Data pack adversarial

**[57] Bash** — construção de `data_pack_estresse/` com oito casos que o data pack real
não contém: dois clientes de nome colidente com títulos de valor idêntico; dois títulos
de mesmo valor contra um depósito cego; desconto de 5% num título de **Produto**;
excesso fora da fórmula de mora; nome muito abreviado (`SBR EXPRESS DLVRY`) contra
título de serviço com 2% de ISS; título já liquidado no ERP de origem; data pt-BR em
arquivo ISO; linha corrompida; e uma **nota nova legítima** do mesmo fornecedor (NF
88400) como teste de falso positivo.

**[58] Edit** `src/ar/matcher.py` — `aceitar_inexplicado`, com a justificativa no docstring.
**[59] Edit** `src/ar/matcher.py` — passo (e) do `_escolher_por_valor`.
**[60] Bash** — patch dos call sites e execução sobre o pack de estresse.

> ### MOMENTO 3 — onde eu contrariei a IA
>
> A versão original devolvia `None` quando nenhuma regra explicasse a diferença, e o
> crédito virava órfão. O comentário dizia *"melhor deixar órfão do que forçar vínculo
> ruim"* — soa prudente.
>
> O pack de estresse mostrou o custo: crédito de R$ 21.000,00 **com o nome completo do
> franqueado no histórico**, contra título de R$ 20.000,00 vencido no dia anterior,
> virava "caixa não aplicado". A analista recebia um órfão quando a informação
> disponível era "R$ 21.000,00 do Cantinho Mineiro contra a NF 104703, R$ 1.000,00 de
> diferença sem explicação".
>
> Tornei a regra **assimétrica**: identidade forte linka mesmo sem explicar o valor (e
> a trava rebaixa para confirmação humana); identidade fraca continua não linkando.
> Prudência não é recusar sempre — é recusar onde a evidência é ruim.

**[61] Bash** — inspeção caso a caso do pack de estresse. Todos se comportaram como projetado:

```
27/07  21.000,00 | NOME_FORTE INEXPLICADO 0.53 INVESTIGAR -> NF 104703
25/07  19.900,00 | SO_VALOR   EXATO       0.50 INVESTIGAR -> AMBÍGUO: NF 104700, NF 104701. Não baixar.
28/07   4.321,00 | SO_VALOR   EXATO       0.50 INVESTIGAR -> AMBÍGUO: NF 104706, NF 104707. Não baixar.
26/07   9.500,00 | ID_BANCARIO PARCIAL    0.94 AUTO       -> NF 104702 (Produto: PARCIAL, não RETENCAO)
ORFAO 27/07 8.624,00 | PIX RECEBIDO SBR EXPRESS DLVRY | não identificado
AVISOS: linha 19 e 23 — valor inválido/zerado, título ignorado
```

**[62] Bash** — verificação de disponibilidade da IA e dos alertas do pack de estresse:
```
ANTHROPIC_API_KEY: AUSENTE
SDK anthropic: ausente
```
E o teste de falso positivo passou: a NF 88400 **não** gerou alerta algum.

### Fase 7 — Testes

**[63] Bash** — `pip install anthropic pytest` (anthropic 1.13.0, pytest 9.1.1).

> **Decisão registrada.** Sem chave de API no ambiente, optei por testar os guard-rails
> da IA com um **cliente stub** em vez de pedir a chave. É teste melhor: preciso provar
> o que acontece quando o modelo devolve id inexistente, se abstém, ou responde com
> confiança baixa — e uma chamada real não produz esses casos sob demanda.

**[64] TaskUpdate** — tarefas 6 e 7 concluídas; 8 em progresso.
**[65] Write** `tests/conftest.py` — fixtures de sessão para os dois data packs.
**[66] Write** `tests/test_golden_set.py` — um teste por caso real, nomeado por negócio.
**[67] Write** `tests/test_contas_a_pagar.py` — o caso São Jorge e o **não-caso**.
**[68] Write** `tests/test_limites_e_ia.py` — casos adversariais + guard-rails com stub.

**[69] Bash** — `python3 -m pytest -q` → **46 passed in 0.16s**.

### Fase 8 — README e verificação

**[70] TaskUpdate** — tarefa 8 concluída; 9 em progresso.
**[71] Bash** — `requirements.txt`, `.env.example`, `.gitignore`, `Makefile`.
**[72] Write** `README.md` — 11 seções: como rodar, saídas, diagnóstico, arquitetura,
governança, onde a IA atua, onde quebra, o que é reusável, estrutura, 30 dias, premissas.
**[73] Write** `MOMENTOS.md` — os cinco momentos, três deles erros.
**[74] Bash** — `prompts/LEIA-ME.md` e **verificação em sala limpa**: apagar tudo que é
gerado e rodar seguindo só o README.
```
=== make testes ===        46 passed
=== make rodar-sem-ia ===  exit=0, 7 arquivos em out/
=== make estresse ===      exit=0
```

**[75] Bash** — script Playwright para screenshot do relatório → falhou
(`ERR_MODULE_NOT_FOUND`).
**[76] Bash** — instalação local do Playwright no scratchpad e captura em três modos.
**[77] Read** `rel_light_1180.png` — inspeção visual (a disciplina de visualização manda
olhar o resultado, não só validar cores). Três problemas:
- cabeçalho dizia "15 créditos" e o README dizia 16 — **o README estava errado**;
- o segmento verde de 8% ficava sem rótulo (limiar de 12%);
- os ícones `!!` e `~` nos títulos pareciam erro de digitação.

**[78] Read** `rel_light_390.png` — mobile: sem overflow horizontal, tiles empilham,
rótulos escondidos com legenda e tabela como alívio. OK.

**[79] Bash** — leitura das métricas reais para corrigir o README:
```
movimentos 18  creditos 15  conciliados 14  cobertura 0.9941  auto 0.5581
```
**[80] Edit** `README.md` — corrige para `15 créditos` e `14/15`.
**[81] Bash** — glifos geométricos (◆ ▲ ■ ●) no lugar de `!!`/`~`, limiar de rótulo de
12% → 7%, regeneração e nova captura.
**[82] Read** `rel_dark_1180.png` — tema escuro correto, rótulo de R$ 8.120,00 visível.

**[83] Bash** — verificação final e empacotamento → **644 arquivos, 3,3 MB**. Errado.
**[84] Bash** — diagnóstico: `node_modules` (13 MB) vazou para dentro do projeto porque
o `npm install` do screenshot rodou a partir do diretório do projeto.
**[85] Bash** — remoção, `.gitignore` atualizado, reempacotamento:
**67 arquivos, 130 KB**, e conferência de que não há credencial no pacote.

**[86] TaskUpdate** — tarefa 9 concluída.
**[87] SendUserFile** — entrega de `vantara-concilia.zip` e `out/relatorio.html`.

## Resposta final da IA

Solução construída, rodando e testada. 5.607 linhas, 46 testes, execução limpa do zero.

### A tese que o código defende

**O motor não é de conciliação, é de identidade.** Um núcleo resolve "quem é essa
entidade" e "qual documento é esse", e alimenta tanto o AR quanto o AP. Isso é o que
vira reusável para as próximas cinco contas — conector de Protheus não é.

A separação que organiza tudo:

```
EIXO IDENTIDADE  →  de quem é esse dinheiro?    (cascata: nosso número → CNPJ → nome → IA → só valor)
EIXO VALOR       →  por que o valor difere?     (exato / parcial / retenção / mora / agregado / inexplicado)
```

Quatro dos 14 créditos conciliáveis têm valor diferente do título, e **todos os quatro
têm explicação financeira legítima**. Um motor que exige valor exato joga os quatro na
exceção — e, no caso da retenção de ISS, manda cobrar R$ 780 de imposto que o
franqueado já recolheu.

### Resultado sobre julho

| | |
|---|---|
| Conciliados | 14/15 créditos, cobertura 99,4% |
| Automatizável sem humano | 55,8% do valor, 9 baixas propostas |
| Exposição confirmada | R$ 54.308,00 |
| Exposição sem controle | R$ 34.117,82 |
| Conferência de fechamento | OK — as duas invariantes fecham ao centavo |

E o número do reframe: **dos R$ 101.870 em aberto, só R$ 8.120 (8%) é atraso de fato.**
R$ 31.250 é título fantasma do Grão Nobre — duplicado entre Protheus e Omie, já pago, e
que a régua de cobrança perseguiria.

Em contas a pagar, o pipeline reconstrói sozinho o caso São Jorge: nota paga em 20/07,
boleto de R$ 19.278 reemitido e **ainda vivo** na caixa, pagamento de 100% numa entrega
de 80% (R$ 3.780), e a conferência da Camila em 19/07 lendo um pagamento agendado para
o dia 20 como liquidado.

### Três coisas que você vai usar no roleplay

**"Eu não preciso de escrita no seu Protheus."** A saída é um arquivo de baixas
propostas. Não existe caminho de escrita para ERP no código, e tem um teste que falha
se alguém introduzir um. A restrição que ele impôs virou argumento a seu favor.

**A conferência de fechamento.** Duas equações que têm que fechar ao centavo em toda
execução. Se não fecharem, o pipeline sai com código 1 e o relatório abre em vermelho.
É a resposta direta a "como a operação descobre antes do cliente" — e, provavelmente, a
diferença em relação à ferramenta parada no contrato, que errava em silêncio.

**Onde a IA não atua.** No data pack de julho a cascata determinística resolve 14 de 14.
Declarar isso é o que te dá autoridade para dizer onde ela é insubstituível: os 340
e-mails/mês de contas a pagar, onde `"entregue parcialmente (12 de 15 volumes)"` está
enterrado num `Obs:`.

### Duas coisas que você precisa fazer

O `MOMENTOS.md` já está escrito com os cinco momentos reais desta sessão — incluindo
três em que a IA errou: o regex de vencimento que perdia em silêncio a data mais
importante do case, o match perfeito rebaixado para revisão manual, e o número de risco
inflado em R$ 38.556 que eu quase deixei você levar para a reunião. Confira se concorda
com a narrativa antes de enviar.

Falta exportar o transcript desta sessão para `prompts/` — tem um LEIA-ME lá explicando
a estrutura.

Quer que eu ataque agora o roteiro dos 4 minutos de vídeo, ou a mensagem ao CTO?

---

# TURNO 4 — Transcrição

## Mensagem enviada

> ```
> Gere, por favor, a transcrição de toda essa conversa.
> ```

## Chamadas de ferramenta

**[88] Write** `prompts/sessao_01_construcao.md` — turnos 1 e 2.
**[89] Bash** — acréscimo dos turnos 3 e 4 e dos apêndices.
**[90] Bash** — reempacotamento com a transcrição dentro.

---

# APÊNDICE A — Ambiente da sessão

| Item | Valor |
|---|---|
| Modelo | Claude Opus 5 (`claude-opus-5`), modo agêntico |
| Ferramentas usadas | shell (bash), leitura/escrita de arquivo, edição, leitura de imagem, skill `dataviz`, quadro de tarefas |
| Runtime | Python 3.13.16, Node 22.22, Linux, container efêmero |
| Pacotes instalados na sessão | `anthropic` 1.13.0, `pytest` 9.1.1, `playwright` 1.56.1 (só para screenshot) |
| `ANTHROPIC_API_KEY` | **ausente** — toda a execução registrada rodou com `--sem-ia` |
| Chamadas de ferramenta | 90 |
| Linhas de código produzidas | 5.607 (`src/`, `run.py`, `tests/`) |
| Testes | 46, ~0,2 s, sem rede e sem chave |

**Consequência de não haver chave:** a camada de IA nunca foi executada contra a API
real nesta sessão. Ela é exercitada por um cliente stub nos testes, que cobre os três
guard-rails. Para o vídeo de demo, basta `export ANTHROPIC_API_KEY=...` e `python run.py`
— o caso `SBR EXPRESS DLVRY` do pack de estresse é o que demonstra a IA recuperando um
crédito que a camada determinística perde por completo.

---

# APÊNDICE B — Mapa dos cinco momentos

| # | Momento | Onde aconteceu neste log | Natureza |
|---|---|---|---|
| 1 | Regex de vencimento que falhava em silêncio | chamadas [20]–[26] | **erro da IA**, pego por conferência manual |
| 2 | Match perfeito rebaixado para revisão manual | chamadas [32], [36]–[38] | **erro da IA**: lógica certa, resultado de negócio errado |
| 3 | Crédito com pagador identificado virando órfão | chamadas [57]–[61] | **discordância**: contrariei a proposta inicial |
| 4 | Risco somado em duplicidade (R$ 38.556 inexistentes) | chamadas [50]–[56] | **erro da IA**, pego por leitura crítica do próprio output |
| 5 | Decisão de usar menos IA do que seria possível | chamadas [28], [63] | **decisão de arquitetura** |

Narrativa completa em `../MOMENTOS.md`.

---

# APÊNDICE C — Como verificar esta transcrição

Tudo o que está descrito aqui é reproduzível a partir da pasta entregue:

```bash
pip install -r requirements.txt
python -m pytest -q                                              # 46 passed
python run.py --sem-ia                                           # exit 0
python run.py --sem-ia --dados data_pack_estresse --saida out_estresse
```

Os comentários no código registram as decisões no ponto onde elas valem — inclusive os
dois bugs do Momento 1 e do Momento 2, documentados para que ninguém os reintroduza:

- `src/ingest/inbox_ap.py`, `_RE_VENC` — por que não há `\b` depois do ponto
- `src/normalizacao.py`, `tokens_do_historico` — por que o fragmento final é descartado
- `src/ar/matcher.py`, `_escolher_por_valor` — por que a regra é assimétrica
- `src/observabilidade.py`, `_agregar_risco` — por que o total é máximo por grupo
