# Vantara — camada auditável de identidade e conciliação

> **Recebíveis primeiro. Identidade antes de matching. Zero escrita no ERP.**

## Comece aqui

Esta pasta é a **raiz executável e entregável da solução**. Ela contém código,
configuração, fluxos, testes, data packs, apresentações e as saídas já geradas.
Não depende de Lovable, n8n, Replit ou outro serviço hospedado: a aplicação
Streamlit e o pipeline rodam localmente.

Para avaliar sem nenhuma conta ou chave de API, extraia o ZIP, entre na pasta
`vantara-concilia` e execute:

```bash
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py --sem-ia
python -m pytest -q
streamlit run demo.py --server.port 8501
```

Abra [http://localhost:8501](http://localhost:8501). O modo `--sem-ia` é a
reprodução oficial do case e não exige contas externas. A chave de LLM é
opcional e deve ser criada pelo avaliador em um arquivo local `.env`, conforme
[Configuração opcional da IA](#onde-colocar-a-chave-de-api-do-llm). Nenhuma
chave real faz parte da entrega.

Mapa de leitura:

- [FLUXOS.md](FLUXOS.md): fluxos de negócio, decisão, dados e arquitetura;
- [MANIFESTO_ENTREGA.md](MANIFESTO_ENTREGA.md): inventário do pacote e o que foi excluído;
- [ROTEIRO_DEMO.md](ROTEIRO_DEMO.md): roteiro para demonstrar a aplicação;
- `out/`: resultados oficiais já gerados a partir do data pack de julho.

A Vantara pediu uma “IA que bate pagamento”. O protótipo demonstra que o problema anterior ao matching é a falta de uma identidade financeira comum entre Protheus, Omie e banco. Ele consome os arquivos como vieram, normaliza entidades e documentos, propõe vínculos explicáveis e separa fatos de hipóteses.

O objetivo dos primeiros 30 dias não é fechar o mês sozinho. É entregar uma fila diária que a analista consegue auditar, reduzir cobrança indevida e medir com dados reais quais casos podem ganhar automação depois.

## Escopo do piloto

**Dentro do escopo**

- títulos a receber de Protheus e Omie;
- extrato da conta principal de cobrança;
- resolução de CNPJ, nomes truncados e identificadores bancários;
- propostas de baixa, confirmação humana e investigação;
- suspensão temporária de cobrança quando houver indício forte de duplicidade;
- conferência aritmética e métricas operacionais;
- alertas de contas a pagar como demonstração secundária.

**Fora do escopo**

- escrita automática em Protheus ou Omie;
- disparo automático de cobrança;
- confirmação fiscal de retenções sem nota, guia ou política aprovada;
- automação da liberação de pagamentos a fornecedores;
- adquirência/cartões e as outras três contas bancárias;
- leitura de anexos que não foram fornecidos no data pack.

Contas a pagar mostrou sinais importantes, mas não é a segunda implantação do piloto. Os alertas de AP provam uma expansão possível; não são tratados como perda materializada nem desviam o foco de Recebíveis.

## Como executar

### Pré-requisitos

- Python 3.10 ou superior e `pip`;
- navegador moderno para a interface Streamlit;
- nenhuma conta externa para o modo determinístico (padrão recomendado para reproduzir os resultados deste README);
- opcionalmente, uma chave de API de um dos três provedores suportados para a camada semântica (Anthropic, Google ou xAI) — veja abaixo.

### Passo a passo (modo determinístico, sem IA)

```bash
# depois de extrair o pacote, entre na raiz da solução
cd vantara-concilia

# 1. ambiente isolado (recomendado)
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. dependências
python -m pip install -r requirements.txt

# 3. execução reprodutível, sem nenhuma chave de API
python run.py --sem-ia

# 4. testes (47 casos)
python -m pytest -q

# 5. demo interativa local
streamlit run demo.py
```

Isso já reproduz os números da seção "Resultado reproduzido no data pack" abaixo, sem depender de nenhum provedor de IA.
O resultado esperado dos testes atuais é **47 passed**. Se a porta 8501 estiver
ocupada, use `streamlit run demo.py --server.port 8502`. Para encerrar, pressione
`Ctrl+C` no terminal que iniciou o Streamlit.

### Demo interativa — processar seus próprios dados

A demo (`streamlit run demo.py`) abre na etapa **"Preparar dados"**, onde o usuário pode:

1. **Fazer upload** dos 4 arquivos nos layouts esperados (ou usar os dados de exemplo sem enviar nada);
2. **Ligar ou desligar a IA** (requer `GOOGLE_API_KEY` no `.env`);
3. **Executar o pipeline** e ver o resultado como um checklist de verificação:

| Etapa | O que mostra | Ação quando há pendência |
|---|---|---|
| **Ingestão** | Arquivos carregados, avisos de encoding | Corrigir formato/encoding do arquivo |
| **Identidade** | Entidades unificadas, possíveis duplicidades | Validar documentos de origem antes de cobrar |
| **Conciliação** | Baixas automáticas, itens para revisão, investigação | Revisar na Fila de revisão (validar/marcar como erro) |
| **Caixa não aplicado** | Créditos sem título associado | Verificar outras contas, meses ou títulos não exportados |
| **Alertas** | Riscos por severidade (crítico/alto/médio/info) | Tratar cada alerta conforme destinatário indicado |
| **Conferência** | Invariantes aritméticas (títulos = vínculos + saldo) | Não usar as saídas se a conferência falhar |

Ao final da etapa de processamento, a aplicação avança automaticamente para
**Validar e fechar caixa**. Nessa etapa, a analista acompanha a Fila de revisão,
Baixas automáticas, Alertas e riscos, Painel executivo e Caixa linha a linha.
Validar uma linha, marcá-la como erro ou mantê-la pendente atualiza o fechamento
operacional em tempo real.

### Onde colocar a chave de API do LLM

A camada de IA é **opcional** e só entra em jogo para desempate de nomes muito distorcidos e extração de e-mails de AP (veja "Onde a IA atua"). O provedor padrão em `config/regras.yaml` é `auto` (detecta pela primeira chave presente no ambiente), e o cliente (`src/ia/cliente.py`) aceita três:

| Provedor | Variável de ambiente | Modelo padrão | SDK |
|---|---|---|---|
| Google (Gemini) — **recomendado** | `GOOGLE_API_KEY` ou `GEMINI_API_KEY` | `gemini-3-flash-preview` | `google-genai` |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | `claude-sonnet-4-5` | `anthropic` |
| xAI (Grok) | `XAI_API_KEY` ou `GROK_API_KEY` | `grok-3-mini` | `openai` |

**Recomendação para quem for avaliar:** use **Google Gemini** com o modelo `gemini-3-flash-preview`. É gratuito no tier free do Google AI Studio e foi o provedor testado e validado neste protótipo. Para obter a chave:

1. Acesse [aistudio.google.com/apikey](https://aistudio.google.com/apikey);
2. Clique em "Create API key" e selecione um projeto (ou crie um novo);
3. Copie a chave gerada.

`python run.py` e `streamlit run demo.py` carregam o arquivo `.env` da raiz do projeto automaticamente (via `python-dotenv`, já listado em `requirements.txt`). Não é preciso exportar nada no shell.

```bash
# 1. copie o template (NUNCA versione o arquivo .env)
cp .env.example .env

# 2. edite o .env e cole a chave do Google AI Studio:
#    GOOGLE_API_KEY=sua-chave-aqui

# 3. rode normalmente — o provedor é detectado automaticamente pela chave
python run.py
```

Para trocar de provedor sem editar código, mude `ia.provedor` em `config/regras.yaml` para `anthropic`, `google`, `xai` ou `auto` (detecta pela primeira chave presente no ambiente, nessa ordem).

Sem nenhuma chave definida — ou com a flag `--sem-ia` — o pipeline roda normalmente só com as camadas determinísticas; falha de API também não interrompe a execução, o caso cai na fila humana.

### Outras opções de execução

```bash
python run.py --dados ./agosto --saida ./out_agosto
python run.py --config ./config/regras.yaml
python run.py --sem-ia --dados data_pack_estresse --saida out_estresse
```

O processo retorna `0` quando as invariantes aritméticas fecham e `1` quando elas falham. Uma execução verde prova conservação de valores; não prova que todo vínculo está semanticamente correto. Casos de menor evidência continuam na fila humana.

### Pacotes de dados para teste

| Pasta | Uso |
|---|---|
| `data_pack/` | amostra principal de julho/2026 |
| `data_pack_estresse/` | casos adversariais do pipeline |

### Troubleshooting local

**O Streamlit não abre:** confirme que o ambiente virtual está ativo e rode
`streamlit run demo.py --server.port 8501` dentro da pasta do projeto.

**A porta está ocupada:** use outra porta, por exemplo
`streamlit run demo.py --server.port 8502`.

**A aplicação informa que não encontrou dados:** não envie arquivos para usar o
data pack de exemplo ou verifique se os quatro arquivos enviados são CSV/TXT
legíveis, com os separadores esperados.

**A IA está desligada:** isso é esperado sem `.env` ou sem uma chave válida. O
modo determinístico continua funcionando; ative a chave somente depois de validar
o pipeline sem IA.

**A conferência de fechamento falhou:** não use os arquivos de saída. Consulte
`metricas.json`, corrija a entrada/configuração e execute novamente.

**Quero abrir o relatório HTML:** após `python run.py --sem-ia`, abra
`out/relatorio.html` no navegador. No macOS, também é possível usar
`open out/relatorio.html`.

## Saídas

Ao executar `python run.py --sem-ia`, tudo é gravado em `out/`. A pasta já vem
preenchida na entrega para permitir inspeção sem executar código:

| Arquivo | Uso |
|---|---|
| `relatorio.html` | resumo executivo, limites e alertas |
| `01_fila_conciliacao.csv` | fila priorizada para a analista |
| `02_baixas_propostas.csv` | layout genérico de propostas de baixa |
| `03_titulos_em_aberto.csv` | saldo, estado da cobrança e justificativa |
| `04_caixa_nao_aplicado.csv` | créditos sem título associado |
| `05_alertas.csv` | riscos com natureza, responsável e evidência |
| `metricas.json` | saúde, cobertura, drift e trilha da execução |

O cenário adversarial segue a mesma estrutura em `out_estresse/`. O relatório
visual abre diretamente no navegador pelo arquivo `relatorio.html` de cada pasta.

O deck pode ser recompilado de forma independente:

```bash
cd ppt
npm install
npm run build
npm run build:story
npm run build:case
```

- `VantaraConcilia_Barte.pptx`: versão técnica original revisada;
- `VantaraConcilia_Apresentacao_Ludica.pptx`: narrativa visual passo a passo para explicar problema, solução, arquitetura e piloto ao CTO.
- `VantaraConcilia_Solucao_Barte.pptx`: apresentação em duas partes — solução para a Vantara e núcleo reutilizável para a Barte e outros clientes.

Os CSVs usam `;`, vírgula decimal e UTF-8 com BOM para abrir no Excel pt-BR. `02_baixas_propostas.csv` **não é ainda um arquivo homologado de importação do Protheus**. O layout do importador precisa ser confirmado com o TI; os identificadores bancários originais, inclusive zeros à esquerda, são preservados para essa adaptação.

## Resultado reproduzido no data pack

Execução determinística verificada:

```text
17 títulos                           R$ 416.150,50
15 créditos                          R$ 315.808,50
14/15 créditos vinculados/propostos  cobertura 99,4%
8 propostas de alta confiança        R$ 152.880,00 (48,4% dos créditos)
6 casos para confirmação humana      R$ 161.078,50
1 crédito sem título                 R$   1.850,00
```

Saldo em aberto ao final da simulação:

| Estado | Valor | Leitura correta |
|---|---:|---|
| Possível duplicidade entre ERPs | R$ 31.250,00 | suspender cobrança e validar documentos |
| Saldo de pagamento parcial | R$ 62.500,00 | fato suportado pelo identificador bancário |
| Sem recebimento no extrato analisado | R$ 8.120,00 | verificar outras contas/baixas; não prova inadimplência |

O data pack contém somente uma das quatro contas bancárias. Por isso o protótipo não chama R$ 8.120,00 de “inadimplência de fato”.

Alertas não são perdas:

| Natureza | Valor | Significado |
|---|---:|---|
| Perda confirmada e materializada | R$ 0,00 | nenhuma perda é comprovada pelo data pack |
| Exposição potencial | R$ 50.528,00 | possível duplicidade AR + boleto AP ainda pagável |
| Sem controle verificável | R$ 34.117,82 | cobrança cujo anexo não foi fornecido |
| Valor indeterminado | — | entrega parcial sem valor unitário/condição comercial |

## Como o motor decide

O motor separa duas perguntas:

1. **Identidade:** de quem é o dinheiro?
2. **Valor:** por que o crédito difere do título?

A cascata de identidade roda da evidência forte para a fraca:

1. `nosso_numero` no campo bancário;
2. CNPJ explícito no histórico;
3. nome completo ou truncado;
4. IA sobre uma lista fechada de candidatos;
5. valor único, sempre com confirmação humana.

As classificações de retenção e mora são **hipóteses aritméticas**. No piloto, mesmo quando a conta fecha, ambas exigem confirmação documental da controladoria. O mesmo vale para qualquer decisão tomada por IA.

### Estados operacionais

- `AUTO_APLICAR`: alta confiança para entrar no arquivo de propostas. Não há escrita automática; a Vantara continua sendo a autoridade de aplicação.
- `CONFIRMAR`: o vínculo é útil, mas exige validação humana.
- `INVESTIGAR`: a evidência não é suficiente e nenhum saldo é consumido.

## Onde a IA atua

No data pack de julho, regras determinísticas resolvem os casos de recebíveis. A IA é uma camada opcional e limitada para:

- desempatar nomes muito distorcidos entre candidatos já filtrados;
- extrair fatos de e-mails de AP fora dos padrões conhecidos;
- abster-se quando a evidência não permite decidir.

Guard-rails:

- recebe no máximo oito candidatos, nunca o universo inteiro;
- id fora da lista é descartado;
- confiança baixa vira abstenção;
- decisão de IA nunca vira proposta automática;
- falha de API não interrompe o pipeline.

O adapter envia ao provedor o histórico/candidatos ou o corpo do e-mail. Isso serve para o protótipo com dados sintéticos, mas **não está aprovado para dados reais**. Em produção, o modelo deve estar no ambiente aprovado pela Vantara ou a camada de IA permanece desligada.

## Arquitetura de produção proposta

O requisito do CTO é explícito: nada roda fora da infraestrutura da Vantara. VPN e TLS não mudam o local do processamento. A proposta para o piloto é:

```text
Barte: código-fonte único, CI, imagem assinada, versões e suporte
                         │
                         ▼
Vantara cloud: container isolado + bucket read-only + KMS + logs
                         │
                         ▼
          CSVs e relatório no ambiente da Vantara
```

- runtime dentro da conta cloud da Vantara;
- credenciais read-only e nenhuma rota de escrita para ERP;
- egress bloqueado por padrão;
- dados brutos e resultados permanecem na Vantara;
- somente telemetria sem dados financeiros pode sair;
- modelo de IA local/tenant-approved ou IA desligada;
- core reutilizável mantido como uma única imagem pela Barte;
- configuração da Vantara separada do core.

Isso é uma exceção à orientação padrão da Barte e precisa de aprovação interna. O compromisso não deve ser prometido ao CTO antes dessa aprovação.

## Controles e limites

### O que a conferência prova

As invariantes garantem:

```text
títulos iniciais = vínculos propostos + saldo remanescente
créditos bancários = propostas - retenções + mora + caixa não aplicado
                    + excedentes inexplicados + créditos em investigação
```

Elas detectam perda ou duplicação aritmética dentro da execução. Não detectam um vínculo semanticamente errado que preserve o mesmo valor.

Antes de produção ainda são necessários:

- golden set validado pela analista;
- precisão e taxa de revisão por tier;
- auditoria amostral diária;
- hash e completude dos arquivos de entrada;
- idempotência de lote;
- quarentena de linhas rejeitadas;
- teste de importação no layout real do Protheus;
- política de retenção, acesso e auditoria dos dados.

### Limitações conhecidas

1. Uma conta bancária foi fornecida; a Vantara possui quatro.
2. Anexos de NF, boleto e CT-e não fazem parte do data pack.
3. Coincidência de CNPJ, valor e vencimento entre ERPs é indício, não prova de duplicidade.
4. Retenção e mora dependem de documento e contrato não fornecidos.
5. O detector AP usa número de documento no histórico bancário; em produção deve cruzar CNAB/remessa e favorecido.
6. Agregação está limitada a quatro títulos entre quatorze candidatos.
7. Cartão/adquirência não está coberto.
8. Pagamento por terceiro ainda não é tratado.

## Plano de 30 dias

| Semana | Entrega | Critério de saída |
|---|---|---|
| 1 | exports read-only e golden set validado | ingestão completa e casos de julho assinados pela Controller |
| 2 | fila diária de recebíveis em shadow mode | nenhuma escrita, toda divergência com evidência e dono |
| 3 | medição por tier e bloqueio temporário de cobrança duvidosa | precisão, revisão e falso positivo conhecidos |
| 4 | proposta de baixa em volume e decisão de arquitetura | piloto aceito ou interrompido por métricas objetivas |

Metas a calibrar com dados reais, não com a amostra:

- 100% dos créditos classificados como proposto, confirmar, investigar ou caixa não aplicado;
- zero baixa e zero cobrança disparadas automaticamente no piloto;
- zero caso de baixa por retenção/mora sem documento aprovado;
- precisão por tier e tempo de revisão medidos diariamente;
- qualquer mudança de layout detectada antes da entrega da fila.

## Reuso versus configuração da Vantara

**Core Barte:** schema canônico, adapters, identidade, classificação de valor, travas, invariantes, filas, observabilidade e contrato de IA.

**Configuração Vantara:** layouts de exportação, contas, tolerâncias aprovadas, política fiscal/contratual, teto operacional, mapeamentos e destinatários.

O ativo reutilizável não é um script de Protheus: é o contrato auditável entre entrada suja, evidência, decisão e ação humana.

## Estrutura

```text
config/regras.yaml       política e travas
data_pack/               dados originais, sem alteração
data_pack_estresse/      casos adversariais
out/                     saídas oficiais do data pack de julho
out_estresse/            saídas dos casos adversariais
src/ingest/              adapters de origem
src/identidade/          resolução de entidade e possíveis duplicidades
src/ar/                   identidade + valor para recebíveis
src/ap/                   alertas secundários de contas a pagar
src/ia/                   adapter multi-provedor (google-genai, anthropic, openai) e guard-rails
src/saida/                CSVs e relatório HTML
tests/                    47 testes de negócio e limites
run.py                   CLI do pipeline (carrega .env automaticamente)
demo.py                  demo Streamlit — preparação, revisão humana e fechamento do caixa
prompts/                 transcripts, prompts e contexto de demonstração
.env.example             template de configuração (copiar para .env e preencher)
FLUXOS.md                fluxos funcionais, técnicos e de decisão
MANIFESTO_ENTREGA.md     inventário e regras do pacote de entrega
scripts/                 empacotamento reproduzível sem segredos
```

## Como gerar o ZIP de entrega

Na raiz desta pasta:

```bash
make pacote
```

O arquivo será criado em `dist/vantara-concilia-entrega.zip`, com a pasta
`vantara-concilia/` na raiz. O empacotador exclui `.env`, `.venv`, caches,
`node_modules` e execuções temporárias, mas mantém os data packs, as saídas
oficiais, o código, os testes, as configurações, os fluxos e as apresentações.

## Pendências de entrega do case

- `prompts/` contém registros de contexto e transcripts consolidados; eles não substituem um export bruto de uma ferramenta externa, caso esse export seja exigido formalmente.
- `MOMENTOS.md` é uma retrospectiva editada e não substitui um transcript bruto.
- O vídeo de até quatro minutos ainda precisa ser gravado.
- `MENSAGEM_CTO.md` é um rascunho coerente com a arquitetura proposta; falta inserir o link e os tempos do vídeo antes do envio.
