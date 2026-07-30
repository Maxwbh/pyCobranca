"""Segmento Y-03 (PIX) da remessa CNAB 240 — porta de ``Cnab240::PixMixin``.

O segmento Y-03 (Bolepix) é opcional e vem após os segmentos P/Q/R de cada
título quando o pagamento é um :class:`~pycobranca.cnab.pagamento.PagamentoPix`.
As classes ``*Pix`` combinam a remessa do banco com este mixin.
"""

from __future__ import annotations

from ..pagamento import PagamentoPix
from .banco_brasil import RemessaBancoBrasil240
from .caixa import RemessaCaixa240
from .sicoob import RemessaSicoob240

__all__ = [
    "PixMixinCnab240",
    "RemessaBancoBrasil240Pix",
    "RemessaCaixa240Pix",
    "RemessaSicoob240Pix",
]

#: Tipo de chave DICT → código do layout FEBRABAN.
DICT_MAPPING = {
    "cpf": "1",
    "cnpj": "2",
    "telefone": "3",
    "email": "4",
    "chave_aleatoria": "5",
}


class PixMixinCnab240:
    """Adiciona o segmento Y-03 (PIX, 240 posições)."""

    def monta_segmento_y(self, pagamento: PagamentoPix, nro_lote: int, sequencial: int) -> str:
        pagamento.validar()
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "3"
            + str(sequencial).rjust(5, "0")
            + "Y"
            + " " * 2
            + "03"
            + "00000"
            + " " * 4
            + DICT_MAPPING.get(pagamento.tipo_chave_dict, "0")
            + str(pagamento.codigo_chave_dict).ljust(77)
            + str(pagamento.txid or "").ljust(35)
            + " " * 100
        )


class RemessaBancoBrasil240Pix(PixMixinCnab240, RemessaBancoBrasil240):
    """Banco do Brasil (001) com Bolepix (segmento Y-03)."""


class RemessaCaixa240Pix(PixMixinCnab240, RemessaCaixa240):
    """Caixa (104) com Bolepix (segmento Y-03)."""


class RemessaSicoob240Pix(PixMixinCnab240, RemessaSicoob240):
    """Sicoob (756) com Bolepix (segmento Y-03)."""
