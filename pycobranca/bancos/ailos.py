"""Ailos (085)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from .base import BancoBase

__all__ = ["Ailos"]


class Ailos(BancoBase):
    codigo: ClassVar[str] = "085"
    nome: ClassVar[str] = "Ailos"
    digito_banco: ClassVar[str] = "1"
    carteiras: ClassVar[tuple[str, ...]] = ("01", "1")
    suporta_pix: ClassVar[bool] = False

    @property
    def dv_conta(self):
        return modulo11_flex(so_digitos(self.conta).zfill(7), mapa={10: 0})

    def nosso_numero_formatado(self) -> str:
        return (
            f"{so_digitos(self.conta).zfill(7)}{self.dv_conta}"
            f"{so_digitos(self.nosso_numero).zfill(9)}"
        )

    def campo_livre(self) -> str:
        # Manual Ailos: convênio(6) + conta com DV(8 = 7+1) + nosso número(9) + carteira(2)
        return (
            f"{so_digitos(self.convenio).zfill(6)}"
            f"{so_digitos(self.conta).zfill(7)}{self.dv_conta}"
            f"{so_digitos(self.nosso_numero).zfill(9)}"
            f"{so_digitos(self.carteira).zfill(2)}"
        )
