"""
Camada de IA — multi-provedor.

Suporta Anthropic (Claude), Google (Gemini) e xAI (Grok). O provedor é
escolhido por config ou auto-detectado pela chave de API presente no ambiente.

Três decisões de desenho que são o que eu defenderia diante do CTO:

1. A IA NUNCA recebe o universo de dados. Ela só ranqueia candidatos que a
   camada determinística já selecionou, e os candidatos vêm com id. Se ela
   devolver um id que não está na lista, a resposta é descartada. Alucinação
   fica impedida por construção, não por pedido no prompt.

2. A IA PODE SE ABSTER, e abstenção é resposta de primeira classe. Um modelo
   obrigado a escolher sempre escolhe — e é assim que nasce baixa errada. Aqui,
   "não sei" devolve o caso para a fila humana.

3. A IA NUNCA APLICA NADA. O config trava
   `bloquear_se_decidido_por_ia: true`, então decisão de IA no máximo chega a
   "CONFIRMAR". Humano aplica. Isso não é desconfiança do modelo: é que baixa
   indevida em contas a receber vira cobrança indevida a franqueado, que é
   justamente o problema que estamos resolvendo.

Mais: o pipeline inteiro funciona SEM chave de API. Sem IA, os tiers
determinísticos rodam e os casos ambíguos vão para a fila humana com o motivo
registrado. Um pipeline financeiro que para porque a API caiu não entra em
produção.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PROVEDORES_SUPORTADOS = ("anthropic", "google", "xai")

_ENV_KEYS = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "google": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    "xai": ("XAI_API_KEY", "GROK_API_KEY"),
}

_MODELOS_PADRAO = {
    "anthropic": "claude-sonnet-4-5",
    "google": "gemini-3-flash-preview",
    "xai": "grok-3-mini",
}

_SCHEMA_ESCOLHA_TITULO = {
    "type": "object",
    "properties": {
        "titulo_id": {"type": ["string", "null"]},
        "confianca": {"type": "number"},
        "justificativa": {"type": "string"},
    },
    "required": ["titulo_id", "confianca", "justificativa"],
}

_SCHEMA_ENRIQUECIMENTO_AP = {
    "type": "object",
    "properties": {
        "fornecedor": {"type": ["string", "null"]},
        "e_reemissao_de_cobranca_anterior": {"type": "boolean"},
        "entrega_parcial": {"type": ["string", "null"]},
        "quantidade_entregue": {"type": ["string", "null"]},
        "documentos_citados": {"type": "array", "items": {"type": "string"}},
        "observacoes_de_risco": {"type": ["string", "null"]},
    },
    "required": [
        "fornecedor",
        "e_reemissao_de_cobranca_anterior",
        "entrega_parcial",
        "quantidade_entregue",
        "documentos_citados",
        "observacoes_de_risco",
    ],
}


@dataclass
class DecisaoIA:
    """Resposta estruturada do modelo. `escolha` None significa abstenção."""
    escolha: str | None
    confianca: float
    justificativa: str
    absteve: bool = False
    erro: str | None = None


def _detectar_provedor() -> tuple[str | None, str | None]:
    """Auto-detecta o provedor pela chave de API presente no ambiente."""
    for provedor, env_vars in _ENV_KEYS.items():
        for var in env_vars:
            chave = os.environ.get(var)
            if chave:
                return provedor, var
    return None, None


def _obter_chave(provedor: str) -> str | None:
    for var in _ENV_KEYS.get(provedor, ()):
        chave = os.environ.get(var)
        if chave:
            return chave
    return None


class ClienteIA:
    def __init__(self, cfg: dict, habilitada: bool = True, dir_cache: str | Path = ".cache_ia"):
        ia_cfg = cfg.get("ia", {})
        self.max_tokens = int(ia_cfg.get("max_tokens", 1200))
        self.temperatura = float(ia_cfg.get("temperatura", 0.0))
        self.max_candidatos = int(ia_cfg.get("max_candidatos_no_prompt", 8))
        self.score_minimo = float(ia_cfg.get("score_minimo_aceito", 0.6))
        self.usar_cache = bool(ia_cfg.get("cache", True))
        self.dir_cache = Path(dir_cache)

        self.chamadas = 0
        self.acertos_cache = 0
        self.abstencoes = 0
        self.falhas = 0
        self.erros: list[dict[str, str]] = []

        self._cliente = None
        self.provedor: str | None = None
        self.modelo: str | None = None
        self.habilitada = bool(habilitada and ia_cfg.get("habilitada", True))
        self.motivo_desligada: str | None = None

        if not self.habilitada:
            self.motivo_desligada = "desabilitada por configuração ou flag --sem-ia"
            return

        provedor_cfg = ia_cfg.get("provedor", "auto")
        modelo_cfg = ia_cfg.get("modelo")

        if provedor_cfg == "auto":
            self.provedor, _env_var = _detectar_provedor()
            if not self.provedor:
                self.habilitada = False
                self.motivo_desligada = (
                    "nenhuma chave de API encontrada no ambiente. "
                    "Configure uma das variáveis: "
                    + ", ".join(v for vs in _ENV_KEYS.values() for v in vs)
                )
                return
        else:
            self.provedor = provedor_cfg
            if self.provedor not in _PROVEDORES_SUPORTADOS:
                self.habilitada = False
                self.motivo_desligada = (
                    f"provedor '{self.provedor}' não suportado. "
                    f"Use: {', '.join(_PROVEDORES_SUPORTADOS)}"
                )
                return
            if not _obter_chave(self.provedor):
                self.habilitada = False
                self.motivo_desligada = (
                    f"chave de API ausente para provedor '{self.provedor}'. "
                    f"Configure: {' ou '.join(_ENV_KEYS[self.provedor])}"
                )
                return

        self.modelo = modelo_cfg or _MODELOS_PADRAO[self.provedor]
        self._inicializar_cliente()

    def _inicializar_cliente(self) -> None:
        try:
            if self.provedor == "anthropic":
                import anthropic
                self._cliente = anthropic.Anthropic()

            elif self.provedor == "google":
                from google import genai
                self._cliente = genai.Client(api_key=_obter_chave("google"))

            elif self.provedor == "xai":
                from openai import OpenAI
                self._cliente = OpenAI(
                    api_key=_obter_chave("xai"),
                    base_url="https://api.x.ai/v1",
                )
        except Exception as exc:
            self.habilitada = False
            self.motivo_desligada = f"SDK do provedor '{self.provedor}' indisponível: {exc}"
            self.erros.append({
                "categoria": "SISTEMA — SDK indisponível",
                "etapa": "inicialização",
                "mensagem": self.motivo_desligada,
            })

    # ------------------------------------------------------------------
    @property
    def ativa(self) -> bool:
        return bool(self.habilitada and self._cliente)

    def _chave_cache(self, prompt: str, sistema: str) -> Path:
        h = hashlib.sha256(f"{self.provedor}|{self.modelo}|{sistema}|{prompt}".encode()).hexdigest()[:24]
        return self.dir_cache / f"{h}.json"

    def _chamar_anthropic(self, sistema: str, prompt: str) -> str | None:
        resp = self._cliente.messages.create(
            model=self.modelo,
            max_tokens=self.max_tokens,
            temperature=self.temperatura,
            system=sistema,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def _chamar_google(self, sistema: str, prompt: str) -> str | None:
        from google.genai import types
        config_args = dict(
            max_output_tokens=self.max_tokens,
            temperature=self.temperatura,
            system_instruction=sistema,
            response_mime_type="application/json",
        )
        schema = getattr(self, "_schema_json", None)
        if schema:
            config_args["response_json_schema"] = schema
        config = types.GenerateContentConfig(**config_args)
        resp = self._cliente.models.generate_content(
            model=self.modelo,
            contents=prompt,
            config=config,
        )
        texto = getattr(resp, "text", None)
        if not texto:
            candidatos = getattr(resp, "candidates", None) or []
            motivos = []
            for candidato in candidatos[:2]:
                motivo = getattr(getattr(candidato, "finish_reason", None), "name", None)
                if motivo:
                    motivos.append(motivo)
            detalhe = f" finish_reason={','.join(motivos)}." if motivos else "."
            raise RuntimeError(f"Google não retornou conteúdo textual.{detalhe}")
        return texto

    def _chamar_xai(self, sistema: str, prompt: str) -> str | None:
        resp = self._cliente.chat.completions.create(
            model=self.modelo,
            max_tokens=self.max_tokens,
            temperature=self.temperatura,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content

    def _chamar(self, sistema: str, prompt: str, schema_hint: str) -> dict[str, Any] | None:
        """
        Chamada crua com cache em disco.

        O cache existe por dois motivos: reexecutar o pipeline no mesmo mês não
        deve custar de novo, e o resultado do case precisa ser reproduzível por
        quem for avaliar — inclusive sem chave de API, se eu versionar o cache.
        """
        if not self.ativa:
            return None

        arq = self._chave_cache(prompt, sistema)
        if self.usar_cache and arq.exists():
            self.acertos_cache += 1
            try:
                return json.loads(arq.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.erros.append({
                    "categoria": "SISTEMA — cache inválido",
                    "etapa": "leitura do cache",
                    "mensagem": "O arquivo de cache não contém JSON válido; uma nova chamada será tentada.",
                })

        prompt_completo = f"{prompt}\n\nResponda SOMENTE com JSON válido: {schema_hint}"

        try:
            self.chamadas += 1
            despacho = {
                "anthropic": self._chamar_anthropic,
                "google": self._chamar_google,
                "xai": self._chamar_xai,
            }
            texto = despacho[self.provedor](sistema, prompt_completo)
            dados = _extrair_json(texto)
            if dados is None:
                self.falhas += 1
                self.erros.append({
                    "categoria": "SISTEMA — resposta inválida",
                    "etapa": "interpretação da resposta",
                    "mensagem": (
                        "A API respondeu, mas o conteúdo não pôde ser interpretado "
                        f"como JSON válido no formato esperado ({_diagnostico_json(texto)})."
                    ),
                })
                return None
            if self.usar_cache:
                self.dir_cache.mkdir(parents=True, exist_ok=True)
                arq.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
            return dados
        except Exception as exc:
            self.falhas += 1
            self.erros.append(self._classificar_erro_api(exc))
            return None

    def _classificar_erro_api(self, exc: Exception) -> dict[str, str]:
        """Converte uma exceção do SDK em diagnóstico seguro para a interface."""
        bruto = str(exc).strip().replace("\n", " ")
        for chave in _ENV_KEYS.get(self.provedor or "", ()):
            segredo = os.environ.get(chave)
            if segredo:
                bruto = bruto.replace(segredo, "[REDACTED]")
        mensagem = bruto[:500] or "sem mensagem retornada pelo SDK"
        baixo = mensagem.lower()

        if any(token in baixo for token in ("401", "403", "unauthorized", "forbidden", "api key", "permission")):
            categoria = "API — autenticação/permissão"
        elif any(token in baixo for token in ("429", "quota", "rate limit", "resource exhausted")):
            categoria = "API — quota/limite"
        elif any(token in baixo for token in ("timeout", "timed out", "connection", "dns", "network")):
            categoria = "API — rede/timeout"
        else:
            categoria = "API — erro do provedor"

        return {
            "categoria": categoria,
            "etapa": "chamada ao provedor",
            "mensagem": f"{type(exc).__name__}: {mensagem}",
        }

    # ------------------------------------------------------------------
    def escolher_titulo(
        self,
        historico: str,
        valor_credito: str,
        data_credito: str,
        candidatos: list[dict[str, Any]],
    ) -> DecisaoIA:
        """
        Desempata candidatos de título para um crédito bancário.

        A lista de candidatos vem da camada determinística. O modelo só pode
        responder com um `titulo_id` que está nela, ou se abster.
        """
        if not self.ativa:
            return DecisaoIA(None, 0.0, "IA desligada", absteve=True,
                             erro=self.motivo_desligada)
        if not candidatos:
            return DecisaoIA(None, 0.0, "sem candidatos", absteve=True)

        candidatos = candidatos[: self.max_candidatos]
        ids_validos = {c["titulo_id"] for c in candidatos}

        sistema = (
            "Você apoia a conciliação de contas a receber de uma franqueadora "
            "brasileira. Recebe UM crédito do extrato bancário e uma lista fechada "
            "de títulos candidatos. Sua tarefa é dizer qual título aquele crédito "
            "quita.\n\n"
            "REGRAS ABSOLUTAS:\n"
            "1. Você só pode escolher um titulo_id que esteja na lista. Nunca invente.\n"
            "2. Se a evidência não for suficiente, ABSTENHA-SE "
            "(titulo_id: null). Abster-se é a resposta correta na dúvida — um "
            "palpite errado gera cobrança indevida a um franqueado que pagou.\n"
            "3. Nome truncado no histórico do banco é normal (o extrato corta em ~32 "
            "caracteres). Diferença de valor pode ter causa legítima: retenção de "
            "imposto na fonte, multa de mora, pagamento parcial.\n"
            "4. Justifique em uma frase, citando a evidência concreta que usou."
        )
        prompt = (
            f"CRÉDITO NO EXTRATO\n"
            f"  histórico: {historico!r}\n"
            f"  valor: R$ {valor_credito}\n"
            f"  data: {data_credito}\n\n"
            f"TÍTULOS CANDIDATOS (lista fechada)\n"
            f"{json.dumps(candidatos, ensure_ascii=False, indent=2)}"
        )
        schema = (
            '{"titulo_id": "<id da lista ou null>", '
            '"confianca": <0.0 a 1.0>, "justificativa": "<uma frase>"}'
        )

        self._schema_json = _SCHEMA_ESCOLHA_TITULO
        try:
            dados = self._chamar(sistema, prompt, schema)
        finally:
            self._schema_json = None
        if not dados:
            return DecisaoIA(None, 0.0, "falha na chamada à IA", absteve=True,
                             erro="resposta não parseável ou erro de rede")

        escolha = dados.get("titulo_id")
        justificativa = str(dados.get("justificativa", ""))[:400]
        try:
            confianca = float(dados.get("confianca", 0.0))
        except (TypeError, ValueError):
            confianca = 0.0

        if escolha in (None, "", "null"):
            self.abstencoes += 1
            return DecisaoIA(None, confianca, justificativa or "IA se absteve", absteve=True)

        if escolha not in ids_validos:
            self.falhas += 1
            self.erros.append({
                "categoria": "SISTEMA — guardrail",
                "etapa": "validação da resposta",
                "mensagem": f"A IA devolveu titulo_id fora da lista permitida: {escolha!r}.",
            })
            return DecisaoIA(
                None, 0.0,
                f"IA devolveu id inexistente ({escolha!r}); resposta descartada",
                absteve=True, erro="id_fora_da_lista",
            )

        if confianca < self.score_minimo:
            self.abstencoes += 1
            return DecisaoIA(
                None, confianca,
                f"IA escolheu {escolha} com confiança {confianca:.2f}, abaixo do "
                f"mínimo {self.score_minimo:.2f} — devolvido à fila humana",
                absteve=True,
            )

        return DecisaoIA(escolha, confianca, justificativa or "sem justificativa")

    # ------------------------------------------------------------------
    def enriquecer_cobranca_ap(self, cobranca: dict[str, Any]) -> dict[str, Any] | None:
        """
        Extrai de um e-mail de contas a pagar o que não tem forma de campo.

        A IA complementa a extração quando o e-mail foge dos padrões conhecidos.
        No data pack, a frase de entrega parcial também é capturada pelo fallback
        determinístico; em produção, a camada semântica cobre variações de texto.
        """
        if not self.ativa:
            return None

        sistema = (
            "Você lê e-mails de cobrança recebidos pelo contas a pagar de uma "
            "empresa brasileira e extrai fatos. Extraia APENAS o que está escrito. "
            "Se um campo não estiver no texto, devolva null. Nunca estime, nunca "
            "complete com o que seria plausível: um valor inventado aqui vira um "
            "pagamento errado."
        )
        prompt = (
            "E-MAIL\n"
            f"  de: {cobranca.get('remetente')}\n"
            f"  data: {cobranca.get('recebido_em')}\n"
            f"  assunto: {cobranca.get('assunto')}\n"
            f"  corpo:\n{cobranca.get('corpo')}\n"
        )
        schema = (
            '{"fornecedor": "<nome comercial do fornecedor ou null>", '
            '"e_reemissao_de_cobranca_anterior": true|false, '
            '"entrega_parcial": "<trecho literal que indica entrega incompleta ou null>", '
            '"quantidade_entregue": "<ex: 12 de 15 volumes, ou null>", '
            '"documentos_citados": ["<numeros de nota citados>"], '
            '"observacoes_de_risco": "<uma frase sobre risco de pagamento, ou null>"}'
        )
        self._schema_json = _SCHEMA_ENRIQUECIMENTO_AP
        try:
            return self._chamar(sistema, prompt, schema)
        finally:
            self._schema_json = None

    # ------------------------------------------------------------------
    def resumo(self) -> dict[str, Any]:
        return {
            "ativa": self.ativa,
            "provedor": self.provedor,
            "modelo": self.modelo if self.ativa else None,
            "motivo_desligada": self.motivo_desligada,
            "chamadas": self.chamadas,
            "acertos_cache": self.acertos_cache,
            "abstencoes": self.abstencoes,
            "falhas": self.falhas,
            "erros": self.erros[-10:],
        }


def _extrair_json(texto: str | dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Tolera o modelo embrulhar o JSON em ```json ... ``` ou em prosa.

    Não é frescura: é a diferença entre o pipeline sobreviver a uma variação de
    formatação e quebrar em produção numa segunda-feira.
    """
    if isinstance(texto, dict):
        return texto

    t = (texto or "").strip().lstrip("\ufeff")
    bloco = re.search(r"```(?:json)?\s*(.*?)```", t, flags=re.IGNORECASE | re.DOTALL)
    if bloco:
        t = bloco.group(1).strip()
    try:
        return json.loads(t.strip())
    except json.JSONDecodeError:
        pass

    # Tolera texto introdutório ou posterior ao JSON sem cortar objetos
    # incorretamente pelo primeiro/último caractere `{`/`}`.
    decoder = json.JSONDecoder()
    for achado in re.finditer(r"\{", t):
        try:
            objeto, _fim = decoder.raw_decode(t[achado.start():])
            if isinstance(objeto, dict):
                return objeto
        except json.JSONDecodeError:
            continue
    return None


def _diagnostico_json(texto: str | dict[str, Any] | None) -> str:
    """Explica por que uma resposta não virou objeto JSON, sem expor o prompt."""
    if isinstance(texto, dict):
        return "objeto já estruturado"
    if not texto or not str(texto).strip():
        return "resposta vazia"
    bruto = str(texto).strip()
    if "```" in bruto:
        return "bloco markdown presente, mas JSON interno inválido"
    if "{" not in bruto:
        return "nenhum objeto JSON encontrado"
    return "objeto JSON malformado ou incompleto"
