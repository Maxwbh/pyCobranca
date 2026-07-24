"""Hierarquia de erros de domínio da PyCobrança."""

from __future__ import annotations

__all__ = ["PyCobrancaError", "BoletoInvalido", "BancoNaoRegistrado"]


class PyCobrancaError(Exception):
    """Erro-base da biblioteca."""


class BoletoInvalido(PyCobrancaError, ValueError):
    """Dados do boleto não passam nas validações (comuns ou do banco)."""


class BancoNaoRegistrado(PyCobrancaError, KeyError):
    """Código FEBRABAN não consta no registro de bancos."""
