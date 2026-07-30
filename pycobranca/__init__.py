"""PyCobrança — plataforma de cobrança bancária brasileira em Python.

Uma única biblioteca para boleto (código de barras, linha digitável e PDF),
CNAB 240/400 (remessa e retorno) e PIX/Bolepix, para 18 bancos, em Python puro.
"""

from __future__ import annotations

__all__ = ["__version__", "banco_info", "BANCOS", "Bancos", "BancoBase"]

__version__ = "1.0.2"


def _bancos() -> dict[str, str]:
    """Mapa ``código FEBRABAN -> nome`` de **todos** os bancos registrados.

    Derivado do registro (``pycobranca.bancos.REGISTRO``) — fonte única de
    verdade, sempre em sincronia com os bancos efetivamente suportados.
    """
    from .bancos import REGISTRO

    return {codigo: cls.nome for codigo, cls in sorted(REGISTRO.items())}


def __getattr__(nome: str):
    # imports tardios para manter o import do pacote leve
    if nome in ("Bancos", "BancoBase"):
        from . import bancos

        return getattr(bancos, nome)
    if nome == "BANCOS":
        return _bancos()
    raise AttributeError(f"module {__name__!r} has no attribute {nome!r}")


def banco_info(codigo: str) -> str:
    """Retorna o nome do banco a partir do código FEBRABAN.

    Args:
        codigo: Código FEBRABAN de 3 dígitos (ex.: ``"341"``); zeros à esquerda
            são preenchidos automaticamente (``"1"`` -> ``"001"``).

    Returns:
        Nome do banco correspondente.

    Raises:
        KeyError: Se o código não estiver registrado.
    """
    from .bancos import REGISTRO

    codigo = str(codigo).zfill(3)
    if codigo not in REGISTRO:
        raise KeyError(f"Banco não registrado: {codigo!r}")
    return REGISTRO[codigo].nome
