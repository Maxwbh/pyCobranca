"""Sicoob (756) — DV do nosso número com fatores fixos 3-1-9-7 (esq.→dir.)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo11_flex
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["Sicoob"]


class Sicoob(BancoBase):
    codigo: ClassVar[str] = "756"
    nome: ClassVar[str] = "Sicoob"
    digito_banco: ClassVar[str] = "0"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "3", "9", "09")
    suporta_pix: ClassVar[bool] = True
    # convênio/nº do contrato têm mín. 0 porque o identificador usa um OU outro
    # (nº do contrato na carteira 9; convênio nas demais).
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "convenio": (0, 7),
        "numero_contrato": (0, 7),
        # ``zfill(2)`` no campo livre preenche mas não corta: três dígitos
        # estouram as 25 posições.
        "variacao": (0, 2),
        "nosso_numero": (1, 7),
        # Parcela, 3 posições (23–25 do campo livre): ``zfill(3)`` preenche mas
        # não corta, e o quarto dígito estourava as 25 posições.
        "quantidade": (0, 3),
    }

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

    @property
    def _carteira1(self) -> str:
        """A posição 1 do campo livre: o dígito **significativo** da carteira.

        Era ``so_digitos(self.carteira)[:1]``, que pega o **primeiro** caractere —
        e ``"09"`` virava ``"0"``. Como ``carteiras`` declara ``"9"`` e ``"09"``
        como a mesma coisa (e :attr:`_identificador` já as trata assim), o mesmo
        título saía com dois códigos de barras diferentes conforme a grafia, e o
        da forma preenchida com zero anunciava uma carteira que o Sicoob não tem.

        Nada disso levantava: o código de barras continua com 44 posições e o DV
        é recalculado sobre o valor errado, então ele passa em qualquer
        conferência estrutural. É o mesmo modo de falha do ``portfolio`` do
        Citibank — sai plausível e vai para o banco errado.
        """
        digitos = so_digitos(self.carteira).lstrip("0")
        if len(digitos) > 1:
            raise BoletoInvalido(
                f"carteira {self.carteira!r} não cabe na posição 1 do campo livre "
                f"({len(digitos)} dígitos significativos)"
            )
        return digitos or "0"

    def campo_livre(self) -> str:
        return (
            f"{self._carteira1}"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{(so_digitos(self.variacao) or '01').zfill(2)}"
            f"{self._identificador}"
            f"{self.nosso_numero_formatado()}"
            f"{(so_digitos(self.quantidade) or '001').zfill(3)}"
        )
