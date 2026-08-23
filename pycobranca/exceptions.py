"""Hierarquia de erros de domínio da PyCobrança."""

from __future__ import annotations

__all__ = [
    "PyCobrancaError",
    "BoletoInvalido",
    "BancoNaoRegistrado",
    "DadosInvalidos",
    "DependenciaAusente",
    "ModeloInvalido",
    "OFXInvalido",
    "RetornoInvalido",
]


class PyCobrancaError(Exception):
    """Erro-base da biblioteca.

    **Todo** erro levantado pela PyCobrança herda desta classe *e* do erro
    embutido correspondente (``ValueError``, ``KeyError``, ``RuntimeError``),
    nessa ordem: ``except PyCobrancaError`` cobre a biblioteca inteira, e quem
    já tratava pelo tipo embutido continua funcionando.
    """


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


class DadosInvalidos(PyCobrancaError, ValueError):
    """Entrada fora do que a composição do título aceita.

    É o erro das camadas baixas — dígitos verificadores, fator de vencimento,
    código de barras e linha digitável —, onde a regra é estrutural e não tem
    banco envolvido: campo livre com 24 posições, código de barras com 43
    dígitos, sequência sem dígito para o módulo 10.

    Distinta de :class:`BoletoInvalido`, que reúne as violações **de regra de
    banco** numa lista.
    """


class ModeloInvalido(PyCobrancaError, ValueError):
    """Documento ou bloco de layout que não existe no catálogo de renderização."""


class DependenciaAusente(PyCobrancaError, RuntimeError):
    """Dependência de renderização faltando na instalação (``reportlab``, ``qrcode``)."""


class OFXInvalido(PyCobrancaError, ValueError):
    """Conteúdo não é um arquivo OFX válido (marcador ausente/estrutura quebrada)."""


class RetornoInvalido(PyCobrancaError, ValueError):
    """Arquivo de retorno CNAB vazio ou sem header reconhecível."""
