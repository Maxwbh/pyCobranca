"""Hierarquia de erros de domínio da PyCobrança."""

from __future__ import annotations

__all__ = [
    "PyCobrancaError",
    "BoletoInvalido",
    "BancoNaoRegistrado",
    "OFXInvalido",
    "RetornoInvalido",
]


class PyCobrancaError(Exception):
    """Erro-base da biblioteca."""


class BoletoInvalido(PyCobrancaError, ValueError):
    """Dados do boleto não passam nas validações (comuns ou do banco).

    Carrega a lista **estruturada** de erros em :attr:`erros` (um item por
    problema encontrado), além da mensagem única (``str(exc)`` = itens unidos
    por ``"; "``). Um consumidor — por exemplo, uma camada REST — pode mapear
    cada item de :attr:`erros` para uma resposta de validação legível.
    """

    def __init__(self, erros: str | list[str]) -> None:
        self.erros: list[str] = [erros] if isinstance(erros, str) else list(erros)
        super().__init__("; ".join(self.erros))


class BancoNaoRegistrado(PyCobrancaError, KeyError):
    """Código FEBRABAN não consta no registro de bancos."""


class OFXInvalido(PyCobrancaError, ValueError):
    """Conteúdo não é um arquivo OFX válido (marcador ausente/estrutura quebrada)."""


class RetornoInvalido(PyCobrancaError, ValueError):
    """Arquivo de retorno CNAB vazio ou sem header reconhecível."""
