"""Banrisul (041) — campo livre com dígito duplo (módulo 10 + 11)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import duplo_digito
from .base import BancoBase

__all__ = ["Banrisul"]


class Banrisul(BancoBase):
    codigo: ClassVar[str] = "041"
    nome: ClassVar[str] = "Banrisul"
    digito_banco: ClassVar[str] = "8"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "2")
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "convenio": (1, 7),
        "nosso_numero": (1, 8),
    }

    def campo_livre(self) -> str:
        base = (
            f"{so_digitos(self.carteira)[:1] or '2'}1"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.convenio).zfill(7)}"
            f"{so_digitos(self.nosso_numero).zfill(8)}40"
        )
        return base + duplo_digito(base)

    def nosso_numero_formatado(self) -> str:
        nn = so_digitos(self.nosso_numero).zfill(8)
        return f"{nn}-{duplo_digito(nn)}"

    def agencia_conta_formatado(self) -> str:
        convenio = so_digitos(self.convenio).zfill(7)
        agencia = so_digitos(self.agencia).zfill(4)
        return f"{agencia} / {convenio[:6]}.{convenio[6]}.{self.digito_convenio}"
