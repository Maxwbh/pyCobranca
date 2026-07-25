"""Santander (033) — campo livre e DV do nosso número.

Campo livre (25): ``9`` (fixo) + código do cedente(7) + nosso número com
DV(13) + IOS ``0`` + carteira(3).

DV do nosso número: módulo 11 (pesos 2..9) sobre os 12 dígitos; DV = ``11 -
resto``; resultados maiores que 9 viram ``0``.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_resto
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["Santander"]


class Santander(BancoBase):
    codigo: ClassVar[str] = "033"
    nome: ClassVar[str] = "Santander"
    digito_banco: ClassVar[str] = "7"
    carteiras: ClassVar[tuple[str, ...]] = ("101", "102", "121")
    suporta_pix: ClassVar[bool] = True

    @property
    def _cedente7(self) -> str:
        return so_digitos(self.convenio or self.conta).zfill(7)

    @property
    def _nosso_numero12(self) -> str:
        return so_digitos(self.nosso_numero).zfill(12)

    @property
    def dv_nosso_numero(self) -> str:
        resto = modulo11_resto(self._nosso_numero12, peso_max=9)
        dv = 11 - resto
        return "0" if dv > 9 else str(dv)

    def campo_livre(self) -> str:
        carteira = so_digitos(self.carteira).zfill(3)
        return f"9{self._cedente7}{self._nosso_numero12}{self.dv_nosso_numero}0{carteira}"

    def nosso_numero_formatado(self) -> str:
        return f"{self._nosso_numero12}-{self.dv_nosso_numero}"

    def validar(self) -> None:
        super().validar()
        erros: list[str] = []
        if len(so_digitos(self.convenio or self.conta)) > 7:
            erros.append("código do cedente (convênio) deve ter até 7 dígitos")
        if len(so_digitos(self.nosso_numero)) > 12:
            erros.append("nosso número deve ter até 12 dígitos")
        if erros:
            raise BoletoInvalido("; ".join(erros))
