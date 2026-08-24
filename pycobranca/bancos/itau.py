"""Itaú (341) — campo livre e DACs.

Campo livre (25 posições):

| Posições | Conteúdo |
|----------|----------|
| 1–3   | Carteira |
| 4–11  | Nosso número (8) |
| 12    | DAC do nosso número (módulo 10) — a composição varia por carteira |
| 13–16 | Agência (4) |
| 17–21 | Conta (5) |
| 22    | DAC [agência/conta] (módulo 10) |
| 23–25 | ``000`` |

**DAC do nosso número.** O manual (*Cobrança CNAB 400*, jan/2017, nota 23) manda compor
``agência + conta + carteira + nosso número``, *"exceto as carteiras escriturais e na modalidade
direta as carteiras 126, 131, 145, 150 e 168, cujo DAC do 'Nosso Número' é composto apenas dos
campos: Carteira e Nosso Número"*.

Das sete carteiras aceitas aqui, **quatro são escriturais** pela tabela do próprio manual
(nota 5): 104, 112, 115 e 188 — todas na composição curta. A 109 é direta e usa a longa.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo10
from .base import BancoBase

__all__ = ["Itau"]


class Itau(BancoBase):
    codigo: ClassVar[str] = "341"
    nome: ClassVar[str] = "Itaú"
    digito_banco: ClassVar[str] = "7"
    carteiras: ClassVar[tuple[str, ...]] = ("104", "109", "112", "115", "175", "177", "188")
    suporta_pix: ClassVar[bool] = True
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "conta": (1, 5),
        "nosso_numero": (1, 8),
    }

    @property
    def _agencia4(self) -> str:
        return so_digitos(self.agencia).zfill(4)

    @property
    def _conta5(self) -> str:
        return so_digitos(self.conta).zfill(5)

    @property
    def _nosso_numero8(self) -> str:
        return so_digitos(self.nosso_numero).zfill(8)

    #: Carteiras **escriturais** (manual, nota 5): o Itaú mantém o registro e devolve o
    #: nosso número. Todas entram na composição curta do DAC.
    _ESCRITURAIS: ClassVar[frozenset[str]] = frozenset({"104", "112", "115", "147", "188"})

    #: Carteiras **diretas** que o manual excetua. A nota 23 lista ``145`` e o anexo 4 lista
    #: ``146`` — a contradição é do próprio manual. Nenhuma das duas está em
    #: :data:`carteiras`, então as duas ficam aqui até que um vetor de referência decida.
    _DIRETAS_DAC_CURTO: ClassVar[frozenset[str]] = frozenset(
        {"126", "131", "145", "146", "150", "168"}
    )

    @property
    def dac_nosso_numero(self) -> int:
        """DAC do nosso número (módulo 10), na composição que a carteira exige.

        Escriturais e as diretas excetuadas usam ``carteira + nosso número``; as demais,
        ``agência + conta + carteira + nosso número``. Aplicar a composição longa numa
        carteira escritural produz um código de barras **estruturalmente válido e com o
        dígito errado** — o boleto imprime, o banco recusa ou credita em outro título.
        """
        if self.carteira in self._ESCRITURAIS or self.carteira in self._DIRETAS_DAC_CURTO:
            return modulo10(f"{self.carteira}{self._nosso_numero8}")
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
