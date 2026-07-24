"""Itaú (341) — campo livre e DACs.

Campo livre (25 posições):

| Posições | Conteúdo |
|----------|----------|
| 1–3   | Carteira |
| 4–11  | Nosso número (8) |
| 12    | DAC [agência/conta/carteira/nosso número] (módulo 10) |
| 13–16 | Agência (4) |
| 17–21 | Conta (5) |
| 22    | DAC [agência/conta] (módulo 10) |
| 23–25 | ``000`` |
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo10
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["Itau"]


class Itau(BancoBase):
    codigo: ClassVar[str] = "341"
    nome: ClassVar[str] = "Itaú"
    digito_banco: ClassVar[str] = "7"
    carteiras: ClassVar[tuple[str, ...]] = ("104", "109", "112", "115", "175", "177", "188")
    suporta_pix: ClassVar[bool] = True

    @property
    def _agencia4(self) -> str:
        return so_digitos(self.agencia).zfill(4)

    @property
    def _conta5(self) -> str:
        return so_digitos(self.conta).zfill(5)

    @property
    def _nosso_numero8(self) -> str:
        return so_digitos(self.nosso_numero).zfill(8)

    @property
    def dac_nosso_numero(self) -> int:
        """DAC do nosso número: módulo 10 de agência+conta+carteira+nosso número."""
        return modulo10(f"{self._agencia4}{self._conta5}{self.carteira}{self._nosso_numero8}")

    @property
    def dac_conta(self) -> int:
        """DAC da conta: módulo 10 de agência+conta."""
        return modulo10(f"{self._agencia4}{self._conta5}")

    def campo_livre(self) -> str:
        return (
            f"{self.carteira}{self._nosso_numero8}{self.dac_nosso_numero}"
            f"{self._agencia4}{self._conta5}{self.dac_conta}000"
        )

    def nosso_numero_formatado(self) -> str:
        return f"{self.carteira}/{self._nosso_numero8}-{self.dac_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return f"{self._agencia4} / {self._conta5}-{self.dac_conta}"

    def validar(self) -> None:
        super().validar()
        erros: list[str] = []
        if len(so_digitos(self.agencia)) > 4:
            erros.append("agência deve ter até 4 dígitos")
        if len(so_digitos(self.conta)) > 5:
            erros.append("conta deve ter até 5 dígitos")
        if len(self._nosso_numero8) != 8:
            erros.append("nosso número deve ter até 8 dígitos")
        if erros:
            raise BoletoInvalido("; ".join(erros))
