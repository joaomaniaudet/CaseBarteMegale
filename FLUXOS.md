# Fluxos da solução

Este documento resume o funcionamento auditável do Vantara Concilia. O piloto
não escreve nos ERPs nem dispara cobranças: ele prepara propostas e evidências
para decisão humana.

## 1. Fluxo de negócio

```text
Protheus + Omie + extrato Itaú + caixa de entrada de AP
                         │
                         ▼
            Normalização e identidade comum
                         │
                         ▼
          Conciliação e classificação de valor
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     alta confiança  confirmação     investigação
          │              │              │
          └──────────────┴──────────────┘
                         ▼
            decisão registrada da analista
                         │
                         ▼
       fechamento do caixa + arquivos de proposta
```

O objetivo é distinguir dinheiro validado, dinheiro em análise, erros marcados
e caixa não aplicado. Alertas de risco não são somados novamente ao caixa: eles
são uma lente de controle sobre fatos que já podem existir nas linhas financeiras.

## 2. Jornada do usuário

1. A pessoa abre a aplicação local com `streamlit run demo.py`.
2. Em **Preparar dados**, usa o data pack incluído ou envia os quatro arquivos.
3. Configura IA ligada/desligada e executa o processamento.
4. A aplicação avança para **Validar e fechar caixa**.
5. Na fila, a analista valida, mantém pendente ou marca a linha como erro.
6. A decisão atualiza imediatamente os totais de caixa validado, em análise e erro.
7. As abas mostram baixas propostas, riscos, visão executiva e caixa linha a linha.

## 3. Fluxo técnico

```text
Arquivos de entrada
  └─ src/ingest/*            leitura, encoding, separadores e schema
       └─ src/normalizacao   CNPJ, nomes, datas, moeda e identificadores
            └─ src/identidade
                 ├─ resolução de entidade
                 └─ possível duplicidade entre ERPs
                      └─ src/ar
                           ├─ matching de recebíveis
                           └─ explicação de valor
                                ├─ src/ap (alertas secundários)
                                ├─ src/observabilidade (invariantes)
                                └─ src/saida (CSV, JSON e HTML)
```

`config/regras.yaml` concentra política, tolerâncias, thresholds e travas. O
core não depende de nomes ou valores fixos da Vantara para decidir.

## 4. Cascata de decisão

```text
nosso número → CNPJ → nome forte/truncado → IA limitada → valor único
     forte       forte          médio          humano        humano
```

- Evidência forte e valor explicado podem gerar `AUTO_APLICAR`.
- Evidência útil, IA, retenção ou mora geram `CONFIRMAR`.
- Evidência insuficiente gera `INVESTIGAR` e não consome saldo.
- `AUTO_APLICAR` significa pronto para proposta, nunca baixa escrita no ERP.

## 5. Papel da IA

A IA é opcional. Ela recebe apenas candidatos previamente filtrados para
desempatar nomes distorcidos e extrair fatos de e-mails fora dos padrões. Uma
resposta inválida, falha de API ou baixa confiança cai no fallback determinístico
ou na fila humana. A IA não autoriza baixa.

## 6. Arquitetura proposta para produção

```text
Barte
  código versionado + CI + imagem assinada + suporte
                         │ distribuição controlada
                         ▼
Conta cloud da Vantara
  container isolado + bucket read-only + KMS + logs + egress restrito
                         │
                         ▼
  propostas CSV + relatório + trilha de auditoria no tenant da Vantara
```

Premissas ainda sujeitas a validação: cloud escolhida, mecanismo de CI/CD,
layout homologado do importador Protheus, política de retenção, provedor de IA
aprovado e autorização interna da Barte para o modelo de implantação no tenant.

## 7. Reuso pela Barte

O core reutilizável inclui schema canônico, adapters, motor de identidade,
explicação de valor, guard-rails, invariantes, filas, observabilidade e contrato
de IA. Por cliente ficam configuração de layouts, contas, políticas, tolerâncias,
limites, mapeamentos e destinatários. Em uma evolução multi-tenant, cada cliente
deve ter configuração, credenciais, armazenamento, criptografia e telemetria
isolados; essa plataforma não está implementada neste protótipo.
