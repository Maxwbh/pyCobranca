"""Banco do Brasil (001) — campo livre por tamanho de convênio.

O layout do campo livre (25 posições) varia com o convênio:

- **Convênio 7** (mais comum): ``000000`` + convênio(7) + sequencial(10) + carteira(2).
- **Convênio 6**: convênio(6) + sequencial(5) + agência(4) + conta(8) + carteira(2).
- **Convênio 4**: convênio(4) + sequencial(7) + agência(4) + conta(8) + carteira(2).

No convênio 7 o nosso número são 17 dígitos (convênio + sequencial), sem DV.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["BancoDoBrasil"]

_SEQUENCIAL_POR_CONVENIO = {7: 10, 6: 5, 4: 7}


class BancoDoBrasil(BancoBase):
    codigo: ClassVar[str] = "001"
    nome: ClassVar[str] = "Banco do Brasil"
    digito_banco: ClassVar[str] = "9"
    carteiras: ClassVar[tuple[str, ...]] = ("11", "12", "15", "16", "17", "18", "31", "51")
    suporta_pix: ClassVar[bool] = True

    @property
    def _convenio(self) -> str:
        return so_digitos(self.convenio)

    @property
    def _sequencial(self) -> str:
        tamanho = _SEQUENCIAL_POR_CONVENIO[len(self._convenio)]
        return so_digitos(self.nosso_numero).zfill(tamanho)

    def campo_livre(self) -> str:
        convenio = self._convenio
        carteira = so_digitos(self.carteira).zfill(2)
        if len(convenio) == 7:
            return f"000000{convenio}{self._sequencial}{carteira}"
        agencia = so_digitos(self.agencia).zfill(4)
        conta = so_digitos(self.conta).zfill(8)
        return f"{convenio}{self._sequencial}{agencia}{conta}{carteira}"

    def nosso_numero_formatado(self) -> str:
        if len(self._convenio) == 7:
            return f"{self._convenio}{self._sequencial}"
        return self._sequencial

    def validar(self) -> None:
        super().validar()
        erros: list[str] = []
        if len(self._convenio) not in _SEQUENCIAL_POR_CONVENIO:
            erros.append("convênio deve ter 4, 6 ou 7 dígitos")
        else:
            maximo = _SEQUENCIAL_POR_CONVENIO[len(self._convenio)]
            if len(so_digitos(self.nosso_numero)) > maximo:
                erros.append(f"nosso número deve ter até {maximo} dígitos para este convênio")
        if erros:
            raise BoletoInvalido("; ".join(erros))
