"""
Contas a pagar: o caso São Jorge e, igualmente importante, o NÃO-caso.

Um detector de pagamento duplicado que grita em toda segunda cobrança do mesmo
fornecedor é inútil — a equipe desliga na primeira semana. Por isso há tantos
testes de ausência de alerta quanto de presença.
"""

from __future__ import annotations

from decimal import Decimal


def _alerta(res, codigo):
    return [a for a in res.alertas if a.codigo == codigo]


# ---------------------------------------------------------------------------
# O caso
# ---------------------------------------------------------------------------

def test_detecta_reemissao_de_boleto_de_nota_ja_paga(execucao):
    """
    NF 88231 paga em 20/07 (18.900). Boleto reemitido de 19.278 vivo na caixa,
    vencendo 25/07. Terceiro pagamento duplicado do ano em formação.
    """
    res, _ = execucao
    a = _alerta(res, "AP-001")
    assert len(a) == 1
    assert a[0].valor_em_risco == Decimal("19278.00")
    assert a[0].severidade.value == "CRITICO"
    assert "BLOQUEAR PAGAMENTO E VALIDAR" in a[0].descricao


def test_normalizacao_de_documento_vence_o_zero_a_esquerda(execucao):
    """
    'NF 88231' e 'Nota fiscal 088231' são o mesmo documento. Para qualquer
    sistema são dois. Esta é a única razão pela qual o alerta existe.
    """
    res, _ = execucao
    a = _alerta(res, "AP-001")[0]
    evid = " ".join(str(e) for e in a.evidencias)
    assert "88231" in evid and "088231" in evid
    assert "mesmo documento" in evid


def test_detecta_gap_de_three_way_match(execucao):
    """
    'entregue parcialmente (12 de 15 volumes)' estava num 'Obs:' no fim de um
    e-mail de cobrança. A quantidade de volumes não prova a proporção monetária;
    o motor deve sinalizar a falha sem inventar um valor de perda.
    """
    res, _ = execucao
    a = _alerta(res, "AP-002")
    assert len(a) == 1
    assert a[0].valor_em_risco == Decimal("0")
    assert a[0].tipo_risco == "indeterminado"
    assert "12 de 15" in " ".join(str(e) for e in a[0].evidencias)
    assert "não é possível calcular" in " ".join(str(e) for e in a[0].evidencias)


def test_detecta_conferencia_contra_pagamento_agendado(execucao):
    """
    Em 19/07 a Camila lê 'pagou dia 20' — data que ainda não chegou — e conclui
    que a cobrança era de outra nota. Detectável comparando a data da mensagem
    com a data do débito no extrato.
    """
    res, _ = execucao
    a = _alerta(res, "AP-004")
    assert len(a) == 1
    assert "dia 20" in a[0].descricao
    evid = " ".join(str(e) for e in a[0].evidencias)
    assert "não podia confirmar liquidação" in evid
    assert "alguem confere" in evid        # a dúvida que ficou sem dono


def test_detecta_aprovacao_sem_evidencia(execucao):
    res, _ = execucao
    a = _alerta(res, "AP-003")
    assert len(a) == 1
    assert "acho que sim" in a[0].descricao


def test_cobranca_em_lote_sem_documento_eh_sinalizada(execucao):
    """
    46 CT-e num anexo que não veio no data pack. A solução declara a premissa
    em vez de fingir que conferiu.
    """
    res, _ = execucao
    a = _alerta(res, "AP-005")
    assert len(a) == 1
    assert a[0].tipo_risco == "sem_controle"
    assert "PREMISSA" in " ".join(str(e) for e in a[0].evidencias) or \
           "PREMISSA" in a[0].descricao


# ---------------------------------------------------------------------------
# O NÃO-caso: ausência de falso positivo
# ---------------------------------------------------------------------------

def test_nota_nova_do_mesmo_fornecedor_nao_gera_alerta(execucao_estresse):
    """
    O data pack de estresse tem a NF 88400 da MESMA São Jorge: documento
    diferente, valor diferente, nenhuma relação com a 88231.

    Se isso gerasse AP-001, o detector seria inútil — todo fornecedor recorrente
    viraria alerta e a equipe desligaria a ferramenta na primeira semana. Este
    teste é o que protege a taxa de falso positivo.
    """
    res, _ = execucao_estresse
    alertas_dup = _alerta(res, "AP-001") + _alerta(res, "AP-006")
    for a in alertas_dup:
        assert "88400" not in a.descricao
        assert "88400" not in " ".join(a.referencias)
    # e continua achando o caso verdadeiro
    assert len(_alerta(res, "AP-001")) == 1


def test_titulo_ja_liquidado_no_erp_nao_entra_no_pipeline(execucao_estresse):
    """
    FAT-2026-0350 vem com paid_flag=S. Consumi-lo como título aberto criaria um
    fantasma dentro do próprio pipeline.
    """
    res, _ = execucao_estresse
    assert "FAT-2026-0350" not in {t.documento for t in res.titulos}
