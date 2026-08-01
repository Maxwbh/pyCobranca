"""Banestes (021) — DV duplo no nosso número e dígito duplo no campo livre."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import duplo_digito, modulo11_flex
from .base import BancoBase

__all__ = ["Banestes"]

_MAPA = {10: 0, 11: 0}


class Banestes(BancoBase):
    codigo: ClassVar[str] = "021"
    nome: ClassVar[str] = "Banestes"
    digito_banco: ClassVar[str] = "3"
    carteiras: ClassVar[tuple[str, ...]] = ("11", "13")
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "conta": (1, 10),
        "nosso_numero": (1, 8),
    }

    @property
    def dv_nosso_numero(self) -> str:
        nn = so_digitos(self.nosso_numero).zfill(8)
        dv1 = modulo11_flex(nn, mapa=_MAPA)
        dv2 = modulo11_flex(f"{nn}{dv1}", mapa=_MAPA)
        return f"{dv1}{dv2}"

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(8)}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return (
            f"{int(so_digitos(self.agencia) or 0)} / "
            f"{int(so_digitos(self.conta) or 0)}{self.digito_conta}"
        )

    def campo_livre(self) -> str:
        base = (
            f"{so_digitos(self.nosso_numero).zfill(8)}"
            f"{so_digitos(self.conta).zfill(10)}{self.digito_conta}"
            f"{(so_digitos(self.variacao) or '2')[:1]}021"
        )
        return base + duplo_digito(base)
