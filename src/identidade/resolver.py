"""
Resolvedor de identidade de entidade.

ESTE É O NÚCLEO REUSÁVEL DA SOLUÇÃO.

A Vantara pediu "uma IA que bate pagamento". Mas o que está quebrado não é o
matching — é que a mesma empresa existe como duas entidades diferentes em dois
ERPs, com CNPJ formatado de um jeito e sem máscara no outro, com a razão social
abreviada de forma diferente:

    Protheus: 'Grao Nobre Comercio Ltda'          CNPJ '55.666.777/0001-44'
    Omie:     'GRAO NOBRE COM LTDA'               CNPJ '55666777000144'

Enquanto não existe o conceito de "entidade", nenhum motor de conciliação
resolve o caso: não falta dinheiro, sobra dívida.

Um motor de conciliação é específico de contas a receber. Uma camada de
identidade serve a contas a receber, contas a pagar, cadastro de fornecedor,
visão consolidada de exposição por franqueado e às próximas cinco contas da
Barte — que terão outros ERPs e o mesmo problema.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..canonico import Entidade, Evidencia, Titulo
from ..normalizacao import NormalizadorNome, formatar_cnpj, limpar_texto


@dataclass
class CandidatoEntidade:
    entidade: Entidade
    score: float
    tokens_casados: int
    cobertura: float
    via: str              # "CNPJ" | "NOME"


class ResolvedorEntidades:
    """
    Agrupa títulos de fontes distintas em entidades unificadas.

    Precedência:
      1. CNPJ normalizado — determinístico, é a identidade legal. Sempre ganha.
      2. Chave canônica de nome — para quem vem sem CNPJ (planilha da terceira
         unidade, pagador que só tem nome no histórico bancário).

    Não uso IA aqui de propósito. Unificação de cadastro tem que ser
    reproduzível: se rodar duas vezes e der entidade diferente, a controladoria
    perde a confiança na ferramenta no primeiro mês. A IA entra DEPOIS, para
    desempatar candidatos, nunca para criar a entidade.
    """

    def __init__(self, normalizador: NormalizadorNome):
        self.norm = normalizador
        self.entidades: dict[str, Entidade] = {}
        self._por_cnpj: dict[str, str] = {}
        self._por_nome: dict[str, str] = {}

    # ------------------------------------------------------------------
    def construir(self, titulos: list[Titulo]) -> dict[str, Entidade]:
        """Primeira passada: cria as entidades e carimba entidade_id nos títulos."""
        agrupado: dict[str, list[Titulo]] = defaultdict(list)

        for t in titulos:
            chave = self._chave(t.cnpj, t.nome_original)
            agrupado[chave].append(t)
            t.entidade_id = chave

        for chave, grupo in agrupado.items():
            cnpjs = {t.cnpj for t in grupo if t.cnpj}
            nomes = tuple(dict.fromkeys(t.nome_original for t in grupo if t.nome_original))
            fontes = tuple(dict.fromkeys(t.fonte for t in grupo))
            # Nome canônico = o mais longo entre os vistos. Nome longo costuma
            # ser o menos abreviado, e abreviação é o que atrapalha o humano
            # que vai ler a fila.
            nome_canonico = max(nomes, key=len) if nomes else chave
            ent = Entidade(
                id=chave,
                cnpj=next(iter(cnpjs)) if cnpjs else None,
                nome_canonico=nome_canonico,
                nomes_vistos=nomes,
                fontes=fontes,
            )
            self.entidades[chave] = ent
            if ent.cnpj:
                self._por_cnpj[ent.cnpj] = chave
            self._por_nome.setdefault(self.norm.chave_canonica(nome_canonico), chave)
            for n in nomes:
                self._por_nome.setdefault(self.norm.chave_canonica(n), chave)

        return self.entidades

    def _chave(self, cnpj: str | None, nome: str) -> str:
        if cnpj:
            return f"cnpj:{cnpj}"
        canon = self.norm.chave_canonica(nome)
        return f"nome:{canon}" if canon else "nome:INDEFINIDO"

    # ------------------------------------------------------------------
    def identificar_por_cnpj(self, cnpjs: list[str]) -> CandidatoEntidade | None:
        """Pagador identificado por CNPJ achado no texto livre do extrato."""
        for c in cnpjs:
            chave = self._por_cnpj.get(c)
            if chave:
                return CandidatoEntidade(
                    entidade=self.entidades[chave],
                    score=1.0,
                    tokens_casados=0,
                    cobertura=1.0,
                    via="CNPJ",
                )
        return None

    def identificar_por_nome(self, historico: str) -> list[CandidatoEntidade]:
        """
        Pagador identificado pelo nome truncado no histórico bancário.

        Devolve TODOS os candidatos com cobertura > 0, ordenados. Devolver a
        lista em vez do melhor é deliberado: é o que permite detectar empate e
        bloquear automação (ver travas_auto_aplicar em config/regras.yaml).
        """
        tokens_banco = self.norm.tokens_do_historico(historico)
        if not tokens_banco:
            return []

        candidatos: list[CandidatoEntidade] = []
        for ent in self.entidades.values():
            melhor_cob, melhor_n = 0.0, 0
            for nome in (ent.nome_canonico, *ent.nomes_vistos):
                cob, n = self.norm.cobertura(tokens_banco, self.norm.tokens(nome))
                if cob > melhor_cob or (cob == melhor_cob and n > melhor_n):
                    melhor_cob, melhor_n = cob, n
            if melhor_cob <= 0:
                continue
            candidatos.append(
                CandidatoEntidade(
                    entidade=ent,
                    score=melhor_cob,
                    tokens_casados=melhor_n,
                    cobertura=melhor_cob,
                    via="NOME",
                )
            )

        candidatos.sort(key=lambda c: (c.cobertura, c.tokens_casados), reverse=True)
        return candidatos

    # ------------------------------------------------------------------
    def entidades_com_nomes_divergentes(self) -> list[tuple[Entidade, list[str]]]:
        """
        Mesma entidade escrita de formas diferentes entre sistemas.

        Não é erro de pagamento, é cegueira de gestão: hoje a Vantara não
        consegue dizer quanto o Empório Bela Vista deve no total, porque ele é
        'Emporio Bela Vista Alimentos SA' no Protheus e 'BELA VISTA EMPORIO
        S/A' no Omie.
        """
        achados = []
        for ent in self.entidades.values():
            if len(ent.fontes) < 2:
                continue
            variantes = {limpar_texto(n) for n in ent.nomes_vistos}
            if len(variantes) > 1:
                achados.append((ent, sorted(ent.nomes_vistos)))
        return achados

    def descrever(self, entidade_id: str) -> str:
        ent = self.entidades.get(entidade_id)
        if not ent:
            return entidade_id
        cnpj = f" ({formatar_cnpj(ent.cnpj)})" if ent.cnpj else " (sem CNPJ)"
        return f"{ent.nome_canonico}{cnpj}"


def evidencia_identidade(cand: CandidatoEntidade, historico: str) -> Evidencia:
    if cand.via == "CNPJ":
        return Evidencia(
            regra="identidade/cnpj_em_texto_livre",
            detalhe=(
                f"CNPJ {formatar_cnpj(cand.entidade.cnpj)} extraído do histórico "
                f"'{historico.strip()}'"
            ),
            campos={"cnpj": cand.entidade.cnpj},
        )
    return Evidencia(
        regra="identidade/nome_truncado",
        detalhe=(
            f"{cand.tokens_casados} token(s) do histórico '{historico.strip()}' "
            f"cobrem {cand.cobertura:.0%} de '{cand.entidade.nome_canonico}'"
        ),
        campos={
            "cobertura": round(cand.cobertura, 3),
            "tokens_casados": cand.tokens_casados,
        },
    )
