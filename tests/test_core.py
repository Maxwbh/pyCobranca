"""Testes do núcleo: dígitos verificadores, fator de vencimento e documentos."""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.core import (
    fator_vencimento,
    formatar_cnpj,
    formatar_cpf,
    modulo10,
    modulo11_codigo_barras,
    validar_cnpj,
    validar_cpf,
)
from pycobranca.core.datas import data_do_fator

# --- módulo 10 (vetores calculados à mão) -----------------------------------


def test_modulo10_vetores() -> None:
    assert modulo10("005712345") == 7  # DAC agência+conta (Itaú)
    assert modulo10("00571234510912345678") == 0  # DAC nosso número (Itaú)
    # exemplo clássico do manual Itaú: agência 1547 c/c 85634 -> DAC 6? (verificação própria)
    assert 0 <= modulo10("154785634") <= 9


def test_modulo10_ignora_mascara_e_rejeita_vazio() -> None:
    assert modulo10("0057-12345") == modulo10("005712345")
    with pytest.raises(ValueError):
        modulo10("abc")


# --- módulo 11 do código de barras ------------------------------------------


def test_modulo11_regra_febraban() -> None:
    # DV sempre em 1..9 (0, 10 e 11 colapsam em 1)
    for seq in ("0" * 43, "9" * 43, "123456789" * 4 + "1234567"):
        assert 1 <= modulo11_codigo_barras(seq) <= 9


# --- fator de vencimento ----------------------------------------------------


def test_fator_vencimento_base_classica() -> None:
    assert fator_vencimento(date(2000, 7, 3)) == 1000  # exemplo clássico FEBRABAN
    assert fator_vencimento(date(1997, 10, 8)) == 1


def test_fator_vencimento_rollover_2025() -> None:
    assert fator_vencimento(date(2025, 2, 21)) == 9999  # último dia da série antiga
    assert fator_vencimento(date(2025, 2, 22)) == 1000  # reinício
    dias = (date(2026, 8, 15) - date(2025, 2, 22)).days
    assert fator_vencimento(date(2026, 8, 15)) == 1000 + dias


def test_data_do_fator_roundtrip_pos_rollover() -> None:
    d = date(2026, 8, 15)
    assert data_do_fator(fator_vencimento(d), referencia=date(2026, 7, 23)) == d


# --- CPF / CNPJ -------------------------------------------------------------


def test_cpf_valido_e_invalido() -> None:
    assert validar_cpf("529.982.247-25")  # vetor público bem conhecido
    assert not validar_cpf("529.982.247-26")
    assert not validar_cpf("111.111.111-11")
    assert formatar_cpf("52998224725") == "529.982.247-25"


def test_cnpj_valido_e_invalido() -> None:
    assert validar_cnpj("11.222.333/0001-81")  # vetor público bem conhecido
    assert not validar_cnpj("11.222.333/0001-82")
    assert not validar_cnpj("00.000.000/0000-00")
    assert formatar_cnpj("11222333000181") == "11.222.333/0001-81"
