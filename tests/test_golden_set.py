"""
Golden set: o comportamento esperado de CADA crédito do data pack de julho.

Isto não é cobertura de código. É um contrato sobre decisões de negócio.

Cada teste abaixo trava um caso que eu identifiquei lendo o data pack à mão
ANTES de escrever o motor. Se um refactor mudar a classificação da retenção de
retenção ou liberar cobrança durante validação de duplicidade, o teste quebra com o nome do caso
no output — e não em um `assert len(x) == 14` que não diz nada.

É também a resposta à pergunta "como a operação descobre antes do cliente":
estes testes rodam no CI a cada mudança, e a conferência de fechamento roda em
toda execução sobre os dados daquele dia.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.canonico import ClasseValor, Decisao, TierIdentidade
from tests.conftest import conc_por_valor


# ---------------------------------------------------------------------------
# Integridade geral
# ---------------------------------------------------------------------------

def test_conferencia_de_fechamento_fecha_ao_centavo(execucao):
    """A invariante mais importante: nenhum centavo perdido ou duplicado."""
    res, _ = execucao
    saude = res.metricas["saude"]
    assert saude["conferencia_de_fechamento_ok"], saude["checagens"]
    for c in saude["checagens"]:
        assert Decimal(c["diferenca"]) == 0, f"{c['nome']}: {c}"


def test_ingestao_le_os_dois_formatos_sem_limpeza_manual(execucao):
    res, _ = execucao
    assert len([t for t in res.titulos if t.fonte == "protheus"]) == 12
    assert len([t for t in res.titulos if t.fonte == "omie"]) == 5
    assert len(res.movimentos) == 18
    # valor pt-BR com vírgula e ISO com ponto no mesmo pipeline
    assert sum(t.valor for t in res.titulos) == Decimal("416150.50")


def test_todo_credito_tem_destino(execucao):
    """Nenhum crédito pode ficar sem classificação. Dinheiro sem destino é
    exatamente o que trava o fechamento hoje."""
    res, _ = execucao
    creditos = [m for m in res.movimentos if m.is_credito]
    assert len(res.conciliacoes) + len(res.orfaos) == len(creditos)


def test_fechamento_do_caixa_separa_proposta_de_analise_humana(execucao):
    res, _ = execucao
    fechamento = res.metricas["fechamento_caixa"]
    assert Decimal(fechamento["valor_caixa_validado_para_proposta"]) == Decimal("152880.00")
    assert Decimal(fechamento["valor_caixa_em_analise_humana"]) == Decimal("162928.50")
    assert Decimal(fechamento["valor_caixa_total"]) == Decimal("315808.50")
    assert (
        Decimal(fechamento["valor_caixa_validado_para_proposta"])
        + Decimal(fechamento["valor_caixa_em_analise_humana"])
        == Decimal(fechamento["valor_caixa_total"])
    )


def test_entidades_unificadas_entre_erps(execucao):
    """Grão Nobre e Bela Vista existem nos dois ERPs e viram UMA entidade."""
    res, _ = execucao
    por_cnpj = {e.cnpj: e for e in res.entidades.values() if e.cnpj}
    for cnpj in ("55666777000144", "22333444000155"):
        ent = por_cnpj[cnpj]
        assert len(ent.fontes) == 2, f"{cnpj} deveria aparecer em protheus e omie"
        assert len(ent.nomes_vistos) == 2, f"{cnpj} tem grafias distintas por fonte"


# ---------------------------------------------------------------------------
# Os sete modos de o valor não bater — um teste por caso real
# ---------------------------------------------------------------------------

def test_caso_boleto_registrado_eh_deterministico(execucao):
    """NF 104521: nosso_numero no extrato. Evidência máxima, baixa automática."""
    res, _ = execucao
    c = conc_por_valor(res, "18450.00")
    assert c.tier == TierIdentidade.ID_BANCARIO
    assert c.classe_valor == ClasseValor.EXATO
    assert c.decisao == Decisao.AUTO_APLICAR
    assert c.titulos[0].documento == "NF 104521"


def test_caso_pix_sem_identificador_casa_por_nome_truncado(execucao):
    """
    NF 104522 (royalty, 3.200): 'PIX RECEBIDO PADARIA VILA NOVA LT'.

    O 'LT' é um 'LTDA' cortado em 32 caracteres. Travar este caso importa
    porque foi exatamente aqui que minha primeira versão errou: contava o
    fragmento como token não casado e rebaixava o match para nome fraco.
    """
    res, _ = execucao
    c = conc_por_valor(res, "3200.00")
    assert c.tier == TierIdentidade.NOME_FORTE
    assert c.titulos[0].documento == "NF 104522"


def test_caso_um_credito_quitando_dois_titulos(execucao):
    """TED de 47.630,50 = NF 104533 (42.780,50) + NF 104588 (4.850,00)."""
    res, _ = execucao
    c = conc_por_valor(res, "47630.50")
    assert c.classe_valor == ClasseValor.AGREGADO
    assert {t.documento for t in c.titulos} == {"NF 104533", "NF 104588"}
    assert sum(t.valor for t in c.titulos) == Decimal("47630.50")
    # Agregação nunca é automática: um crédito para N títulos merece um olhar
    assert c.decisao == Decisao.CONFIRMAR


def test_caso_pagamento_parcial_preserva_o_saldo(execucao):
    """
    NF 104560: 125.000 de face, 62.500 recebidos.

    O risco aqui é baixa total, que apagaria 62.500 de cobrança legítima.
    """
    res, _ = execucao
    c = conc_por_valor(res, "62500.00")
    assert c.classe_valor == ClasseValor.PARCIAL
    assert c.valor_aplicado == Decimal("62500.00")
    aberto = {e.titulo.documento: e for e in res.em_aberto}
    assert aberto["NF 104560"].titulo.saldo == Decimal("62500.00")
    assert aberto["NF 104560"].e_cobravel is True


def test_caso_retencao_de_iss_exige_confirmacao_documental(execucao):
    """
    NF 104571 (Serviço, 15.600) -> 14.820 recebidos. Exatamente 5% de ISS.

    A aritmética é compatível com ISS, mas o data pack não traz nota, guia ou
    política fiscal. A hipótese deve ir para confirmação humana.
    """
    res, _ = execucao
    c = conc_por_valor(res, "14820.00")
    assert c.classe_valor == ClasseValor.RETENCAO
    assert c.decisao == Decisao.CONFIRMAR
    assert c.valor_aplicado == Decimal("15600.00")
    assert c.diferenca == Decimal("-780.00")
    assert "ISS 5%" in " ".join(str(e) for e in c.evidencias)
    assert "NF 104571" not in {e.titulo.documento for e in res.em_aberto}


def test_caso_mora_exige_confirmacao_do_contrato(execucao):
    """NF 104601: diferença compatível com multa, mas contrato não foi fornecido."""
    res, _ = execucao
    c = conc_por_valor(res, "23358.00")
    assert c.classe_valor == ClasseValor.MORA
    assert c.decisao == Decisao.CONFIRMAR
    assert c.valor_aplicado == Decimal("22900.00")
    assert c.diferenca == Decimal("458.00")
    assert "NF 104601" not in {e.titulo.documento for e in res.em_aberto}


def test_caso_cnpj_cru_no_historico(execucao):
    """'PIX RECEBIDO 11222333000166' -> CNPJ sem máscara em texto livre."""
    res, _ = execucao
    c = conc_por_valor(res, "7430.00")
    assert c.tier == TierIdentidade.CNPJ_TEXTO
    assert c.titulos[0].documento == "NF 104595"


def test_caso_deposito_nao_identificado_nunca_eh_automatico(execucao):
    """
    'DEPOSITO NAO IDENTIFICADO' 5.670 -> FAT-2026-0340, só por valor.

    É o '8% sem identificação' da Vantara. Casa, mas por eliminação — e por
    política nunca roda sozinho, mesmo sendo o único título com esse valor.
    """
    res, _ = execucao
    c = conc_por_valor(res, "5670.00")
    assert c.tier == TierIdentidade.SO_VALOR
    assert c.decisao != Decisao.AUTO_APLICAR
    assert c.titulos[0].documento == "FAT-2026-0340"


def test_caso_credito_sem_titulo_vira_caixa_nao_aplicado(execucao):
    """
    PIX de 1.850 da Padaria Vila Nova sem título correspondente.

    O importante não é só não casar: é identificar o PAGADOR mesmo assim. 'R$
    1.850 da Padaria Vila Nova' se resolve com um telefonema; 'crédito não
    identificado' fica na planilha para sempre.
    """
    res, _ = execucao
    assert len(res.orfaos) == 1
    o = res.orfaos[0]
    assert o.movimento.valor == Decimal("1850.00")
    assert o.entidade_provavel and "Padaria Vila Nova" in o.entidade_provavel


# ---------------------------------------------------------------------------
# Possível duplicidade entre ERPs — achado que exige validação
# ---------------------------------------------------------------------------

def test_possivel_duplicidade_suspende_cobranca_para_validacao(execucao):
    """
    Grão Nobre: 31.250 aberto no Protheus E no Omie, mesmo vencimento.
    O franqueado pagou uma vez. A cobrança do possível gêmeo deve ser suspensa,
    mas os dados não autorizam declarar a dívida definitivamente duplicada.
    """
    res, _ = execucao
    cad = [a for a in res.alertas if a.codigo == "CAD-001"]
    assert len(cad) == 1
    assert cad[0].valor_em_risco == Decimal("31250.00")
    assert cad[0].tipo_risco == "potencial"
    assert "Cadastro" in cad[0].destinatario    # não vai para a fila de conciliação

    gemeo = next(e for e in res.em_aberto if e.titulo.documento == "FAT-2026-0331")
    assert gemeo.e_cobravel is False
    assert "SUSPENDER COBRANÇA" in gemeo.motivo
    assert "validar" in gemeo.motivo


def test_pagamento_do_grao_nobre_casa_com_o_titulo_do_protheus(execucao):
    """
    O crédito de 31.250 veio com nosso_numero, que só o título do Protheus tem.
    Travar isso garante que a ordem dos passes (evidência forte primeiro) não
    seja invertida por um refactor.
    """
    res, _ = execucao
    c = conc_por_valor(res, "31250.00")
    assert c.tier == TierIdentidade.ID_BANCARIO
    assert c.titulos[0].fonte == "protheus"


def test_decomposicao_nao_promove_ausencia_de_match_a_inadimplencia(execucao):
    """O extrato cobre uma conta entre quatro; ausência de match não prova atraso."""
    res, _ = execucao
    d = res.metricas["decomposicao_do_gap"]
    assert Decimal(d["em_validacao_possivel_duplicidade"]) == Decimal("31250.00")
    assert Decimal(d["saldo_de_pagamento_parcial"]) == Decimal("62500.00")
    assert Decimal(d["sem_recebimento_identificado_no_extrato"]) == Decimal("8120.00")
    assert d["percentual_sem_recebimento_identificado"] < 0.10
    assert "não prova inadimplência" in d["leitura"]


# ---------------------------------------------------------------------------
# Governança: o que NÃO roda sozinho
# ---------------------------------------------------------------------------

def test_baixas_propostas_contem_apenas_o_que_passou_nas_travas(execucao):
    import csv
    res, arquivos = execucao
    with open(arquivos["baixas_propostas"], encoding="utf-8-sig") as fh:
        linhas = list(csv.DictReader(fh, delimiter=";"))
    auto = [c for c in res.conciliacoes if c.decisao == Decisao.AUTO_APLICAR]
    assert len(linhas) == sum(len(c.titulos) for c in auto)
    for l in linhas:
        assert float(l["confianca"]) >= 0.90
        assert l["tier_identidade"] not in ("SO_VALOR", "IA")
        assert l["evidencia"], "toda baixa proposta precisa carregar evidência"

    boleto = next(l for l in linhas if l["documento"] == "NF 104521")
    assert boleto["nosso_numero"] == "000012345678"
    assert boleto["doc_bancario"] == "000012345678"


def test_nenhuma_escrita_em_sistema_de_origem(execucao):
    """
    O TI da Vantara liberou só leitura no Protheus por 90 dias.

    A solução respeita isso por construção: a saída é arquivo de proposta, e
    nada no código tem caminho de escrita para um ERP. Este teste existe para
    que isso continue verdade depois do próximo refactor.
    """
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "src"
    proibidos = ("pyodbc", "cx_Oracle", "sqlalchemy", "requests.post",
                 "psycopg2", "pymssql", "TOTVSRest")
    for arq in src.rglob("*.py"):
        texto = arq.read_text(encoding="utf-8")
        for p in proibidos:
            assert p not in texto, f"{arq.name} referencia {p}: possível caminho de escrita"


def test_valor_acima_do_teto_exige_humano(execucao):
    """NF 104560 tem 125.000 de face, acima do teto automático de 100.000."""
    res, _ = execucao
    c = conc_por_valor(res, "62500.00")
    assert c.decisao == Decisao.CONFIRMAR
    assert any("teto automático" in str(e) for e in c.evidencias)


def test_risco_nao_eh_contado_duas_vezes(execucao):
    """
    AP-001 e AP-004 descrevem o MESMO boleto de 19.278. Somar os dois daria
    38.556 de risco inexistente — número inflado que um CTO desmonta na hora.
    """
    res, _ = execucao
    alr = res.metricas["alertas"]
    assert Decimal(alr["valor_em_risco_confirmado"]) == Decimal("0.00")
    assert Decimal(alr["valor_exposicao_potencial"]) == Decimal("50528.00")
    assert alr["grupos_de_exposicao"] < alr["total"]
    soma_crua = sum(a.valor_em_risco for a in res.alertas)
    assert soma_crua > Decimal(alr["valor_exposicao_potencial"])
