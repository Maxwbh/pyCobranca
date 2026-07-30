"""HSBC (399) — carteiras CNR (com data juliana) e CSB. Legado."""

from __future__ import annotations

from datetime import date
from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["HSBC"]


def _juliano(d: date) -> str:
    dias = (d - date(d.year - 1, 12, 31)).days
    return f"{dias}{str(d.year)[3]}".rjust(4, "0")


class HSBC(BancoBase):
    codigo: ClassVar[str] = "399"
    nome: ClassVar[str] = "HSBC"
    digito_banco: ClassVar[str] = "9"
    carteiras: ClassVar[tuple[str, ...]] = ("CNR", "CSB")
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "conta": (1, 7),
        "nosso_numero": (1, 13),
    }

    def nosso_numero_formatado(self) -> str:
        nn = so_digitos(self.nosso_numero).zfill(13)
        if self.carteira == "CNR":
            if self.data_vencimento is None:
                raise BoletoInvalido("data_vencimento é obrigatória para carteira CNR")
            data = self.data_vencimento.strftime("%d%m%y")
            parte1 = f"{nn}{modulo11_flex(nn, mapa={10: 0})}4"
            soma = int(parte1) + int(so_digitos(self.conta).zfill(7)) + int(data)
            return f"{parte1}{modulo11_flex(str(soma), mapa={10: 0})}"
        return nn

    def campo_livre(self) -> str:
        nn = so_digitos(self.nosso_numero).zfill(13)
        if self.carteira == "CNR":
            if self.data_vencimento is None:
                raise BoletoInvalido("data_vencimento é obrigatória para carteira CNR")
            return f"{so_digitos(self.conta).zfill(7)}{nn}{_juliano(self.data_vencimento)}2"
        return f"{nn}{so_digitos(self.agencia).zfill(4)}{so_digitos(self.conta).zfill(7)}001"
