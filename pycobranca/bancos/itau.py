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
direta as carteiras 126, 131, 145, 150 e 168"*. Mas o anexo 4 do **mesmo manual**, sobre "boletos
emitidos pelo próprio cliente", omite a cláusula das escriturais e lista só as diretas — e ainda
troca ``145`` por ``146``.

Das aceitas aqui, só a **112** usa a composição curta, e por lastro externo, não por leitura.
Ver :data:`Itau._DAC_SEM_AGENCIA_CONTA` para por que 104, 115, 147 e 188 ficam de fora.
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

    #: Carteiras cujo DAC sai de ``carteira + nosso número``, sem agência nem conta.
    #:
    #: A ``112`` é a única das aceitas aqui que entra, e entra com lastro: **duas de três
    #: implementações independentes conferidas** a tratam assim, e dois relatos de campo a
    #: verificaram contra boletos emitidos pelo próprio Itaú. As demais são as diretas que
    #: o manual excetua — a nota 23 escreve ``145`` e o anexo 4 escreve ``146``,
    #: contradição do próprio manual, e nenhuma das duas está em :data:`carteiras`.
    #:
    #: **Não** entram 104, 115, 147 e 188, embora a nota 23 diga "exceto as carteiras
    #: escriturais" e a tabela de carteiras (nota 5) classifique as quatro assim. O anexo
    #: 4, que trata de "boletos emitidos pelo próprio cliente", contradiz a nota 23 e lista
    #: só as diretas; e das três implementações conferidas, nenhuma coloca 115 e 188 na
    #: composição curta. Sem vetor de referência que decida, mudar o código de barras
    #: dessas carteiras pela leitura de um trecho que o próprio manual contradiz seria
    #: quebrar a paridade sem prova.
    _DAC_SEM_AGENCIA_CONTA: ClassVar[frozenset[str]] = frozenset(
        {"112", "126", "131", "145", "146", "150", "168"}
    )

    @property
    def dac_nosso_numero(self) -> int:
        """DAC do nosso número (módulo 10), na composição que a carteira exige.

        As carteiras de :data:`_DAC_SEM_AGENCIA_CONTA` usam ``carteira + nosso número``;
        as demais, ``agência + conta + carteira + nosso número``. Errar a composição
        produz um código de barras **estruturalmente válido e com o dígito errado** — o
        boleto imprime, o banco recusa ou credita em outro título.
        """
        if self.carteira in self._DAC_SEM_AGENCIA_CONTA:
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
