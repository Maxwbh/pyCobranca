"""Registro programático de bancos.

Uso::

    from pycobranca.bancos import Bancos

    Banco = Bancos.find("341")   # -> classe Itau
    Bancos.todos()               # -> [Itau, ...]
    Bancos.com_pix()             # -> bancos com suporte a Bolepix
"""

from __future__ import annotations

from ..exceptions import BancoNaoRegistrado
from .ailos import Ailos
from .banco_do_brasil import BancoDoBrasil
from .banco_nordeste import BancoNordeste
from .banestes import Banestes
from .banrisul import Banrisul
from .base import REGISTRO, BancoBase
from .bradesco import Bradesco
from .brb import BRB
from .c6 import C6
from .caixa import Caixa
from .citibank import Citibank
from .credisis import CrediSIS
from .hsbc import HSBC
from .itau import Itau
from .safra import Safra
from .santander import Santander
from .sicoob import Sicoob
from .sicredi import Sicredi
from .unicred import Unicred

__all__ = [
    "Bancos",
    "BancoBase",
    "Ailos",
    "BancoDoBrasil",
    "BancoNordeste",
    "Banestes",
    "Banrisul",
    "Bradesco",
    "BRB",
    "C6",
    "Caixa",
    "Citibank",
    "CrediSIS",
    "HSBC",
    "Itau",
    "Safra",
    "Santander",
    "Sicoob",
    "Sicredi",
    "Unicred",
]


class Bancos:
    """Consulta ao registro de bancos (preenchido por auto-registro)."""

    @staticmethod
    def todos() -> list[type[BancoBase]]:
        return sorted(REGISTRO.values(), key=lambda b: b.codigo)

    @staticmethod
    def find(codigo: str) -> type[BancoBase]:
        chave = str(codigo).zfill(3)
        try:
            return REGISTRO[chave]
        except KeyError:
            raise BancoNaoRegistrado(chave) from None

    @staticmethod
    def com_pix() -> list[type[BancoBase]]:
        return [b for b in Bancos.todos() if b.suporta_pix]
