"""Datas da cobrança: fator de vencimento FEBRABAN.

O fator de vencimento são 4 dígitos do código de barras que codificam a data
de vencimento como dias corridos desde a base 07/10/1997. O fator atingiu
9999 em 21/02/2025; a partir de 22/02/2025 vale a regra de reinício da
FEBRABAN: a contagem recomeça em 1000.
"""

from __future__ import annotations

from datetime import date, timedelta

from ..exceptions import DadosInvalidos

__all__ = ["fator_vencimento", "data_do_fator", "BASE_FATOR", "ROLLOVER_FATOR"]

BASE_FATOR = date(1997, 10, 7)
ROLLOVER_FATOR = date(2025, 2, 22)  # neste dia o fator volta a valer 1000


def fator_vencimento(vencimento: date) -> int:
    """Calcula o fator de vencimento (4 dígitos) para a data.

    Antes de 22/02/2025: dias corridos desde 07/10/1997 (03/07/2000 → 1000).
    De 22/02/2025 em diante: ``1000 + dias desde 22/02/2025`` (regra de
    reinício da FEBRABAN).
    """
    if vencimento < BASE_FATOR:
        raise DadosInvalidos(f"vencimento anterior à base do fator: {vencimento}")
    if vencimento < ROLLOVER_FATOR:
        fator = (vencimento - BASE_FATOR).days
    else:
        fator = 1000 + (vencimento - ROLLOVER_FATOR).days
    if fator > 9999:
        raise DadosInvalidos(f"fator de vencimento fora do intervalo (>{9999}): {vencimento}")
    return fator


def data_do_fator(fator: int, *, referencia: date | None = None) -> date:
    """Data de vencimento correspondente a um fator lido de um boleto/retorno.

    Como o fator é ambíguo após o reinício, ``referencia`` (padrão: hoje)
    decide a época: fatores lidos a partir de 22/02/2025 usam a nova base.
    """
    if not 0 < fator <= 9999:
        raise DadosInvalidos(f"fator inválido: {fator}")
    referencia = referencia or date.today()
    if referencia >= ROLLOVER_FATOR and fator >= 1000:
        return ROLLOVER_FATOR + timedelta(days=fator - 1000)
    return BASE_FATOR + timedelta(days=fator)
