"""Linha digitável (IPTE) a partir do código de barras.

A linha digitável rearranja as 44 posições do código de barras em 5 campos:

- Campo 1: banco (3) + moeda (1) + campo livre[1..5] + DV módulo 10
- Campo 2: campo livre[6..15] + DV módulo 10
- Campo 3: campo livre[16..25] + DV módulo 10
- Campo 4: DV geral do código de barras (1 dígito)
- Campo 5: fator de vencimento (4) + valor (10)

Formato: ``AAABC.CCCCD DDDDD.DDDDDE EEEEE.EEEEEF G HHHHIIIIIIIIII``.
"""

from __future__ import annotations

from ..core.dv import modulo10
from ..exceptions import DadosInvalidos

__all__ = ["linha_digitavel"]


def linha_digitavel(codigo_barras: str) -> str:
    """Gera a linha digitável formatada a partir das 44 posições."""
    cb = str(codigo_barras)
    if len(cb) != 44 or not cb.isdigit():
        raise DadosInvalidos(f"código de barras deve ter 44 dígitos: {codigo_barras!r}")

    banco_moeda = cb[0:4]
    dv_geral = cb[4]
    fator_valor = cb[5:19]
    campo_livre = cb[19:44]

    campo1 = banco_moeda + campo_livre[0:5]
    campo2 = campo_livre[5:15]
    campo3 = campo_livre[15:25]

    c1 = f"{campo1}{modulo10(campo1)}"
    c2 = f"{campo2}{modulo10(campo2)}"
    c3 = f"{campo3}{modulo10(campo3)}"

    return (
        f"{c1[0:5]}.{c1[5:10]} {c2[0:5]}.{c2[5:11]} {c3[0:5]}.{c3[5:11]} {dv_geral} {fator_valor}"
    )
