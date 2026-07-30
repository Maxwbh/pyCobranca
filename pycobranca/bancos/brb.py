"""BRB — Banco de Brasília (070) — campo livre com dígito duplo."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import duplo_digito
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["BRB"]


class BRB(BancoBase):
    codigo: ClassVar[str] = "070"
    nome: ClassVar[str] = "BRB"
    digito_banco: ClassVar[str] = "1"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "2")
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "incremento": (1, 3),
        "agencia": (1, 3),
        "conta": (1, 7),
        "nosso_numero": (1, 6),
    }

    def _campo_livre_base(self) -> str:
        if not self.incremento:
            raise BoletoInvalido("incremento (3 dígitos) é obrigatório para o BRB")
        return (
            f"{so_digitos(self.incremento).zfill(3)}"
            f"{so_digitos(self.agencia).zfill(3)}"
            f"{so_digitos(self.conta).zfill(7)}"
            f"{so_digitos(self.carteira)[:1]}"
            f"{so_digitos(self.nosso_numero).zfill(6)}070"
        )

    def campo_livre(self) -> str:
        base = self._campo_livre_base()
        return base + duplo_digito(base)

    def nosso_numero_formatado(self) -> str:
        cl = self.campo_livre()
        return (
            f"{so_digitos(self.carteira)[:1]}{so_digitos(self.nosso_numero).zfill(6)}070{cl[-2:]}"
        )

    def agencia_conta_formatado(self) -> str:
        return f"000 - {so_digitos(self.agencia).zfill(3)} - {so_digitos(self.conta).zfill(7)}"
