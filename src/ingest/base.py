"""Infra comum de ingestão: leitura tolerante a encoding e delimitador."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterator

# Ordem de tentativa. Export de ERP brasileiro é latin-1 com frequência
# desconfortável; UTF-8 com BOM aparece quando alguém passou pelo Excel.
ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def ler_texto(caminho: str | Path) -> tuple[str, str]:
    """Devolve (conteúdo, encoding usado). Nunca estoura por encoding."""
    p = Path(caminho)
    dados = p.read_bytes()
    for enc in ENCODINGS:
        try:
            return dados.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return dados.decode("latin-1", errors="replace"), "latin-1/replace"


def detectar_delimitador(amostra: str) -> str:
    """
    Protheus exporta com ';', Omie com ','. Detectar em vez de assumir, porque
    na quinta conta vai aparecer um que usa tab.
    """
    try:
        return csv.Sniffer().sniff(amostra, delimiters=";,\t|").delimiter
    except csv.Error:
        primeira = amostra.splitlines()[0] if amostra.splitlines() else ""
        return max(";,\t|", key=primeira.count) if primeira else ","


def ler_csv(caminho: str | Path) -> tuple[list[dict[str, str]], list[str]]:
    """
    Lê CSV devolvendo (linhas, avisos).

    Normaliza os cabeçalhos para minúsculo sem espaço, porque 'Valor',
    'valor' e ' valor ' são o mesmo campo e não vale carregar essa dúvida
    para dentro do motor.
    """
    avisos: list[str] = []
    texto, enc = ler_texto(caminho)
    if enc != "utf-8":
        avisos.append(f"{Path(caminho).name}: lido como {enc}")

    delim = detectar_delimitador(texto[:4096])
    leitor = csv.DictReader(io.StringIO(texto), delimiter=delim)
    campos = [(c or "").strip().lower() for c in (leitor.fieldnames or [])]

    linhas: list[dict[str, str]] = []
    for i, bruta in enumerate(leitor, start=2):
        linha = {}
        for chave_orig, valor in bruta.items():
            chave = (chave_orig or "").strip().lower()
            linha[chave] = (valor or "").strip() if isinstance(valor, str) else valor
        if not any(v for v in linha.values()):
            continue
        faltando = [c for c in campos if c not in linha or linha.get(c) in (None, "")]
        if len(faltando) == len(campos):
            avisos.append(f"{Path(caminho).name} linha {i}: vazia, ignorada")
            continue
        linha["_linha_origem"] = str(i)
        linhas.append(linha)
    return linhas, avisos


def primeiro_campo(linha: dict, *nomes: str) -> str | None:
    """
    Pega o primeiro campo presente entre vários nomes possíveis.

    Serve para absorver variação de layout sem um `if` por sistema:
    'cnpj' no Protheus, 'tax_id' no Omie, 'cpf_cnpj' no próximo ERP.
    """
    for n in nomes:
        v = linha.get(n)
        if v not in (None, ""):
            return str(v)
    return None


def iter_blocos(texto: str, marcador: str) -> Iterator[str]:
    """Quebra um arquivo de texto em blocos por um marcador de separação."""
    partes = texto.split(marcador)
    for parte in partes:
        if parte.strip():
            yield parte
