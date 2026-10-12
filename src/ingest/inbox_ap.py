"""
Adapter da caixa de entrada de contas a pagar.

Este é o arquivo mais difícil do data pack e o mais valioso. Não tem schema:
é e-mail em prosa, com anexo que não veio, valor escrito de três formas,
número de documento com e sem zero à esquerda, vencimento às vezes relativo
("5 dias após o recebimento conforme contrato") e uma thread de WhatsApp onde
a aprovação de fato acontece.

A estratégia é em duas camadas:

  CAMADA 1 — regra (aqui): o que tem forma reconhecível. Valor, data, número
  de documento, linha digitável, pedido de compra, domínio do remetente.
  Determinístico, grátis, auditável.

  CAMADA 2 — IA (src/ia/extracao_ap.py): o que só existe em linguagem.
  "o pedido PC 4471 foi entregue parcialmente (12 de 15 volumes)" não tem
  campo. "Reenvio o boleto atualizado" é uma intenção, não um dado.

Camada 1 roda sempre. Camada 2 é opcional e tem fallback por palavra-chave,
para que o pipeline nunca dependa de uma chamada de API para funcionar.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from ..canonico import CobrancaRecebida, MensagemAprovacao
from ..normalizacao import (
    extrair_linha_digitavel,
    limpar_texto,
    normalizar_documento,
    parse_data,
    parse_valor,
)
from .base import ler_texto

FONTE = "inbox_ap"

_SEP_BLOCO = re.compile(r"^-{3,}\s*(.+?)\s*-{3,}\s*$", re.MULTILINE)

_RE_DE = re.compile(r"^De:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_RE_DATA = re.compile(r"^Data:\s*(\d{2}/\d{2}/\d{4})", re.MULTILINE | re.IGNORECASE)
_RE_ASSUNTO = re.compile(r"^Assunto:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_RE_ANEXO = re.compile(r"\[anexo:\s*([^\]]+)\]", re.IGNORECASE)

# Dinheiro: 'R$ 18.900,00', '18.900,00', 'R$ 34.117,82'
_RE_DINHEIRO = re.compile(r"R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
# Documento fiscal: 'NF 88231', 'Nota fiscal 088231', 'NF-e 104521'
_RE_DOC = re.compile(
    r"\b(?:NFS?-?e?|NOTA\s+FISCAL|NOTA|FATURA|FAT)\b[\s:nº°.]*(\d{3,})",
    re.IGNORECASE,
)
# Pedido de compra: 'PC 4471', 'pedido 4471'
_RE_PC = re.compile(r"\b(?:PC|PEDIDO(?:\s+DE\s+COMPRA)?)\b[\s:nº°.]*(\d{2,})", re.IGNORECASE)
# Vencimento: 'vencimento 20/07', '(venc. 25/07/2026)', 'venc 25/07/2026'
# Sem \b depois do ponto: '.' seguido de ' ' não é fronteira de palavra, e era
# exatamente isso que fazia '(venc. 25/07/2026)' do e-mail 2 passar batido.
_RE_VENC = re.compile(
    r"\bvenc(?:imento)?\.?[\s:]*(\d{2}/\d{2}(?:/\d{4})?)",
    re.IGNORECASE,
)
# Anexo citado como fonte de N documentos: 'planilha com as 46 CT-e'
_RE_LOTE_ANEXO = re.compile(
    r"(\d{1,4})\s+(?:CT-?e|CTE|NFS?-?e|notas?|faturas?|t[ií]tulos?|documentos?)",
    re.IGNORECASE,
)
# WhatsApp: '[06/07 11:02] Compras - Rafael: texto'
_RE_WPP = re.compile(
    r"^\[(\d{2}/\d{2}(?:\s+\d{2}:\d{2})?)\]\s*([^:]+?):\s*(.+)$",
    re.MULTILINE,
)

PALAVRAS_REEMISSAO = (
    "reenvio", "reenviando", "boleto atualizado", "valor atualizado",
    "nao identificamos o pagamento", "não identificamos o pagamento",
    "cobranca em aberto", "cobrança em aberto", "segunda via", "2a via",
    "atualizado com juros", "em aberto",
)
PALAVRAS_ENTREGA_PARCIAL = (
    "entregue parcialmente", "entrega parcial", "parcialmente",
    "restante sai", "volumes", "saldo do pedido", "entrega pendente",
)


def _dominio(remetente: str) -> str:
    m = re.search(r"@([\w.\-]+)", remetente or "")
    return m.group(1).lower() if m else "desconhecido"


def _nome_fornecedor(dominio: str) -> str:
    """Nome de exibição derivado do domínio. Melhorado pela IA quando ativa."""
    base = dominio.split(".")[0]
    return base.upper()


def _valores_rotulados(corpo: str) -> tuple[Decimal | None, Decimal | None, list[str]]:
    """
    Separa 'valor original' de 'valor atualizado'.

    Essa distinção é o que diferencia "o fornecedor está cobrando de novo a
    mesma nota" de "chegou uma nota nova". Sem ela, o e-mail 2 da São Jorge
    parece uma cobrança legítima de R$ 19.278,00.
    """
    notas: list[str] = []
    atualizado: Decimal | None = None
    original: Decimal | None = None

    for m in _RE_DINHEIRO.finditer(corpo):
        valor = parse_valor(m.group(1))
        contexto = limpar_texto(corpo[max(0, m.start() - 40): m.start()])
        if "ATUALIZADO" in contexto and atualizado is None:
            atualizado = valor
        elif "ORIGINAL" in contexto and original is None:
            original = valor

    if atualizado is None and original is None:
        todos = [parse_valor(m.group(1)) for m in _RE_DINHEIRO.finditer(corpo)]
        todos = [v for v in todos if v > 0]
        if todos:
            atualizado = max(todos)
            if len(todos) > 1:
                notas.append(
                    f"{len(todos)} valores no corpo; usado o maior "
                    f"({atualizado}) como valor cobrado"
                )
    return atualizado, original, notas


def _vencimento(corpo: str, referencia: date | None) -> tuple[date | None, list[str]]:
    """
    Pega a ÚLTIMA data de vencimento citada (nos e-mails de reemissão, a data
    nova vem depois da antiga). Completa o ano quando o e-mail escreve só
    'vencimento 20/07'.
    """
    notas: list[str] = []
    achados = _RE_VENC.findall(corpo)
    if not achados:
        if re.search(r"\bvenc", corpo, re.IGNORECASE):
            notas.append(
                "vencimento citado em condição contratual, sem data explícita "
                "— exige confirmação humana"
            )
        return None, notas

    bruto = achados[-1]
    if len(bruto) == 5 and referencia:                  # 'dd/mm'
        bruto = f"{bruto}/{referencia.year}"
        notas.append("ano do vencimento inferido do ano do e-mail")
    return parse_data(bruto), notas


class IngestorInboxAP:
    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)

    def carregar(self) -> tuple[list[CobrancaRecebida], list[MensagemAprovacao], list[str]]:
        texto, enc = ler_texto(self.caminho)
        avisos: list[str] = []
        if enc != "utf-8":
            avisos.append(f"{self.caminho.name}: lido como {enc}")

        cobrancas: list[CobrancaRecebida] = []
        aprovacoes: list[MensagemAprovacao] = []

        # Quebra o arquivo pelos marcadores '--- E-MAIL 1 ---' / '--- TRECHO ... ---'
        marcadores = list(_SEP_BLOCO.finditer(texto))
        for i, m in enumerate(marcadores):
            rotulo = limpar_texto(m.group(1))
            inicio = m.end()
            fim = marcadores[i + 1].start() if i + 1 < len(marcadores) else len(texto)
            bloco = texto[inicio:fim].strip()
            if not bloco:
                continue

            if "WHATSAPP" in rotulo or "APROVAC" in rotulo:
                aprovacoes.extend(self._parse_aprovacoes(bloco))
            elif "MAIL" in rotulo:
                cob = self._parse_email(bloco, rotulo)
                if cob:
                    cobrancas.append(cob)
                else:
                    avisos.append(f"{self.caminho.name}: bloco '{rotulo}' sem campos de e-mail")

        if not cobrancas:
            avisos.append(f"{self.caminho.name}: nenhuma cobrança reconhecida")
        return cobrancas, aprovacoes, avisos

    # ------------------------------------------------------------------
    def _parse_email(self, bloco: str, rotulo: str) -> CobrancaRecebida | None:
        m_de = _RE_DE.search(bloco)
        if not m_de:
            return None

        remetente = m_de.group(1).strip()
        dominio = _dominio(remetente)
        m_data = _RE_DATA.search(bloco)
        recebido = parse_data(m_data.group(1)) if m_data else None
        assunto = (_RE_ASSUNTO.search(bloco).group(1).strip()
                   if _RE_ASSUNTO.search(bloco) else "")

        # Corpo = tudo depois do cabeçalho
        corte = max(
            (m.end() for m in (m_de, m_data, _RE_ASSUNTO.search(bloco)) if m),
            default=0,
        )
        corpo = bloco[corte:].strip()
        texto_busca = f"{assunto}\n{corpo}"

        valor_cobrado, valor_original, notas = _valores_rotulados(texto_busca)
        vencimento, notas_v = _vencimento(texto_busca, recebido)
        notas.extend(notas_v)

        m_doc = _RE_DOC.search(texto_busca)
        documento = m_doc.group(1) if m_doc else None
        if not documento:
            notas.append("nenhum número de documento fiscal identificado")
            m_lote = _RE_LOTE_ANEXO.search(texto_busca)
            if m_lote:
                notas.append(
                    f"cobrança em lote: {m_lote.group(1)} documentos citados, "
                    f"detalhe só no anexo (não incluído no data pack) — "
                    f"PREMISSA: tratado como 1 cobrança agregada, sem conferência "
                    f"item a item"
                )

        m_pc = _RE_PC.search(texto_busca)

        baixo = limpar_texto(texto_busca)
        e_reemissao = any(limpar_texto(p) in baixo for p in PALAVRAS_REEMISSAO)
        trecho_parcial = None
        for p in PALAVRAS_ENTREGA_PARCIAL:
            if limpar_texto(p) in baixo:
                trecho_parcial = self._trecho(corpo, p)
                break

        return CobrancaRecebida(
            id=f"{FONTE}:{rotulo.lower().replace(' ', '_')}",
            remetente=remetente,
            dominio=dominio,
            fornecedor=_nome_fornecedor(dominio),
            recebido_em=recebido,
            assunto=assunto,
            corpo=corpo,
            documento=documento,
            documento_normalizado=normalizar_documento(documento),
            valor_cobrado=valor_cobrado,
            valor_original=valor_original,
            vencimento=vencimento,
            linha_digitavel=extrair_linha_digitavel(texto_busca),
            pedido_compra=m_pc.group(1) if m_pc else None,
            anexos=_RE_ANEXO.findall(bloco),
            e_reemissao=e_reemissao,
            entrega_parcial=trecho_parcial,
            extraido_por="regra",
            notas_extracao=notas,
        )

    @staticmethod
    def _trecho(corpo: str, palavra: str) -> str:
        """
        Devolve a frase que contém a palavra-chave, respeitando a estrutura do
        e-mail: primeiro isola o PARÁGRAFO (quebra por linha em branco), só
        depois corta em frase.

        Importa porque o corpo tem linha digitável e valores em linhas
        próprias, sem ponto final. Achatar tudo antes faz a "frase" da entrega
        parcial começar no meio de uma linha digitável — e o que a analista lê
        na fila fica ilegível.
        """
        chave = palavra.split()[0].lower()
        for paragrafo in re.split(r"\n\s*\n", corpo):
            if chave not in paragrafo.lower():
                continue
            achatado = re.sub(r"\s+", " ", paragrafo).strip()
            for frase in re.split(r"(?<=[.!?])\s+", achatado):
                if chave in frase.lower():
                    return frase.strip(" .")
            return achatado.strip(" .")
        return palavra

    @staticmethod
    def _parse_aprovacoes(bloco: str) -> list[MensagemAprovacao]:
        msgs: list[MensagemAprovacao] = []
        for m in _RE_WPP.finditer(bloco):
            quando, quem, txt = m.group(1), m.group(2).strip(), m.group(3).strip()
            if " - " in quem:
                area, autor = quem.split(" - ", 1)
            else:
                area, autor = "", quem
            msgs.append(
                MensagemAprovacao(
                    quando=quando.strip(),
                    area=area.strip(),
                    autor=autor.strip(),
                    texto=txt,
                )
            )
        return msgs
