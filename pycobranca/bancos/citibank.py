"""Citibank (745)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from .base import BancoBase

__all__ = ["Citibank"]


class Citibank(BancoBase):
    codigo: ClassVar[str] = "745"
    nome: ClassVar[str] = "Citibank"
    digito_banco: ClassVar[str] = "5"
    carteiras: ClassVar[tuple[str, ...]] = ("3",)
    suporta_pix: ClassVar[bool] = False

    @property
    def dv_nosso_numero(self):
        return modulo11_flex(
            so_digitos(self.nosso_numero).zfill(11),
            fatores=(2, 3, 4, 5, 6, 7, 8, 9),
            mapa={10: 0, 11: 0},
            bloco=lambda total: 11 - (total % 11),
        )

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(11)}.{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return f"{so_digitos(self.agencia).zfill(4)} / {so_digitos(self.convenio).zfill(10)}"

    def campo_livre(self) -> str:
        convenio = so_digitos(self.convenio).zfill(10)
        return (
            f"{so_digitos(self.carteira)[:1]}"
            f"{so_digitos(self.portfolio).zfill(3)}"
            f"{convenio[1:]}"
            f"{so_digitos(self.nosso_numero).zfill(11)}{self.dv_nosso_numero}"
        )
