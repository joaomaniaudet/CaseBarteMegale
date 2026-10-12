# Roteiro da demo — até 4 minutos

## 00:00–00:30 — A aposta

“A Vantara pediu uma IA que bate pagamento. Eu comecei um nível antes: hoje Protheus, Omie e banco não compartilham uma identidade financeira confiável. Minha aposta de 30 dias é Recebíveis primeiro, zero escrita e uma fila auditável que separa fato, hipótese e exceção.”

Mostrar rapidamente os quatro arquivos do data pack.

## 00:30–01:10 — Executar

```bash
python run.py --sem-ia
```

Mostrar `out/relatorio.html` e explicar:

- 15 créditos recebidos;
- 14 receberam um vínculo proposto;
- 8 propostas são de alta confiança;
- 6 exigem confirmação;
- 1 permanece como caixa não aplicado.

Frase importante: “Alta confiança não significa escrita automática. O protótipo não possui acesso de escrita ao ERP.”

## 01:10–02:10 — Evidência versus hipótese

Abrir `01_fila_conciliacao.csv`.

1. Mostrar o boleto com `nosso_numero`: evidência determinística.
2. Mostrar o pagamento parcial de R$ 62.500: o título mantém saldo.
3. Mostrar R$ 14.820 contra R$ 15.600: aritmética compatível com retenção, mas exige documento fiscal.
4. Mostrar R$ 5.670 sem identificação: valor sugere candidato, mas nunca vira proposta automática.

## 02:10–02:50 — Possível duplicidade

Abrir `03_titulos_em_aberto.csv` e o alerta `CAD-001`.

“Mesmo CNPJ, valor e vencimento em Protheus e Omie é um forte indício, não uma prova. A ação segura é suspender a cobrança por até 48 horas e mandar Cadastro/TI validar a causa dos documentos. O motor não declara o cliente em dia sozinho.”

## 02:50–03:20 — Onde quebra

Mostrar `data_pack_estresse/` e mencionar:

- empate entre clientes vira investigação;
- colisão de valor não é resolvida por palpite;
- layout corrompido gera aviso;
- a conferência ao centavo prova conservação, não precisão semântica.

## 03:20–03:45 — Arquitetura

“Para o piloto, proponho o mesmo core da Barte empacotado em container assinado, mas executado na conta cloud da Vantara, read-only, com egress bloqueado. É uma exceção que precisa de aprovação interna da Barte. Nenhum dado real deve ir para API externa de IA sem aprovação.”

## 03:45–04:00 — Pedido ao CTO

“Preciso de três decisões: exports diários read-only, um ambiente isolado para o piloto e uma pessoa da Controladoria para assinar o golden set. Em quatro semanas, decidimos com precisão e falso positivo medidos se avançamos ou paramos.”
