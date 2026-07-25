"""Sicoob (756) — DV do nosso número com fatores fixos 3-1-9-7 (esq.→dir.)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from .base import BancoBase

__all__ = ["Sicoob"]


class Sicoob(BancoBase):
    codigo: ClassVar[str] = "756"
    nome: ClassVar[str] = "Sicoob"
    digito_banco: ClassVar[str] = "0"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "3", "9", "09")
    suporta_pix: ClassVar[bool] = True

    @property
    def _identificador(self) -> str:
        if self.carteira in ("9", "09") and self.numero_contrato:
            return so_digitos(self.numero_contrato).zfill(7)
        return so_digitos(self.convenio).zfill(7)

    @property
    def dv_nosso_numero(self):
        base = (
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{self._identificador.zfill(10)}"
            f"{so_digitos(self.nosso_numero).zfill(7)}"
        )
        return modulo11_flex(
            base,
            fatores=(3, 1, 9, 7),
            da_direita=False,
            mapa={10: 0, 11: 0},
            bloco=lambda total: 11 - (total % 11),
        )

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(7)}{self.dv_nosso_numero}"

    def campo_livre(self) -> str:
        return (
            f"{so_digitos(self.carteira)[:1]}"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{(so_digitos(self.variacao) or '01').zfill(2)}"
            f"{self._identificador}"
            f"{self.nosso_numero_formatado()}"
            f"{(so_digitos(self.quantidade) or '001').zfill(3)}"
        )
