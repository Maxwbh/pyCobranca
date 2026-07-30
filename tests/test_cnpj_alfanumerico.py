"""CNPJ alfanumérico (IN RFB 2.229/2024; primeiras emissões a partir de 31/07/2026).

As 12 primeiras posições podem ter letras ``A``–``Z``; os 2 DVs seguem numéricos,
calculados por módulo 11 com o valor de cada caractere igual a ``ord(c) - 48``.
O CPF continua exclusivamente numérico.
"""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.bancos import CrediSIS, Itau
from pycobranca.cnab import Pagamento, RemessaItau400
from pycobranca.core.documentos import (
    cnpj_e_alfanumerico,
    dv_cnpj,
    formatar_cnpj,
    formatar_documento,
    so_alfanumerico,
    validar_cnpj,
    validar_cpf,
)
from pycobranca.exceptions import BoletoInvalido

CNPJ_ALFA = "12ABC34501DE35"
CNPJ_NUM = "11222333000181"
CPF = "52998224725"


# ---- núcleo: validação ----


def test_valida_cnpj_alfanumerico() -> None:
    assert validar_cnpj(CNPJ_ALFA)


def test_valida_cnpj_alfanumerico_com_mascara() -> None:
    assert validar_cnpj("12.ABC.345/01DE-35")


def test_valida_cnpj_alfanumerico_minusculo() -> None:
    assert validar_cnpj("12abc34501de35")


def test_rejeita_dv_errado() -> None:
    assert not validar_cnpj("12ABC34501DE99")


def test_rejeita_dv_com_letra() -> None:
    """Os 2 últimos dígitos verificadores continuam numéricos."""
    assert not validar_cnpj("12ABC34501DEA5")


def test_rejeita_caractere_invalido() -> None:
    assert not validar_cnpj("12@BC34501DE35")


def test_dv_calculado() -> None:
    assert dv_cnpj("12ABC34501DE") == "35"


def test_dv_numerico_inalterado() -> None:
    """Para CNPJ numérico o cálculo é idêntico ao de sempre."""
    assert dv_cnpj("112223330001") == "81"


# ---- retrocompatibilidade: numérico e CPF ----


def test_cnpj_numerico_continua_valido() -> None:
    assert validar_cnpj(CNPJ_NUM)
    assert validar_cnpj("11.222.333/0001-81")


def test_cnpj_numerico_invalido_continua_invalido() -> None:
    assert not validar_cnpj("11222333000182")


def test_cpf_inalterado() -> None:
    assert validar_cpf(CPF)
    assert validar_cpf("529.982.247-25")
    assert not validar_cpf("11111111111")


def test_cpf_com_letras_e_invalido() -> None:
    """CPF continua exclusivamente numérico."""
    assert not validar_cpf("529982247A5")


# ---- helpers ----


def test_so_alfanumerico_preserva_letras() -> None:
    assert so_alfanumerico("12.ABC.345/01DE-35") == CNPJ_ALFA


def test_detecta_alfanumerico() -> None:
    assert cnpj_e_alfanumerico(CNPJ_ALFA)
    assert not cnpj_e_alfanumerico(CNPJ_NUM)


def test_formata_preservando_letras() -> None:
    assert formatar_cnpj(CNPJ_ALFA) == "12.ABC.345/01DE-35"
    assert formatar_cnpj(CNPJ_NUM) == "11.222.333/0001-81"


def test_formata_documento_por_tamanho() -> None:
    assert formatar_documento(CPF) == "529.982.247-25"
    assert formatar_documento(CNPJ_ALFA) == "12.ABC.345/01DE-35"


# ---- boleto ----


def _itau(**kwargs) -> Itau:
    base = dict(
        valor="127.50",
        cedente="EMPRESA NOVA LTDA",
        agencia="1234",
        conta="56789",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
    )
    base.update(kwargs)
    return Itau(**base)


def test_boleto_aceita_cnpj_alfanumerico() -> None:
    boleto = _itau(cedente_documento=CNPJ_ALFA, sacado_documento=CNPJ_ALFA)
    boleto.validar()  # não deve levantar
    assert len(boleto.codigo_barras) == 44


def test_boleto_rejeita_cnpj_alfanumerico_invalido() -> None:
    with pytest.raises(BoletoInvalido, match="cedente_documento inválido"):
        _itau(cedente_documento="12ABC34501DE99").validar()


# ---- CNAB ----


def _pagamento(documento: str) -> Pagamento:
    return Pagamento(
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        valor=199.90,
        documento_sacado=documento,
        nome_sacado="Empresa Nova",
        endereco_sacado="Rua X, 1",
        cep_sacado="01001000",
        cidade_sacado="Sao Paulo",
        uf_sacado="SP",
    )


def test_tipo_inscricao_cnpj_alfanumerico() -> None:
    """Regressão: as letras não podem sumir e fazer o CNPJ virar CPF."""
    assert _pagamento(CNPJ_ALFA).identificacao_sacado() == "02"


def test_tipo_inscricao_cpf_e_cnpj_numerico() -> None:
    assert _pagamento(CPF).identificacao_sacado() == "01"
    assert _pagamento(CNPJ_NUM).identificacao_sacado() == "02"


def test_remessa_preserva_cnpj_alfanumerico() -> None:
    remessa = RemessaItau400(
        empresa_mae="EMPRESA NOVA LTDA",
        documento_cedente=CNPJ_ALFA,
        agencia="1234",
        conta_corrente="56789",
        digito_conta="7",
        carteira="109",
        pagamentos=[_pagamento(CNPJ_ALFA)],
    )
    linhas = remessa.gera_arquivo().splitlines()
    assert all(len(linha) == 400 for linha in linhas)
    detalhe = linhas[1]
    assert CNPJ_ALFA in detalhe  # documento gravado sem perder as letras
    assert detalhe[1:3] == "02"  # tipo de inscrição do sacado = CNPJ


# ---- limitação conhecida ----


def test_contrato_rest_aceita_cnpj_alfanumerico() -> None:
    """O contrato tem `pattern` nos documentos: a API valida o formato antes da engine."""
    from pycobranca.contracts import valida_contrato

    base = dict(
        banco="341",
        valor=127.5,
        cedente="X",
        agencia="1234",
        conta_corrente="56789",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento="2026-08-15",
        sacado="C",
        sacado_documento=CPF,
    )
    for doc in (CNPJ_ALFA, "12.ABC.345/01DE-35", CNPJ_NUM, "529.982.247-25", CPF):
        valida_contrato(dict(base, documento_cedente=doc), "BoletoData")


def test_contrato_rest_rejeita_documento_malformado() -> None:
    from pycobranca.contracts import ErroDeContrato, valida_contrato

    base = dict(
        banco="341",
        valor=127.5,
        cedente="X",
        agencia="1234",
        conta_corrente="56789",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento="2026-08-15",
        sacado="C",
        sacado_documento=CPF,
    )
    with pytest.raises(ErroDeContrato, match="padrão"):
        valida_contrato(dict(base, documento_cedente="12@BC34501DE35"), "BoletoData")


def test_credisis_recusa_cnpj_alfanumerico() -> None:
    """O campo livre do CrediSIS embute um DV do documento; o manual não cobre letras."""
    boleto = CrediSIS(
        valor="127.50",
        cedente="EMPRESA NOVA LTDA",
        cedente_documento=CNPJ_ALFA,
        agencia="1234",
        convenio="123456",
        carteira="18",
        nosso_numero="123456",
        data_vencimento=date(2026, 8, 15),
    )
    with pytest.raises(BoletoInvalido, match="CNPJ alfanumérico"):
        _ = boleto.codigo_barras
