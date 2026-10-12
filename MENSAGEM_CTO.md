# Rascunho de mensagem ao CTO

> Não enviar antes de substituir os campos entre colchetes e publicar o vídeo.

**Assunto:** Decisão técnica para o piloto read-only de recebíveis da Vantara

Olá, Manuel, tudo bem?

Revisei os arquivos de julho com uma pergunta anterior à automação: quais vínculos entre títulos, clientes e entradas bancárias conseguimos explicar e auditar sem escrever no Protheus?

O protótipo lê as exportações atuais de Protheus, Omie e Itaú e devolve uma fila para a analista. Ele não baixa títulos, não dispara cobrança e não transforma diferença de valor em decisão automática. Retenção, mora, depósito não identificado e possível duplicidade entre ERPs ficam explicitamente sujeitos a validação.

No vídeo de [link], sugiro observar:

- [00:XX] entrada dos quatro arquivos e geração da fila;
- [01:XX] diferença entre evidência forte e hipótese;
- [02:XX] suspensão temporária de uma cobrança possivelmente duplicada;
- [03:XX] limites da conferência ao centavo e arquitetura do piloto.

Para respeitar sua premissa de que nada rode fora da infraestrutura da Vantara, proponho discutir um runtime isolado na conta cloud da Vantara: container assinado pela Barte, acesso somente de leitura, dados protegidos pelas chaves da Vantara e sem saída de dados financeiros. Esse desenho é uma exceção à orientação padrão da Barte e ainda depende de aprovação interna; não quero apresentá-lo como compromisso fechado antes de validarmos juntos.

Gostaria de usar nossa reunião para decidir três pontos:

1. quais exports read-only podem ser disponibilizados diariamente;
2. qual ambiente da Vantara pode receber um piloto isolado sem acesso de escrita;
3. quem da Controladoria valida o golden set e as políticas de retenção/mora.

Minha proposta é operar quatro semanas em shadow mode: a ferramenta sugere, a equipe valida e nós medimos precisão, falso positivo e tempo de revisão. Só depois desses dados discutimos qualquer automação adicional.

Esse recorte atende às suas premissas de controle e segurança? Se houver um requisito que inviabilize o desenho antes da reunião, prefiro incorporá-lo agora.

Um abraço,

[Seu nome]  
Client Partner — Barte AI Services
