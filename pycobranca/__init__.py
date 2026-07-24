"""PyCobrança — plataforma de cobrança bancária brasileira em Python.

Uma única biblioteca para boleto (código de barras, linha digitável e PDF),
CNAB 240/400 (remessa e retorno) e PIX/Bolepix, para 18 bancos, em Python puro.
"""

from __future__ import annotations

__all__ = ["__version__", "banco_info", "BANCOS", "Bancos", "BancoBase"]

__version__ = "1.0.0"


def __getattr__(nome: str):
    # import tardio para manter o import do pacote leve
    if nome in ("Bancos", "BancoBase"):
        from . import bancos

        return getattr(bancos, nome)
    raise AttributeError(f"module {__name__!r} has no attribute {nome!r}")


#: Registro inicial de metadados de bancos (código FEBRABAN -> nome).
#: A implementação completa (classes ``BancoBase``) chega na Fase 1.
BANCOS: dict[str, str] = {
    "001": "Banco do Brasil",
    "033": "Santander",
    "041": "Banrisul",
    "070": "BRB",
    "104": "Caixa Econômica Federal",
    "237": "Bradesco",
    "341": "Itaú",
    "748": "Sicredi",
    "756": "Sicoob",
}


def banco_info(codigo: str) -> str:
    """Retorna o nome do banco a partir do código FEBRABAN.

    Args:
        codigo: Código FEBRABAN de 3 dígitos (ex.: ``"341"``).

    Returns:
        Nome do banco correspondente.

    Raises:
        KeyError: Se o código não estiver registrado.
    """
    codigo = str(codigo).zfill(3)
    if codigo not in BANCOS:
        raise KeyError(f"Banco não registrado: {codigo!r}")
    return BANCOS[codigo]
