"""
Schema canônico.

Todo arquivo que entra no pipeline é traduzido para estas estruturas. Os
adapters de ingestão são a ÚNICA parte do código que sabe que existe Protheus,
Omie ou Itaú. A partir daqui, o motor não sabe de onde o dado veio — e é por
isso que ele serve para a próxima conta sem reescrita.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums de classificação
# ---------------------------------------------------------------------------

class TierIdentidade(str, Enum):
    """Como o pagador foi identificado. Ordem = força da evidência."""
    ID_BANCARIO = "ID_BANCARIO"
    CNPJ_TEXTO = "CNPJ_TEXTO"
    NOME_FORTE = "NOME_FORTE"
    NOME_PARCIAL = "NOME_PARCIAL"
    IA = "IA"
    SO_VALOR = "SO_VALOR"
    NENHUM = "NENHUM"


class ClasseValor(str, Enum):
    """Por que o valor que entrou não é igual ao valor de face do título."""
    EXATO = "EXATO"
    AGREGADO = "AGREGADO"
    RETENCAO = "RETENCAO"
    MORA = "MORA"
    PARCIAL = "PARCIAL"
    INEXPLICADO = "INEXPLICADO"


class Decisao(str, Enum):
    AUTO_APLICAR = "AUTO_APLICAR"
    CONFIRMAR = "CONFIRMAR"
    INVESTIGAR = "INVESTIGAR"


class Severidade(str, Enum):
    CRITICO = "CRITICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    INFO = "INFO"


# ---------------------------------------------------------------------------
# Entidades de negócio
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Entidade:
    """
    Um franqueado/cliente, unificado entre sistemas.

    `id` é derivado do CNPJ normalizado quando existe. É este objeto que não
    existe hoje na Vantara, e sua ausência permite possíveis duplicidades entre ERPs.
    """
    id: str
    cnpj: str | None
    nome_canonico: str
    nomes_vistos: tuple[str, ...] = ()
    fontes: tuple[str, ...] = ()

    @property
    def tem_cnpj(self) -> bool:
        return bool(self.cnpj)


@dataclass
class Titulo:
    """Um título a receber em aberto, de qualquer ERP."""
    id: str                      # identificador interno estável
    fonte: str                   # "protheus" | "omie" | ...
    entidade_id: str
    nome_original: str
    cnpj: str | None
    documento: str               # "NF 104521", "FAT-2026-0331"
    documento_normalizado: str   # "104521", "20260331"
    id_bancario: str | None      # nosso_numero, quando houver
    tipo: str                    # Produto | Royalty | Servico | Indefinido
    unidade: str | None
    emissao: date | None
    vencimento: date | None
    valor: Decimal
    saldo: Decimal               # valor - baixas aplicadas nesta execução
    bruto: dict[str, Any] = field(default_factory=dict)

    @property
    def quitado(self) -> bool:
        return self.saldo <= Decimal("0.01")


@dataclass
class MovimentoBancario:
    """Uma linha do extrato."""
    id: str
    data: date
    historico: str
    documento: str | None        # campo documento do extrato (nosso_numero)
    valor: Decimal
    tipo: str                    # "C" crédito | "D" débito
    conta: str
    bruto: dict[str, Any] = field(default_factory=dict)

    @property
    def is_credito(self) -> bool:
        return self.tipo.upper() == "C"


# ---------------------------------------------------------------------------
# Resultado de conciliação
# ---------------------------------------------------------------------------

@dataclass
class Evidencia:
    """
    Por que o motor concluiu o que concluiu.

    Existe para uma pergunta específica do CTO: "como eu audito isso?".
    Toda proposta de baixa carrega a sua. Nada é caixa-preta, inclusive o
    que a IA decidiu — nesse caso a justificativa dela entra aqui como texto.
    """
    regra: str
    detalhe: str
    campos: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.regra}: {self.detalhe}"


@dataclass
class Conciliacao:
    """Vínculo proposto entre um movimento bancário e um ou mais títulos."""
    movimento: MovimentoBancario
    titulos: list[Titulo]
    tier: TierIdentidade
    classe_valor: ClasseValor
    confianca: float
    decisao: Decisao
    valor_aplicado: Decimal
    diferenca: Decimal                      # banco - soma(títulos)
    evidencias: list[Evidencia] = field(default_factory=list)
    candidatos_descartados: int = 0
    acao_sugerida: str = ""
    observacao_analista: str = ""

    @property
    def valor_titulos(self) -> Decimal:
        return sum((t.valor for t in self.titulos), Decimal("0"))


@dataclass
class MovimentoOrfao:
    """Crédito que entrou e não achou título. Em finanças: caixa não aplicado."""
    movimento: MovimentoBancario
    motivo: str
    entidade_provavel: str | None
    candidatos_proximos: list[str] = field(default_factory=list)


@dataclass
class TituloEmAberto:
    """Título que sobrou sem pagamento ao fim da execução."""
    titulo: Titulo
    motivo: str
    severidade: Severidade
    e_cobravel: bool              # se False, cobrar é erro operacional


@dataclass
class Alerta:
    """
    Achado que não é conciliação e não vai para a fila da analista.

    Possível duplicidade, entidade divergente, risco de pagamento duplicado em AP. Vão para
    donos diferentes (cadastro/TI, contas a pagar) justamente porque tratar
    tudo como "exceção de conciliação" é o que enterra esses casos hoje.
    """
    codigo: str
    severidade: Severidade
    titulo_curto: str
    descricao: str
    valor_em_risco: Decimal
    destinatario: str             # quem resolve
    evidencias: list[Evidencia] = field(default_factory=list)
    referencias: list[str] = field(default_factory=list)

    # Agrupador de exposição. Dois alertas podem apontar para O MESMO dinheiro:
    # AP-001 (o boleto reemitido de uma nota já paga) e AP-004 (a conferência
    # que deixou esse boleto passar) descrevem R$ 19.278,00 uma vez, não duas.
    # Somar os dois inflaria o número que eu levo para a reunião — e número
    # inflado é o jeito mais rápido de perder credibilidade com um CTO que
    # confere.
    grupo_risco: str = ""

    # "confirmado": perda já materializada e comprovada documentalmente.
    # "potencial": valor que pode ficar exposto se o alerta não for tratado.
    # "sem_controle": valor que não pode ser verificado com os dados recebidos.
    # "indeterminado": falha de controle sem valor monetário defensável.
    tipo_risco: str = "potencial"

    @property
    def chave_risco(self) -> str:
        return self.grupo_risco or self.codigo


@dataclass
class CobrancaRecebida:
    """
    Uma cobrança que chegou na caixa de entrada de contas a pagar.

    Nota: a identidade do fornecedor aqui é o DOMÍNIO do e-mail, não o nome.
    Os dois e-mails da São Jorge vêm de remetentes diferentes
    (financeiro@ e marcia.rocha@) do mesmo domínio. Em AP, o domínio é a
    identidade forte — nome de fornecedor em assinatura de e-mail é ruído.
    """
    id: str
    remetente: str
    dominio: str
    fornecedor: str
    recebido_em: date | None
    assunto: str
    corpo: str
    documento: str | None
    documento_normalizado: str
    valor_cobrado: Decimal | None
    valor_original: Decimal | None
    vencimento: date | None
    linha_digitavel: str | None
    pedido_compra: str | None
    anexos: list[str] = field(default_factory=list)
    # Enriquecimento semântico (IA, com fallback por palavra-chave)
    e_reemissao: bool = False
    entrega_parcial: str | None = None
    extraido_por: str = "regra"
    notas_extracao: list[str] = field(default_factory=list)

    @property
    def valor_efetivo(self) -> Decimal | None:
        return self.valor_cobrado if self.valor_cobrado is not None else self.valor_original


@dataclass
class MensagemAprovacao:
    """Uma linha da thread de aprovação (WhatsApp)."""
    quando: str
    area: str
    autor: str
    texto: str


@dataclass
class ResultadoExecucao:
    """O retorno completo de uma rodada do pipeline."""
    conciliacoes: list[Conciliacao] = field(default_factory=list)
    orfaos: list[MovimentoOrfao] = field(default_factory=list)
    em_aberto: list[TituloEmAberto] = field(default_factory=list)
    alertas: list[Alerta] = field(default_factory=list)
    entidades: dict[str, Entidade] = field(default_factory=dict)
    titulos: list[Titulo] = field(default_factory=list)
    movimentos: list[MovimentoBancario] = field(default_factory=list)
    metricas: dict[str, Any] = field(default_factory=dict)
    avisos_ingestao: list[str] = field(default_factory=list)
