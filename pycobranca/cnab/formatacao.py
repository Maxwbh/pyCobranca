"""Formatação de campos CNAB (padrão FEBRABAN)."""

from __future__ import annotations

import re
import unicodedata

__all__ = ["remover_acentos", "format_size", "format_valor"]


def remover_acentos(texto: str) -> str:
    """Remove acentos (normaliza para ASCII) nos campos do arquivo CNAB."""
    return unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")


def format_size(texto: str, tamanho: int) -> str:
    """Equivalente ao ``format_size`` (``formatacao_string.rb``).

    Remove acentos, colapsa espaços e **depois** remove símbolos (por isso um
    ``&`` vira espaço duplo, como no Ruby); trunca ou completa com espaços.
    """
    limpo = remover_acentos(texto or "").strip()
    limpo = re.sub(r"\s+", " ", limpo)
    limpo = re.sub(r"[^A-Za-z0-9 ]", "", limpo)
    return limpo[:tamanho] if len(limpo) > tamanho else limpo.ljust(tamanho)


def format_valor(valor, tamanho: int = 13) -> str:
    """Equivalente ao ``format_value``: ``%.2f`` sem o ponto, zeros à esquerda."""
    return f"{float(valor):.2f}".replace(".", "").rjust(tamanho, "0")
