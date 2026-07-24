"""Caixa Econômica Federal (104) — SIGCB.

Nosso número (17): modalidade(2) + sequencial(15). Modalidades comuns:
``14`` (registrada, emissão beneficiário) e ``24`` (sem registro).

Campo livre (25):

| Posições | Conteúdo |
|----------|----------|
| 1–6   | Código do beneficiário (6) |
| 7     | DV do código do beneficiário (módulo 11) |
| 8–10  | Nosso número — posições 3 a 5 |
| 11    | Tipo de cobrança (1º dígito do nosso número) |
| 12–14 | Nosso número — posições 6 a 8 |
| 15    | Identificador de emissão (2º dígito do nosso número) |
| 16–24 | Nosso número — posições 9 a 17 |
| 25    | DV do campo livre (módulo 11 das 24 posições) |

Módulo 11 Caixa: pesos 2..9; DV = ``11 - resto``; DV > 9 → ``0``.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_resto
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["Caixa"]


def _dv11_caixa(sequencia: str) -> str:
    dv = 11 - modulo11_resto(sequencia, peso_max=9)
    return "0" if dv > 9 else str(dv)


class Caixa(BancoBase):
    codigo: ClassVar[str] = "104"
    nome: ClassVar[str] = "Caixa Econômica Federal"
    digito_banco: ClassVar[str] = "0"
    carteiras: ClassVar[tuple[str, ...]] = ("14", "24")  # modalidade SIGCB
    suporta_pix: ClassVar[bool] = True

    @property
    def _beneficiario6(self) -> str:
        return so_digitos(self.convenio).zfill(6)

    @property
    def _nosso_numero17(self) -> str:
        modalidade = so_digitos(self.carteira).zfill(2)
        return f"{modalidade}{so_digitos(self.nosso_numero).zfill(15)}"

    @property
    def dv_beneficiario(self) -> str:
        return _dv11_caixa(self._beneficiario6)

    def campo_livre(self) -> str:
        nn = self._nosso_numero17
        sem_dv = (
            f"{self._beneficiario6}{self.dv_beneficiario}{nn[2:5]}{nn[0]}{nn[5:8]}{nn[1]}{nn[8:17]}"
        )
        return f"{sem_dv}{_dv11_caixa(sem_dv)}"

    @property
    def dv_nosso_numero(self) -> str:
        """DV do nosso número (17 posições), módulo 11 Caixa — manual SIGCB."""
        return _dv11_caixa(self._nosso_numero17)

    def nosso_numero_formatado(self) -> str:
        # Manual SIGCB: 17 posições + DV, impresso como "XX999999999999999-D"
        return f"{self._nosso_numero17}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return f"{so_digitos(self.agencia).zfill(4)} / {self._beneficiario6}-{self.dv_beneficiario}"

    def validar(self) -> None:
        super().validar()
        erros: list[str] = []
        if len(so_digitos(self.convenio)) > 6:
            erros.append("código do beneficiário (convênio) deve ter até 6 dígitos")
        if len(so_digitos(self.nosso_numero)) > 15:
            erros.append("nosso número deve ter até 15 dígitos")
        if erros:
            raise BoletoInvalido("; ".join(erros))
