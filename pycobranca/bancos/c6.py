"""C6 Bank (336) — layout CNAB 400 v2.7 (julho/2025)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from .base import BancoBase

__all__ = ["C6"]


class C6(BancoBase):
    codigo: ClassVar[str] = "336"
    nome: ClassVar[str] = "C6 Bank"
    digito_banco: ClassVar[str] = "7"
    carteiras: ClassVar[tuple[str, ...]] = ("10", "20")
    suporta_pix: ClassVar[bool] = True

    @property
    def dv_nosso_numero(self) -> str:
        base = f"0{so_digitos(self.carteira).zfill(2)}{so_digitos(self.nosso_numero).zfill(10)}"
        return str(
            modulo11_flex(
                base,
                fatores=(2, 3, 4, 5, 6, 7),
                mapa={10: "P", 11: 0},
                bloco=lambda total: 11 - (total % 11),
            )
        )

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(10)}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return f"{so_digitos(self.agencia).zfill(4)} / {so_digitos(self.convenio).zfill(12)}"

    def campo_livre(self) -> str:
        indicador = "4" if so_digitos(self.carteira).zfill(2) == "20" else "3"
        return (
            f"{so_digitos(self.convenio).zfill(12)}"
            f"{so_digitos(self.nosso_numero).zfill(10)}"
            f"{so_digitos(self.carteira).zfill(2)}{indicador}"
        )
