"""Sicredi (748) — nosso número com ano + byte identificador."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["Sicredi"]

_MAPA = {10: 0, 11: 0}


class Sicredi(BancoBase):
    codigo: ClassVar[str] = "748"
    nome: ClassVar[str] = "Sicredi"
    digito_banco: ClassVar[str] = "X"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "3")
    suporta_pix: ClassVar[bool] = False

    @property
    def _nosso_numero_com_byte(self) -> str:
        if self.data_documento is None:
            raise BoletoInvalido(
                "data_documento é obrigatória para o Sicredi (ano do nosso número)"
            )
        if not self.byte_idt:
            raise BoletoInvalido("byte_idt é obrigatório (1=agência, 2-9=beneficiário)")
        ano = self.data_documento.strftime("%y")
        return f"{ano}{self.byte_idt}{so_digitos(self.nosso_numero).zfill(5)}"

    @property
    def _agencia_posto_conta(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.posto).zfill(2)}"
            f"{so_digitos(self.convenio).zfill(5)}"
        )

    @property
    def dv_nosso_numero(self):
        base = f"{self._agencia_posto_conta}{self._nosso_numero_com_byte}"
        return modulo11_flex(base, mapa=_MAPA)

    def nosso_numero_formatado(self) -> str:
        nn = self._nosso_numero_com_byte
        return f"{nn[:2]}/{nn[2:]}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return (
            f"{so_digitos(self.agencia).zfill(4)}.{so_digitos(self.posto).zfill(2)}"
            f".{so_digitos(self.convenio).zfill(5)}"
        )

    def campo_livre(self) -> str:
        nosso_cb = f"{self._nosso_numero_com_byte}{self.dv_nosso_numero}"
        base = f"{so_digitos(self.carteira)[:1]}1{nosso_cb}{self._agencia_posto_conta}10"
        return base + str(modulo11_flex(base, mapa=_MAPA))
