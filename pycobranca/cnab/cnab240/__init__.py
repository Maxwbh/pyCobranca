"""Remessa CNAB 240 (estrutura em lotes, padrão FEBRABAN)."""

from .ailos import RemessaAilos240
from .banco_brasil import RemessaBancoBrasil240
from .caixa import RemessaCaixa240
from .santander import RemessaSantander240
from .sicoob import RemessaSicoob240
from .sicredi import RemessaSicredi240
from .unicred import RemessaUnicred240

__all__ = [
    "RemessaAilos240",
    "RemessaBancoBrasil240",
    "RemessaCaixa240",
    "RemessaSantander240",
    "RemessaSicoob240",
    "RemessaSicredi240",
    "RemessaUnicred240",
]
