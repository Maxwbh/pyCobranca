"""Bradesco (237) — campo livre e DV do nosso número.

Campo livre (25): agência(4) + carteira(2) + nosso número(11) + conta(7) + ``0``.

DV do nosso número: módulo 11 **base 7** (pesos 2..7) sobre carteira + nosso
número; resto 1 → ``P``, resto 0 → ``0``, demais → ``11 - resto``.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_resto
from .base import BancoBase

__all__ = ["Bradesco"]


class Bradesco(BancoBase):
    codigo: ClassVar[str] = "237"
    nome: ClassVar[str] = "Bradesco"
    digito_banco: ClassVar[str] = "2"
    carteiras: ClassVar[tuple[str, ...]] = ("03", "06", "09", "19", "21", "22", "25", "26")
    suporta_pix: ClassVar[bool] = True
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "conta": (1, 7),
        "nosso_numero": (1, 11),
    }

    @property
    def _agencia4(self) -> str:
        return so_digitos(self.agencia).zfill(4)

    @property
    def _conta7(self) -> str:
        return so_digitos(self.conta).zfill(7)

    @property
    def _nosso_numero11(self) -> str:
        return so_digitos(self.nosso_numero).zfill(11)

    @property
    def dv_nosso_numero(self) -> str:
        carteira = so_digitos(self.carteira).zfill(2)
        resto = modulo11_resto(f"{carteira}{self._nosso_numero11}", peso_max=7)
        if resto == 0:
            return "0"
        if resto == 1:
            return "P"
        return str(11 - resto)

    def campo_livre(self) -> str:
        carteira = so_digitos(self.carteira).zfill(2)
        return f"{self._agencia4}{carteira}{self._nosso_numero11}{self._conta7}0"

    def nosso_numero_formatado(self) -> str:
        carteira = so_digitos(self.carteira).zfill(2)
        return f"{carteira}/{self._nosso_numero11}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return f"{self._agencia4} / {self._conta7}"
