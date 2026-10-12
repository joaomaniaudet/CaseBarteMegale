"""
Onde a solução quebra — e o que ela faz quando quebra.

Dois grupos:

  1. Casos adversariais (data_pack_estresse), construídos por mim depois de o
     motor estar funcionando no data pack real. A pergunta não é "passa nos
     dados que funcionam", é "se comporta bem nos que não funcionam".

  2. Guard-rails da camada de IA, testados com um cliente stub. Teste com stub
     é MELHOR que chamada real aqui: eu preciso provar o que acontece quando o
     modelo devolve um id que não existe, ou se absteve, ou respondeu com
     confiança baixa. Uma chamada real não produz esses casos sob demanda.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.canonico import ClasseValor, Decisao, TierIdentidade
from src.ia.cliente import ClienteIA, DecisaoIA, _extrair_json
from tests.conftest import conc_por_valor


# ===========================================================================
# 1. Casos adversariais
# ===========================================================================

def test_empate_entre_dois_clientes_nao_eh_resolvido_por_palpite(execucao_estresse):
    """
    'PIX RECEBIDO CENTRAL' 19.900 casa igualmente com 'Padoca Central' e
    'Padaria Central' — duas empresas, CNPJs diferentes, títulos de valor
    idêntico.

    O comportamento correto é RECUSAR. Escolher um dos dois seria dar baixa num
    franqueado e manter aberto o do outro, que é como se produz a cobrança
    indevida que o Head de Franquias relatou.
    """
    res, _ = execucao_estresse
    c = conc_por_valor(res, "19900.00")
    assert c.decisao == Decisao.INVESTIGAR
    assert c.valor_aplicado == Decimal("0")
    assert "AMBÍGUO" in c.observacao_analista
    assert "NF 104700" in c.observacao_analista and "NF 104701" in c.observacao_analista


def test_colisao_de_valor_em_deposito_cego_vira_investigacao(execucao_estresse):
    """
    Dois títulos de 4.321 e um 'DEPOSITO NAO IDENTIFICADO' de 4.321.

    É o modo de falha que ESCALA: o bônus de unicidade que torna o caso de
    5.670 aceitável desaparece quando há colisão — e com 1.900 títulos/mês a
    colisão deixa de ser exceção.
    """
    res, _ = execucao_estresse
    c = conc_por_valor(res, "4321.00")
    assert c.tier == TierIdentidade.SO_VALOR
    assert c.decisao == Decisao.INVESTIGAR
    assert c.valor_aplicado == Decimal("0")


def test_desconto_de_5pct_em_produto_nao_eh_tratado_como_retencao(execucao_estresse):
    """
    NF 104702 é PRODUTO, 10.000, e recebeu 9.500 — exatos 5%, a mesma fração do
    ISS do caso da NF 104571.

    Não há retenção de ISS em nota de produto. Se o motor explicasse qualquer
    desconto de 5% como retenção, ele quitaria títulos com saldo real em aberto
    — perdendo cobrança legítima. A checagem de TIPO é o que separa os dois.
    """
    res, _ = execucao_estresse
    c = conc_por_valor(res, "9500.00")
    assert c.classe_valor == ClasseValor.PARCIAL
    assert c.valor_aplicado == Decimal("9500.00")
    aberto = {e.titulo.documento: e for e in res.em_aberto}
    assert aberto["NF 104702"].titulo.saldo == Decimal("500.00")


def test_excesso_fora_da_formula_de_mora_nao_eh_automatico(execucao_estresse):
    """
    NF 104703: 20.000 vencido em 26/07, crédito de 21.000 em 27/07.
    Excesso de 5% contra 2,03% esperados por contrato (multa 2% + 1 dia de
    juros). Não é mora — é exceção, e vai para humano com a conta na mão.
    """
    res, _ = execucao_estresse
    c = conc_por_valor(res, "21000.00")
    assert c.classe_valor == ClasseValor.INEXPLICADO
    assert c.decisao != Decisao.AUTO_APLICAR
    assert c.valor_aplicado == Decimal("0")
    # mas o pagador foi identificado: a analista não recebe um órfão cego
    assert c.tier == TierIdentidade.NOME_FORTE


def test_nome_muito_abreviado_vira_orfao_sem_ia(execucao_estresse):
    """
    'PIX RECEBIDO SBR EXPRESS DLVRY' 8.624 contra 'Sabor Express Delivery ME'
    (Serviço, 8.800, 2% de ISS retido).

    Só 1 de 3 tokens casa, e o valor não é exato — logo nem o passe de nome nem
    o de só-valor pegam. Sem IA, isso é um órfão. ESTE é o caso que justifica a
    camada de IA: não aumentar a cobertura do que já funciona, mas recuperar o
    que a regra perde por completo.
    """
    res, _ = execucao_estresse
    orfaos = {o.movimento.valor for o in res.orfaos}
    assert Decimal("8624.00") in orfaos


def test_linha_corrompida_nao_derruba_o_pipeline(execucao_estresse):
    """Export de ERP vem com linha torta. O pipeline avisa e continua."""
    res, _ = execucao_estresse
    avisos = " ".join(res.avisos_ingestao)
    assert "valor inválido/zerado" in avisos
    assert res.metricas["saude"]["conferencia_de_fechamento_ok"]


def test_data_em_formato_errado_para_a_fonte_ainda_eh_lida(execucao_estresse):
    """
    FAT-2026-0351 veio com data pt-BR num arquivo Omie que usa ISO. Parser
    tolerante a formato evita perder um título por causa de quem exportou.
    """
    res, _ = execucao_estresse
    t = next(t for t in res.titulos if t.documento == "FAT-2026-0351")
    assert t.vencimento is not None and t.vencimento.isoformat() == "2026-07-30"


def test_conferencia_fecha_tambem_no_pack_adversarial(execucao_estresse):
    """A invariante tem que valer nos dados ruins, não só nos bons."""
    res, _ = execucao_estresse
    for c in res.metricas["saude"]["checagens"]:
        assert Decimal(c["diferenca"]) == 0, c


# ===========================================================================
# 2. Guard-rails da camada de IA
# ===========================================================================

class StubIA(ClienteIA):
    """
    Cliente de IA falso. Permite testar cada resposta patológica do modelo sem
    rede e sem chave de API.
    """

    def __init__(self, cfg, resposta):
        super().__init__(cfg, habilitada=False)
        self._resposta = resposta
        self.habilitada = True
        self._cliente = object()      # finge SDK presente
        self.usar_cache = False

    def _chamar(self, sistema, prompt, schema_hint):
        return self._resposta


CANDIDATOS = [
    {"titulo_id": "protheus:104521", "cliente": "Padaria Vila Nova Ltda",
     "documento": "NF 104521", "saldo": "18.450,00"},
    {"titulo_id": "omie:FAT-2026-0332", "cliente": "NORTE PANIFICADOS EIRELI",
     "documento": "FAT-2026-0332", "saldo": "12.980,00"},
]


def _chamar(cfg, resposta):
    return StubIA(cfg, resposta).escolher_titulo(
        historico="PIX RECEBIDO ALGUMA COISA",
        valor_credito="18.450,00",
        data_credito="10/07/2026",
        candidatos=CANDIDATOS,
    )


def test_ia_que_inventa_id_tem_a_resposta_descartada(cfg):
    """
    O guard-rail mais importante. O modelo recebe uma lista FECHADA; qualquer
    id fora dela é resposta inválida, não 'quase certa'. Alucinação fica
    impedida por construção — não por pedido no prompt.
    """
    d = _chamar(cfg, {"titulo_id": "protheus:999999", "confianca": 0.98,
                      "justificativa": "tenho certeza"})
    assert d.escolha is None
    assert d.absteve is True
    assert d.erro == "id_fora_da_lista"


def test_ia_pode_se_abster(cfg):
    """Abstenção é resposta de primeira classe. Modelo obrigado a escolher
    sempre escolhe — e é assim que nasce baixa errada."""
    d = _chamar(cfg, {"titulo_id": None, "confianca": 0.2,
                      "justificativa": "histórico não permite decidir"})
    assert d.absteve is True and d.escolha is None


def test_confianca_abaixo_do_minimo_volta_para_fila_humana(cfg):
    d = _chamar(cfg, {"titulo_id": "protheus:104521", "confianca": 0.35,
                      "justificativa": "chute"})
    assert d.absteve is True
    assert "abaixo do mínimo" in d.justificativa


def test_resposta_valida_eh_aceita_com_teto_de_confianca(cfg):
    d = _chamar(cfg, {"titulo_id": "protheus:104521", "confianca": 0.93,
                      "justificativa": "nome e valor compatíveis"})
    assert d.escolha == "protheus:104521"
    assert d.absteve is False


def test_decisao_de_ia_nunca_eh_automatica(cfg):
    """
    Política, não capacidade: a trava `bloquear_se_decidido_por_ia` está no
    config justamente para o CTO poder auditar o limite do automático sem ler
    código. IA propõe, humano aplica.
    """
    assert cfg["travas_auto_aplicar"]["bloquear_se_decidido_por_ia"] is True
    assert cfg["confianca_identidade"]["IA"] < cfg["decisao"]["auto_aplicar_min"]


def test_falha_de_rede_nao_derruba_o_pipeline(cfg):
    """IA fora do ar devolve abstenção, não exceção."""
    d = _chamar(cfg, None)
    assert d.absteve is True
    assert d.erro is not None


@pytest.mark.parametrize("bruto", [
    '{"titulo_id": "x", "confianca": 0.9}',
    '```json\n{"titulo_id": "x", "confianca": 0.9}\n```',
    'Claro! Aqui está:\n{"titulo_id": "x", "confianca": 0.9}\nEspero ter ajudado.',
])
def test_parser_tolera_variacao_de_formatacao_do_modelo(bruto):
    """
    Não é frescura: é a diferença entre o pipeline sobreviver a uma variação de
    formatação e quebrar numa segunda-feira de fechamento.
    """
    assert _extrair_json(bruto)["titulo_id"] == "x"


def test_pipeline_roda_sem_chave_de_api(cfg):
    """
    Requisito de produção: um pipeline financeiro que para porque a API caiu
    não entra em produção. Sem chave, a IA se desliga e registra o motivo.
    """
    import os
    chave = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        ia = ClienteIA(cfg, habilitada=True)
        assert ia.ativa is False
        assert "ANTHROPIC_API_KEY" in (ia.motivo_desligada or "")
    finally:
        if chave:
            os.environ["ANTHROPIC_API_KEY"] = chave
