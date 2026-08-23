"""Montagem das 44 posições do código de barras FEBRABAN.

Estrutura:

| Posições | Conteúdo |
|----------|----------|
| 1–3   | Código do banco |
| 4     | Código da moeda (9 = Real) |
| 5     | DV geral (módulo 11) |
| 6–9   | Fator de vencimento |
| 10–19 | Valor (10 dígitos, em centavos) |
| 20–44 | Campo livre (25 posições, definido por banco) |
"""

from __future__ import annotations

from ..core.dv import modulo11_codigo_barras
from ..exceptions import DadosInvalidos

__all__ = ["montar_codigo_barras"]


def montar_codigo_barras(
    banco: str, fator: int, valor_centavos: int, campo_livre: str, *, moeda: str = "9"
) -> str:
    """Monta o código de barras completo (44 dígitos), calculando o DV geral.

    Args:
        banco: código FEBRABAN do banco (3 dígitos).
        fator: fator de vencimento (4 dígitos).
        valor_centavos: valor do documento em centavos (até 10 dígitos).
        campo_livre: 25 posições específicas do banco.
        moeda: código da moeda (padrão ``"9"`` = Real).

    Returns:
        String de 44 dígitos com o DV geral na posição 5.
    """
    banco = str(banco).zfill(3)
    if len(banco) != 3 or not banco.isdigit():
        raise DadosInvalidos(f"código de banco inválido: {banco!r}")
    if not 0 < int(fator) <= 9999:
        raise DadosInvalidos(f"fator de vencimento inválido: {fator!r}")
    if not 0 <= int(valor_centavos) < 10**10:
        raise DadosInvalidos(f"valor em centavos inválido: {valor_centavos!r}")
    campo_livre = str(campo_livre)
    if len(campo_livre) != 25 or not campo_livre.isdigit():
        raise DadosInvalidos(f"campo livre deve ter 25 dígitos: {campo_livre!r}")

    sem_dv = f"{banco}{moeda}{int(fator):04d}{int(valor_centavos):010d}{campo_livre}"
    dv = modulo11_codigo_barras(sem_dv)
    return f"{banco}{moeda}{dv}{int(fator):04d}{int(valor_centavos):010d}{campo_livre}"
