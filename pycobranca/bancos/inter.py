"""Banco Inter (077) — campo livre da carteira 110.

Campo livre (25 posições), conforme o *Manual CNAB400 — Emissão boletos de cobrança*
(Inter, v2.2, 26/08/2024), seção 7.1.3:

| Posições | Tam. | Conteúdo |
|----------|------|----------|
| 1–4   | 4  | Agência sem DV — ``0001`` |
| 5–7   | 3  | Carteira |
| 8–14  | 7  | Número da operação |
| 15–25 | 11 | Nosso número **com DV** (10 + 1) |

**Só a carteira 110.** O Inter tem duas modalidades com modelos opostos de atribuição do
nosso número, e apenas uma é componível fora de linha:

- **110** — o Inter entrega antes uma faixa de nossos números; a empresa monta o boleto e
  manda o arquivo, que o banco apenas registra. Tudo o que o código de barras exige já está
  na mão de quem emite.
- **112** — o Inter emite e numera; o nosso número **só existe no arquivo retorno**. Antes
  disso não há código de barras a montar, e nenhum algoritmo supre isso: falta o dado.

Por isso :data:`Inter.carteiras` traz apenas ``110``. Aceitar a 112 produziria um título
que imprime, passa em conferência estrutural e carrega um nosso número que o banco nunca
emitiu — ver *ausências permanentes* em ``docs/05-bancos-suportados.md``.

O manual observa (seção 6) que a 110 depende de enquadramento em perfil de relacionamento
Inter Empresas; a 112 é a modalidade automática de toda conta.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo10
from .base import BancoBase

__all__ = ["Inter"]


class Inter(BancoBase):
    codigo: ClassVar[str] = "077"
    nome: ClassVar[str] = "Banco Inter"
    digito_banco: ClassVar[str] = "9"
    carteiras: ClassVar[tuple[str, ...]] = ("110",)
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        # Agência opcional: o Inter é digital e tem agência única. Mínimo 0 aceita a
        # omissão; o máximo continua barrando valor fora de faixa.
        "agencia": (0, 4),
        "convenio": (1, 7),
        "nosso_numero": (1, 10),
    }

    #: Agência única do Inter, usada quando o chamador não informa nenhuma.
    AGENCIA_PADRAO: ClassVar[str] = "0001"

    @property
    def _agencia4(self) -> str:
        digitos = so_digitos(self.agencia)
        return digitos.zfill(4) if digitos else self.AGENCIA_PADRAO

    @property
    def _carteira3(self) -> str:
        return so_digitos(self.carteira).zfill(3)

    @property
    def _operacao7(self) -> str:
        """Número da operação — o identificador do cliente junto ao Inter."""
        return so_digitos(self.convenio).zfill(7)

    @property
    def _nosso_numero10(self) -> str:
        return so_digitos(self.nosso_numero).zfill(10)

    @property
    def dac_nosso_numero(self) -> int:
        """DV do nosso número: módulo 10 de ``agência + carteira + nosso número``.

        Manual, seção 7.3 — 17 dígitos, pesos 2,1 da direita para a esquerda, com os
        produtos maiores que 9 somados algarismo a algarismo. É o módulo 10 da FEBRABAN,
        já implementado em :func:`pycobranca.core.dv.modulo10`; o exemplo do manual
        (``00011100004309540`` → soma 29, resto 9, DV 1) confere.
        """
        return modulo10(f"{self._agencia4}{self._carteira3}{self._nosso_numero10}")

    def campo_livre(self) -> str:
        return (
            f"{self._agencia4}{self._carteira3}{self._operacao7}"
            f"{self._nosso_numero10}{self.dac_nosso_numero}"
        )

    def nosso_numero_formatado(self) -> str:
        return f"{self._nosso_numero10}-{self.dac_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        conta = so_digitos(self.conta)
        return f"{self._agencia4} / {conta}" if conta else self._agencia4
