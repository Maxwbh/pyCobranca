"""Unicred (136)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from .base import BancoBase

__all__ = ["Unicred"]


class Unicred(BancoBase):
    codigo: ClassVar[str] = "136"
    nome: ClassVar[str] = "Unicred"
    digito_banco: ClassVar[str] = "8"
    carteiras: ClassVar[tuple[str, ...]] = ("21",)
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "conta": (1, 9),
        "nosso_numero": (1, 10),
    }

    @property
    def dv_nosso_numero(self):
        return modulo11_flex(so_digitos(self.nosso_numero).zfill(10), mapa={10: 0, 11: 0})

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(10)}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)} / "
            f"{so_digitos(self.conta).zfill(9)}-{self.digito_conta}"
        )

    def campo_livre(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.conta).zfill(9)}{self.digito_conta}"
            f"{so_digitos(self.nosso_numero).zfill(10)}{self.dv_nosso_numero}"
        )
