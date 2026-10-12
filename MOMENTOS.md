# Os momentos que importaram

> **Nota de entrega:** este documento é uma retrospectiva editada. O transcript
> original ainda precisa ser exportado para `prompts/`; esta síntese não o
> substitui.

Cinco momentos do desenvolvimento com IA. Dois deles são erros que não quebraram
nada — e é por isso que foram os mais perigosos.

O histórico completo das sessões ainda não está em `prompts/`.

---

## 1. O regex que estava certo e perdia a data mais importante do case

**O que eu pedi.** Um parser para a caixa de entrada de contas a pagar que
extraísse valor, número de documento e vencimento de e-mail em prosa.

**O que voltou.** Entre outras coisas, este regex de vencimento:

```python
_RE_VENC = re.compile(r"\bvenc(?:imento|\.)?\b[\s:]*(\d{2}/\d{2}(?:/\d{4})?)")
```

Parece correto. Lê `vencimento 20/07` e `venc. 25/07/2026`. Não quebrou, não
levantou exceção, não gerou aviso.

**O problema.** Depois de casar `venc.`, o `\b` final exige fronteira de palavra
— e entre `.` e espaço não há fronteira, porque os dois são não-palavra. Então
`(venc. 25/07/2026)` **falhava em silêncio** e devolvia `None`.

Essa é a data de vencimento do boleto reemitido da São Jorge: **25/07/2026**. É a
data mais importante do data pack inteiro — é o que diz que o boleto de R$
19.278,00 de uma nota já paga ainda está vivo e pagável. Sem ela, o alerta
crítico sairia sem o prazo, e eu teria apresentado no vídeo um achado pela metade.

**O que eu fiz.** Peguei porque, antes de construir qualquer camada em cima, eu
imprimi o resultado da ingestão campo por campo e conferi contra os arquivos à
mão. Dois dos três e-mails tinham `venc` e só um saiu com data. Corrigi tirando o
`\b` final e documentei o motivo no código, para que ninguém "limpe" o regex
depois.

**A lição que levo.** Em pipeline de dados, o modo de falha que importa não é a
exceção — é o campo vazio que ninguém olha. O hábito que me salvou foi não
construir a segunda camada antes de ler a saída da primeira.

---

## 2. A lógica correta que produziu o resultado de negócio errado

**O que aconteceu.** O matching por nome contava quantos tokens do histórico
bancário aparecem na razão social. Lógica impecável. Resultado:

```
'PIX RECEBIDO PADARIA VILA NOVA LT'  →  [PADARIA, VILA, NOVA, LT]
'Padaria Vila Nova Ltda'             →  [PADARIA, VILA, NOVA]
cobertura: 3/4 = 75%  →  NOME_PARCIAL  →  confiança 0,75  →  CONFIRMAR
```

Um Pix com o **nome completo do franqueado** e valor **exatamente igual** ao
título foi rebaixado para revisão manual.

**Por quê.** `LT` é um `LTDA` cortado pelo limite de 32 caracteres do extrato do
Itaú. Como `LTDA` é stopword societária, ele tinha sido removido do lado do
título — então o fragmento não tinha par e contava como falha.

**O que eu fiz.** Fragmento final que é prefixo de stopword agora é descartado,
não contabilizado como erro. O caso subiu para `NOME_FORTE`, confiança 0,93,
automático. E o mesmo ajuste resolveu, de graça, a identificação do pagador do
crédito órfão de R$ 1.850,00 — que antes saía como "não identificado" e agora sai
como "Padaria Vila Nova Ltda", que é a diferença entre um telefonema e uma linha
que fica na planilha para sempre.

**A lição.** Teste que verifica "a função calcula o que diz calcular" passaria.
O erro só aparece quando você pergunta *"esse resultado faz sentido para a
operação?"*. Foi daí que vieram os testes nomeados por caso de negócio, em vez de
por função.

---

## 3. Onde eu contrariei a IA: deixar um crédito órfão era pior

**O que a IA propôs, e eu aceitei na primeira versão.** Em
`_escolher_por_valor`, quando nenhuma regra explicasse a diferença de valor,
devolver `None` — e o crédito virava "caixa não aplicado". O comentário que
escrevi na época: *"melhor deixar órfão do que forçar vínculo ruim"*. Soa
prudente.

**O que mostrou que estava errado.** Construí o data pack adversarial e coloquei
este caso: crédito de R$ 21.000,00 com o nome completo do franqueado no
histórico, contra um título de R$ 20.000,00 vencido no dia anterior. O excesso de
5% não fecha com a fórmula de mora (2,03% esperados). Resultado: **órfão.**

A analista recebia "crédito de R$ 21.000,00, pagador não aplicado" quando a
informação disponível era "crédito de R$ 21.000,00 do Cantinho Mineiro, contra o
título NF 104703 de R$ 20.000,00, R$ 1.000,00 de diferença sem explicação". A
segunda se resolve em um minuto; a primeira vira item de planilha.

**O que eu fiz.** Tornei a regra assimétrica, que é o ponto: **identidade forte
linka mesmo sem explicar o valor** (e a trava rebaixa para confirmação humana);
**identidade fraca continua não linkando**. Prudência não é recusar sempre — é
recusar onde a evidência é ruim.

---

## 4. A IA me entregou um número inflado, e eu quase levei para a reunião

**O que aconteceu.** Pedi a agregação dos alertas e recebi uma soma simples de
`valor_em_risco`. O terminal imprimiu:

```
Valor total em risco: 107.703,82
```

Bonito. E errado de duas formas.

**Primeira.** `AP-001` é o boleto reemitido de R$ 19.278,00. `AP-004` é a
conferência que deixou esse boleto passar. São **dois alertas sobre o mesmo
dinheiro**, e a soma contava R$ 38.556,00.

**Segunda.** Os R$ 34.117,82 da transportadora entraram como "risco" junto com os
outros. Mas aquilo não é perda comprovada — é uma cobrança que eu **não consigo
verificar** porque o anexo com as 46 CT-e não veio. Misturar as duas coisas num
número só é inflar.

**O que eu fiz.** Adicionei `grupo_risco` (o total é o máximo por grupo, não a
soma) e `tipo_risco`. A revisão posterior tornou a distinção mais rigorosa:
**perda confirmada — R$ 0,00**, **exposição potencial — R$ 50.528,00** e
**sem controle verificável — R$ 34.117,82**. Tem um teste travando isso
(`test_risco_nao_eh_contado_duas_vezes`).

**Por que isso foi o momento mais importante.** Eu ia defender esse número diante
de um CTO que foi descrito como alguém que *"quer entender por que começar por
essa frente"* — ou seja, alguém que confere. Um número inflado desmontado em
trinta segundos de reunião não custa só o número: custa a credibilidade de tudo o
que eu disser depois. A revisão mostrou que nem R$ 54.308,00 podia ser chamado
de perda confirmada: parte era exposição potencial e parte dependia de premissas
não fornecidas.

---

## 5. Onde eu decidi usar menos IA do que podia

**A tentação.** O case pede para usar IA, e teria sido fácil mandar os 16
créditos do extrato para o modelo com os 17 títulos e pedir o matching. Provavelmente
funcionaria nesta amostra.

**Por que não fiz.** Três razões, e nenhuma é economia de token:

1. **Com 1.900 títulos/mês eu não saberia dizer onde quebra.** Um motor com
   tiers nomeados me diz que 5 casos vieram de `nosso_numero` e 1 de `só por
   valor` — e que o último é o frágil. Uma caixa-preta me diz "funcionou".
2. **O CTO precisa auditar.** `ISS 5% retido na fonte; 14.820 + 780 = 15.600`
   é auditável. "O modelo concluiu que casa" não é.
3. **Reprodutibilidade.** Unificação de cadastro que dá entidade diferente em
   duas execuções faz a controladoria perder a confiança no primeiro mês.

**O resultado honesto.** No data pack de julho, **a IA não foi necessária para a
conciliação de recebíveis** — a cascata determinística resolve 14 de 14. Eu
poderia esconder isso. Prefiro declarar, porque é o que me permite dizer com
precisão onde ela É necessária: na extração dos e-mails de contas a pagar, onde
`"entregue parcialmente (12 de 15 volumes)"` está enterrado num `Obs:` e não tem
campo, com 340 e-mails por mês.

E porque é provavelmente a razão pela qual a ferramenta que eles compraram no ano
passado está parada: foi vendida como IA para um problema que precisava de
estrutura, e ninguém conseguiu auditar o que ela fazia.
