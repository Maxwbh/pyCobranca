"""CNAB — geração de remessa no padrão FEBRABAN.

Validado **byte a byte** contra vetores de referência para os mesmos dados de
entrada. Layouts implementados:

- **CNAB 400** — Itaú (341), Bradesco (237), Banco do Brasil (001),
  Santander (033), Sicoob (756), Unicred (136), Banrisul (041),
  Banco do Nordeste (004), Banco de Brasília/BRB (070, formato DCB),
  Citibank (745), CrediSIS (097) e C6 (336).
- **CNAB 240** — Ailos (085), Banco do Brasil (001), Caixa (104),
  Santander (033), Sicoob (756), Sicredi (748) e Unicred (136).
"""

from .cnab240 import (
    RemessaAilos240,
    RemessaBancoBrasil240,
    RemessaCaixa240,
    RemessaSantander240,
    RemessaSicoob240,
    RemessaSicredi240,
    RemessaUnicred240,
)
from .cnab240.pix import (
    RemessaBancoBrasil240Pix,
    RemessaCaixa240Pix,
    RemessaSicoob240Pix,
)
from .cnab400 import (
    RemessaBancoBrasil400,
    RemessaBancoBrasilia400,
    RemessaBancoC6_400,
    RemessaBancoNordeste400,
    RemessaBanrisul400,
    RemessaBradesco400,
    RemessaCitibank400,
    RemessaCredisis400,
    RemessaInter400,
    RemessaItau400,
    RemessaSantander400,
    RemessaSicoob400,
    RemessaUnicred400,
)
from .cnab400.pix import (
    RemessaBancoC6_400Pix,
    RemessaBradesco400Pix,
    RemessaItau400Pix,
    RemessaSantander400Pix,
)
from .pagamento import Pagamento, PagamentoPix
from .retorno import RegistroRetorno, Retorno, descreve_ocorrencia

__all__ = [
    "Pagamento",
    "PagamentoPix",
    # Remessa PIX (Bolepix)
    "RemessaItau400Pix",
    "RemessaBradesco400Pix",
    "RemessaBancoC6_400Pix",
    "RemessaSantander400Pix",
    "RemessaBancoBrasil240Pix",
    "RemessaCaixa240Pix",
    "RemessaSicoob240Pix",
    # Retorno (Fase 3)
    "Retorno",
    "RegistroRetorno",
    "descreve_ocorrencia",
    # CNAB 400
    "RemessaItau400",
    "RemessaBradesco400",
    "RemessaBancoBrasil400",
    "RemessaSantander400",
    "RemessaSicoob400",
    "RemessaUnicred400",
    "RemessaBanrisul400",
    "RemessaBancoNordeste400",
    "RemessaBancoBrasilia400",
    "RemessaCitibank400",
    "RemessaCredisis400",
    "RemessaInter400",
    "RemessaBancoC6_400",
    # CNAB 240
    "RemessaAilos240",
    "RemessaBancoBrasil240",
    "RemessaCaixa240",
    "RemessaSantander240",
    "RemessaSicoob240",
    "RemessaSicredi240",
    "RemessaUnicred240",
]
