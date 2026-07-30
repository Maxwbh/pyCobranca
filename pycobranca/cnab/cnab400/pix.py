"""Registro PIX (tipo 8) da remessa CNAB 400 — porta de ``Cnab400::PixMixin``.

O registro tipo 8 (Bolepix) é gerado após o detalhe de cada título quando o
pagamento é um :class:`~pycobranca.cnab.pagamento.PagamentoPix`. As classes
``*Pix`` combinam a remessa do banco com este mixin.
"""

from __future__ import annotations

from ..pagamento import PagamentoPix
from .banco_c6 import RemessaBancoC6_400
from .bradesco import RemessaBradesco400
from .itau import RemessaItau400
from .santander import RemessaSantander400

__all__ = [
    "PixMixinCnab400",
    "RemessaItau400Pix",
    "RemessaBradesco400Pix",
    "RemessaBancoC6_400Pix",
    "RemessaSantander400Pix",
]

#: Tipo de chave DICT → código do layout FEBRABAN.
DICT_MAPPING = {
    "cpf": "1",
    "cnpj": "2",
    "telefone": "3",
    "email": "4",
    "chave_aleatoria": "5",
}


class PixMixinCnab400:
    """Adiciona o registro detalhe PIX (tipo 8, 400 posições)."""

    def monta_detalhe_pix(self, pagamento: PagamentoPix, sequencial: int) -> str:
        pagamento.validar()
        return (
            "8"
            + str(int(pagamento.tipo_pagamento_pix)).rjust(2, "0")
            + str(pagamento.quantidade_pagamentos_pix).rjust(2, "0")
            + str(pagamento.tipo_valor_pix).rjust(1, "0")
            + pagamento.formata_valor_maximo_pix()
            + pagamento.formata_percentual_maximo_pix()
            + pagamento.formata_valor_minimo_pix()
            + pagamento.formata_percentual_minimo_pix()
            + DICT_MAPPING.get(pagamento.tipo_chave_dict, "0")
            + str(pagamento.codigo_chave_dict).ljust(77)
            + str(pagamento.txid or "").ljust(35)
            + " " * 239
            + str(sequencial).rjust(6, "0")
        )


class RemessaItau400Pix(PixMixinCnab400, RemessaItau400):
    """Itaú (341) com Bolepix (registro tipo 8)."""


class RemessaBradesco400Pix(PixMixinCnab400, RemessaBradesco400):
    """Bradesco (237) com Bolepix (registro tipo 8)."""


class RemessaBancoC6_400Pix(PixMixinCnab400, RemessaBancoC6_400):
    """C6 (336) com Bolepix (registro tipo 8)."""


class RemessaSantander400Pix(PixMixinCnab400, RemessaSantander400):
    """Santander (033) com Bolepix (registro tipo 8)."""
