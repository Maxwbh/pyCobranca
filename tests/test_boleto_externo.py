"""Regressão do validador de boleto contra boletos bancários **reais** externos.

Usa o **mesmo** verificador FEBRABAN independente que confere os boletos que a
PyCobrança gera (``test_validacao_externa.py``), agora aplicado a linhas
digitáveis e códigos de barras **reais** publicados por validadores de terceiros.
Se o nosso validador aceita boletos reais de banco, a lógica de DV (módulo 10 nos
campos, módulo 11 geral) e a reconstrução linha↔código estão corretas nas duas
pontas — geração e leitura.

Vetores (dados factuais, não obra autoral) extraídos de validadores públicos:

- boleto-brasileiro-validator — https://github.com/mcrvaz/boleto-brasileiro-validator
- validador-de-boletos — https://github.com/amendoncabh/validador-de-boletos
"""

from __future__ import annotations

import pytest
from test_validacao_externa import (
    _dv_geral_modulo11,
    _dv_modulo10,
    _reconstroi_codigo_barras,
    _so_digitos,
)

# Linhas digitáveis bancárias reais (47 dígitos) e o banco emissor esperado.
LINHAS_REAIS = [
    ("237", "23793381286000782713695000063305975520000370000"),  # Bradesco
    ("237", "23793380296099605290241006333300689690000143014"),  # Bradesco
]

# Códigos de barras reais (44 dígitos).
CODIGOS_REAIS = [
    ("001", "00193373700000001000500940144816060680935031"),  # Banco do Brasil
]


@pytest.mark.parametrize(("banco", "linha"), LINHAS_REAIS)
def test_linha_digitavel_real_valida(banco: str, linha: str) -> None:
    d = _so_digitos(linha)
    assert len(d) == 47, f"linha digitável deve ter 47 dígitos, tem {len(d)}"
    # DVs de campo (módulo 10)
    assert _dv_modulo10(d[0:9]) == int(d[9]), "DV do campo 1 (módulo 10) inválido"
    assert _dv_modulo10(d[10:20]) == int(d[20]), "DV do campo 2 (módulo 10) inválido"
    assert _dv_modulo10(d[21:31]) == int(d[31]), "DV do campo 3 (módulo 10) inválido"
    # reconstrói o código de barras e confere o DV geral (módulo 11)
    cb = _reconstroi_codigo_barras(d)
    assert cb[0:3] == banco, f"banco reconstruído {cb[0:3]} ≠ {banco}"
    assert cb[3] == "9", "moeda deveria ser 9 (Real)"
    assert _dv_geral_modulo11(cb[0:4] + cb[5:]) == int(cb[4]), "DV geral (módulo 11) inválido"


@pytest.mark.parametrize(("banco", "codigo"), CODIGOS_REAIS)
def test_codigo_barras_real_valido(banco: str, codigo: str) -> None:
    cb = _so_digitos(codigo)
    assert len(cb) == 44, f"código de barras deve ter 44 dígitos, tem {len(cb)}"
    assert cb[0:3] == banco, f"banco {cb[0:3]} ≠ {banco}"
    assert _dv_geral_modulo11(cb[0:4] + cb[5:]) == int(cb[4]), "DV geral (módulo 11) inválido"
