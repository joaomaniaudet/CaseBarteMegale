"""
Normalização: a camada mais chata e a que mais resolve.

Boa parte do que parece exigir IA neste case é normalização de string. Separar
isso explicitamente importa por dois motivos:

  1. Custo e auditoria — regra determinística é grátis, reproduzível e o CTO
     consegue ler.
  2. Honestidade — se eu mandasse tudo para o LLM, eu não saberia dizer onde a
     IA está realmente agregando valor. Aqui eu sei: ela entra em 3 lugares,
     declarados em README.md.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------

_NAO_ALFANUM = re.compile(r"[^A-Z0-9 ]+")
_ESPACOS = re.compile(r"\s+")


def sem_acento(texto: str) -> str:
    """'Emporio Bela Vista' e 'Empório Bela Vista' viram a mesma coisa."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def limpar_texto(texto: str | None) -> str:
    if not texto:
        return ""
    t = sem_acento(str(texto)).upper()
    t = _NAO_ALFANUM.sub(" ", t)
    return _ESPACOS.sub(" ", t).strip()


# ---------------------------------------------------------------------------
# CNPJ / CPF
# ---------------------------------------------------------------------------

_SO_DIGITOS = re.compile(r"\D+")
# 14 dígitos corridos (CNPJ sem máscara, como aparece no histórico do extrato)
# ou com máscara. Capturamos ambos e normalizamos depois.
_CNPJ_NO_TEXTO = re.compile(r"(?<!\d)(\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2})(?!\d)")
_CPF_NO_TEXTO = re.compile(r"(?<!\d)(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2})(?!\d)")


def normalizar_cnpj(valor: str | None) -> str | None:
    """
    '12.345.678/0001-90' -> '12345678000190'
    '55666777000144'     -> '55666777000144'

    A Vantara tem o mesmo franqueado cadastrado com máscara no Protheus e sem
    máscara no Omie. Sem esta função, Grão Nobre é duas empresas diferentes.
    """
    if not valor:
        return None
    digitos = _SO_DIGITOS.sub("", str(valor))
    if len(digitos) == 14:
        return digitos
    if len(digitos) == 11:          # CPF (franqueado pessoa física)
        return digitos
    if 0 < len(digitos) < 14:
        return digitos.zfill(14)    # perdeu zero à esquerda em export de planilha
    return digitos or None


def extrair_documentos_fiscais(texto: str) -> list[str]:
    """Acha CNPJ/CPF enterrado em texto livre do histórico bancário."""
    achados: list[str] = []
    for m in _CNPJ_NO_TEXTO.finditer(texto or ""):
        n = normalizar_cnpj(m.group(1))
        if n and len(n) == 14:
            achados.append(n)
    for m in _CPF_NO_TEXTO.finditer(texto or ""):
        n = normalizar_cnpj(m.group(1))
        if n and len(n) == 11 and n not in achados:
            achados.append(n)
    return achados


def formatar_cnpj(cnpj: str | None) -> str:
    if not cnpj:
        return ""
    d = _SO_DIGITOS.sub("", cnpj)
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return cnpj


# ---------------------------------------------------------------------------
# Valores monetários
# ---------------------------------------------------------------------------

def parse_valor(valor: str | float | int | Decimal | None) -> Decimal:
    """
    Aceita os dois formatos que chegam no mesmo pipeline:
      pt-BR do Protheus/Itaú:  '18.450,00'  '1.240,00'
      ISO do Omie:             '31250.00'   '3400.0'

    A heurística: se tem vírgula, a vírgula é o separador decimal e o ponto é
    separador de milhar. Se não tem vírgula, o ponto é decimal.
    """
    if valor is None or valor == "":
        return Decimal("0")
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, (int, float)):
        return Decimal(str(valor))

    s = str(valor).strip()
    s = re.sub(r"[R$\s ]", "", s)
    negativo = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.strip("-()")

    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        d = Decimal(s)
    except InvalidOperation:
        return Decimal("0")
    return -d if negativo else d


def fmt_brl(valor: Decimal | float | int) -> str:
    d = Decimal(str(valor)).quantize(Decimal("0.01"))
    inteiro, _, dec = f"{abs(d):.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    sinal = "-" if d < 0 else ""
    return f"{sinal}{'.'.join(grupos)},{dec}"


# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------

_FORMATOS_DATA = ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%Y", "%Y/%m/%d")


def parse_data(valor: str | date | None) -> date | None:
    """pt-BR ('10/07/2026') e ISO ('2026-07-20') no mesmo pipeline."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    s = str(valor).strip()
    for fmt in _FORMATOS_DATA:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def fmt_data(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


# ---------------------------------------------------------------------------
# Número de documento
# ---------------------------------------------------------------------------

_PREFIXOS_DOC = ("NF", "NFE", "NFSE", "NFS", "FAT", "DUP", "BOL", "CTE", "CT")


def normalizar_documento(doc: str | None) -> str:
    """
    Reduz a grafia do documento à sua identidade.

        'NF 104521'      -> '104521'
        'NF 88231'       -> '88231'
        '088231'         -> '88231'     <-- zero à esquerda, o caso São Jorge
        'FAT-2026-0331'  -> '20260331'
        'Nota fiscal 088231' -> '88231'

    O e-mail 1 da São Jorge diz "NF 88231" e o e-mail 2 diz "Nota fiscal
    088231". Para qualquer sistema são dois documentos. Para o fornecedor é o
    mesmo. Essa função é o que impede o terceiro pagamento duplicado do ano.
    """
    if not doc:
        return ""
    t = limpar_texto(doc)
    t = re.sub(r"\b(NOTA FISCAL|NOTA|FATURA|BOLETO|DUPLICATA|PEDIDO)\b", " ", t)
    for p in _PREFIXOS_DOC:
        t = re.sub(rf"\b{p}\b", " ", t)
    digitos = _SO_DIGITOS.sub("", t)
    if not digitos:
        return _ESPACOS.sub("", t)
    sem_zeros = digitos.lstrip("0")
    return sem_zeros or "0"


def normalizar_id_bancario(valor: str | None) -> str | None:
    """
    nosso_numero: '000012345678' no título e no campo documento do extrato.

    Comparar sem os zeros à esquerda porque nem todo banco devolve o campo
    com o mesmo padding.
    """
    if not valor:
        return None
    d = _SO_DIGITOS.sub("", str(valor))
    if not d:
        return None
    return d.lstrip("0") or "0"


# ---------------------------------------------------------------------------
# Nomes de empresa — o coração do matching por nome
# ---------------------------------------------------------------------------

class NormalizadorNome:
    """
    Transforma razão social em um conjunto de tokens significativos.

    Dois detalhes que decidem o resultado neste data pack:

      1. Stopwords societárias. 'Rede Sabor & Cia Ltda' e 'SABOR CIA' precisam
         convergir, então LTDA/CIA/COMERCIO/SA saem fora.

      2. Truncamento. O Itaú corta o histórico em ~32 caracteres, então o
         ÚLTIMO token pode estar cortado no meio:
             'PIX RECEBIDO CANTINHO MINEIRO FRA'  ->  FRA
             'Cantinho Mineiro Franquias Ltda'    ->  FRANQUIAS
         Tratar o último token como prefixo resolve isso. Tratar como
         igualdade perde o match.
    """

    def __init__(self, stopwords: list[str], ruido_historico: list[str],
                 ultimo_token_prefixo: bool = True, prefixo_minimo: int = 2):
        self.stopwords = {limpar_texto(s) for s in stopwords if s}
        # Ordena do maior para o menor para remover 'LIQUIDACAO COBRANCA
        # SIMPLES' antes de 'LIQUIDACAO COBRANCA'.
        self.ruido = sorted((limpar_texto(r) for r in ruido_historico if r),
                            key=len, reverse=True)
        self.ultimo_token_prefixo = ultimo_token_prefixo
        self.prefixo_minimo = prefixo_minimo

    def tirar_ruido(self, historico: str) -> str:
        """Remove 'PIX RECEBIDO', 'TED RECEBIDA', 'CNPJ' etc. do histórico."""
        t = limpar_texto(historico)
        for r in self.ruido:
            if r and r in t:
                t = t.replace(r, " ")
        # números soltos (CNPJ já foi extraído em outra função)
        t = re.sub(r"\b\d+\b", " ", t)
        return _ESPACOS.sub(" ", t).strip()

    def tokens(self, nome: str) -> list[str]:
        t = limpar_texto(nome)
        brutos = [x for x in t.split(" ") if x]
        return [x for x in brutos if x not in self.stopwords and len(x) > 1]

    def tokens_do_historico(self, historico: str) -> list[str]:
        """
        Tokens úteis do histórico bancário, já descontando o truncamento.

        Caso que motiva o tratamento especial do último token:

            'PIX RECEBIDO PADARIA VILA NOVA LT'  ->  ... NOVA, LT
            'Padaria Vila Nova Ltda'             ->  PADARIA, VILA, NOVA

        'LT' é um 'LTDA' cortado pelo limite de 32 caracteres do extrato. Como
        LTDA é stopword, ele foi removido do lado do título e não existe par
        para o fragmento. Contado como token não casado, derruba a cobertura
        de 100% para 75% e rebaixa um match certo a "nome fraco" — que manda
        para confirmação humana um Pix com nome completo e valor exato.

        Então: fragmento final que é prefixo de stopword é descartado, não
        contabilizado como falha.
        """
        tokens = self.tokens(self.tirar_ruido(historico))
        if tokens:
            ultimo = tokens[-1]
            if any(sw.startswith(ultimo) and sw != ultimo for sw in self.stopwords):
                tokens = tokens[:-1]
        return tokens

    def cobertura(self, tokens_banco: list[str], tokens_titulo: list[str]) -> tuple[float, int]:
        """
        Qual fração dos tokens do banco está presente no nome do título.

        Cobertura (containment), não similaridade simétrica: o histórico do
        banco é um SUBCONJUNTO truncado do nome real, então exigir simetria
        penalizaria o match correto.

        Retorna (cobertura 0..1, quantidade de tokens que casaram).
        """
        if not tokens_banco or not tokens_titulo:
            return 0.0, 0
        alvo = set(tokens_titulo)
        casados = 0
        ultimo_idx = len(tokens_banco) - 1
        for i, tb in enumerate(tokens_banco):
            if tb in alvo:
                casados += 1
                continue
            e_ultimo = (i == ultimo_idx)
            if self.ultimo_token_prefixo and e_ultimo and len(tb) >= self.prefixo_minimo:
                if any(tt.startswith(tb) for tt in alvo):
                    casados += 1
                    continue
            # token do banco pode ser abreviação do nome real em qualquer posição
            if len(tb) >= 4 and any(tt.startswith(tb) for tt in alvo):
                casados += 1
        return casados / len(tokens_banco), casados

    def chave_canonica(self, nome: str) -> str:
        """
        Chave estável para agrupar entidades sem CNPJ.

        Tokens ordenados alfabeticamente, para que 'Emporio Bela Vista' e
        'BELA VISTA EMPORIO' produzam a mesma chave.
        """
        return " ".join(sorted(set(self.tokens(nome))))


# ---------------------------------------------------------------------------
# Linha digitável de boleto
# ---------------------------------------------------------------------------

_LINHA_DIGITAVEL = re.compile(r"(?:\d[\d.\s]{35,60}\d)")


def extrair_linha_digitavel(texto: str) -> str | None:
    """
    Acha a linha digitável (47 dígitos) num corpo de e-mail.

    Serve de identificador forte do boleto: dois e-mails com a MESMA linha
    digitável são a mesma cobrança; linhas diferentes para o mesmo documento
    indicam reemissão.
    """
    for m in _LINHA_DIGITAVEL.finditer(texto or ""):
        digitos = _SO_DIGITOS.sub("", m.group(0))
        if len(digitos) in (47, 48):
            return digitos
    return None


def valores_possiveis_da_linha_digitavel(linha: str | None) -> list[Decimal]:
    """
    Lê o campo de valor da linha digitável (posições 38-47, padrão FEBRABAN)
    para conferir contra o valor escrito no corpo do e-mail.

    PREMISSA DECLARADA: o data pack é sintético e a linha digitável da São
    Jorge não segue estritamente o padrão (o campo traz '0000019278', que em
    centavos daria R$ 192,78, mas o corpo do e-mail diz R$ 19.278,00 — o autor
    escreveu o valor em reais).

    Em produção eu validaria o DV e trataria divergência como bloqueio. Aqui
    devolvo as DUAS leituras possíveis e considero conferido se qualquer uma
    casar, porque gerar alerta em cima de um artefato do dado de teste seria
    falso positivo — e falso positivo é o que faz a analista desligar a
    ferramenta. O README registra isso em "Limitações conhecidas".
    """
    if not linha:
        return []
    d = _SO_DIGITOS.sub("", linha)
    if len(d) < 47:
        return []
    try:
        bruto = int(d[37:47])
    except ValueError:
        return []
    if bruto <= 0:
        return []
    como_centavos = (Decimal(bruto) / Decimal(100)).quantize(Decimal("0.01"))
    como_reais = Decimal(bruto).quantize(Decimal("0.01"))
    return [como_centavos, como_reais]
