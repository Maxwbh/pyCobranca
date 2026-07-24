"""Banco do Nordeste (004)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from .base import BancoBase

__all__ = ["BancoNordeste"]


class BancoNordeste(BancoBase):
    codigo: ClassVar[str] = "004"
    nome: ClassVar[str] = "Banco do Nordeste"
    digito_banco: ClassVar[str] = "3"
    carteiras: ClassVar[tuple[str, ...]] = ("21", "31", "41", "51")
    suporta_pix: ClassVar[bool] = False

    @property
    def dv_nosso_numero(self):
        return modulo11_flex(
            so_digitos(self.nosso_numero).zfill(7),
            fatores=(2, 3, 4, 5, 6, 7, 8),
            mapa={10: 0, 11: 0},
            bloco=lambda total: 11 - (total % 11),
        )

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(7)}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)}/"
            f"{so_digitos(self.conta).zfill(7)}-{self.digito_conta}"
        )

    def campo_livre(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.conta).zfill(7)}{self.digito_conta}"
            f"{so_digitos(self.nosso_numero).zfill(7)}{self.dv_nosso_numero}"
            f"{so_digitos(self.carteira).zfill(2)}000"
        )
