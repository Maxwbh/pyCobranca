"""Safra (422) — DV do nosso número calculado da esquerda para a direita."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["Safra"]


class Safra(BancoBase):
    codigo: ClassVar[str] = "422"
    nome: ClassVar[str] = "Safra"
    digito_banco: ClassVar[str] = "7"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "2")
    suporta_pix: ClassVar[bool] = False

    @property
    def dv_nosso_numero(self):
        return modulo11_flex(
            so_digitos(self.nosso_numero).zfill(8),
            da_direita=False,
            mapa={10: 0, 11: 1},
            bloco=lambda total: 11 - (total % 11),
        )

    def nosso_numero_formatado(self) -> str:
        return f"{so_digitos(self.nosso_numero).zfill(8)}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)}{self.digito_agencia} / "
            f"{so_digitos(self.conta).zfill(8)}{self.digito_conta}"
        )

    def campo_livre(self) -> str:
        if not (self.digito_agencia and self.digito_conta):
            raise BoletoInvalido("digito_agencia e digito_conta são obrigatórios para o Safra")
        return (
            f"7{so_digitos(self.agencia).zfill(4)}{self.digito_agencia}"
            f"{so_digitos(self.conta).zfill(8)}{self.digito_conta}"
            f"{so_digitos(self.nosso_numero).zfill(8)}{self.dv_nosso_numero}2"
        )
