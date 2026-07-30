"""CrediSIS (097)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["CrediSIS"]


class CrediSIS(BancoBase):
    codigo: ClassVar[str] = "097"
    nome: ClassVar[str] = "CrediSIS"
    digito_banco: ClassVar[str] = "3"
    carteiras: ClassVar[tuple[str, ...]] = ("18",)
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "convenio": (1, 6),
        "nosso_numero": (1, 6),
    }

    @property
    def dv_documento_cedente(self):
        doc = so_digitos(self.cedente_documento)
        if not doc:
            raise BoletoInvalido("cedente_documento é obrigatório para o CrediSIS")
        return modulo11_flex(doc, mapa={0: 1, 10: 1, 11: 1})

    def nosso_numero_formatado(self) -> str:
        return (
            f"097{self.dv_documento_cedente}"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.convenio).zfill(6)}"
            f"{so_digitos(self.nosso_numero).zfill(6)}"
        )

    def campo_livre(self) -> str:
        return (
            f"00000097{self.dv_documento_cedente}"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.convenio).zfill(6)}"
            f"{so_digitos(self.nosso_numero).zfill(6)}"
        )
