"""Testes de contrato REST (OpenAPI 3.0).

Garantem que os artefatos da engine (boleto, remessa, retorno) serializam para
os schemas do OpenAPI 3.0 — validados pelo contrato vendorizado
em ``pycobranca/contracts/contrato_rest.json``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pycobranca.bancos import Bancos
from pycobranca.cnab.retorno import Retorno
from pycobranca.contracts import (
    SLUG_POR_CODIGO,
    boleto_para_api,
    pagamento_para_api,
    remessa_para_api,
    retorno_item_para_api,
    valida_contrato,
)
from pycobranca.contracts.contrato_rest import ErroDeContrato

FIXTURES = Path(__file__).parent / "fixtures"


def _boleto(cls):
    return cls(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="12345678000190",
        agencia="1234",
        conta="56789",
        carteira=(cls.carteiras[0] if getattr(cls, "carteiras", None) else "01"),
        nosso_numero="12345678",
        numero_documento="NF-2026-001",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
        convenio="1234567",
    )


@pytest.mark.parametrize("cls", Bancos.todos(), ids=lambda c: c.codigo)
def test_boleto_serializa_no_contrato_boletodata(cls) -> None:
    payload = boleto_para_api(_boleto(cls))
    assert payload["bank"] == SLUG_POR_CODIGO.get(cls.codigo, cls.codigo)
    valida_contrato(payload["data"], "BoletoData")


def test_boleto_data_tem_campos_obrigatorios() -> None:
    from pycobranca.bancos.itau import Itau

    data = boleto_para_api(_boleto(Itau))["data"]
    for campo in ("agencia", "conta_corrente", "nosso_numero", "valor", "cedente"):
        assert campo in data
    assert isinstance(data["valor"], float)


def test_pagamento_serializa_no_contrato() -> None:
    from pycobranca.cnab import Pagamento

    pagamento = Pagamento(
        valor=199.90,
        data_vencimento=date(2026, 8, 15),
        nosso_numero="12345678",
        numero="DOC0001",
        documento_sacado="52998224725",
        nome_sacado="Cliente Final",
        endereco_sacado="Rua das Flores, 100",
        bairro_sacado="Centro",
        cep_sacado="30110000",
        cidade_sacado="Belo Horizonte",
        uf_sacado="MG",
    )
    dados = pagamento_para_api(pagamento)
    valida_contrato(dados, "Pagamento")
    assert dados["nome_sacado"] == "Cliente Final"
    assert dados["numero_documento"] == "DOC0001"
    assert isinstance(dados["valor"], float)


def test_remessa_serializa_no_contrato_remessarequest() -> None:
    from pycobranca.cnab import Pagamento, RemessaItau400

    remessa = RemessaItau400(
        pagamentos=[
            Pagamento(
                valor=199.90,
                data_vencimento=date(2026, 8, 15),
                nosso_numero="12345678",
                numero="DOC0001",
                documento_sacado="52998224725",
                nome_sacado="Cliente Final",
                endereco_sacado="Rua das Flores, 100",
                bairro_sacado="Centro",
                cep_sacado="30110000",
                cidade_sacado="Belo Horizonte",
                uf_sacado="MG",
            )
        ],
        empresa_mae="Empresa Exemplo LTDA",
        documento_cedente="11222333000181",
        agencia="0057",
        conta_corrente="12345",
        digito_conta="7",
        carteira="109",
    )
    dados = remessa_para_api(remessa)
    valida_contrato(dados, "RemessaRequest")  # também valida cada Pagamento via $ref
    assert dados["pagamentos"][0]["nosso_numero"] == "12345678"
    assert isinstance(dados["sequencial_remessa"], int)


def test_retorno_item_serializa_no_contrato() -> None:
    retorno = Retorno.ler(FIXTURES / "retorno" / "CNAB400ITAU.RET")
    item = retorno_item_para_api(retorno.registros[0], layout=retorno.layout)
    valida_contrato(item, "RetornoItem")
    # centavos -> reais em float
    assert item["valor_titulo"] == 40.00
    assert item["valor_pago"] == 37.90
    assert item["motivo_ocorrencia"] == "Liquidação normal"


def test_retorno_todos_os_itens_validos() -> None:
    for arq in ("CNAB400BRADESCO.RET", "CNAB240SICOOB.RET"):
        retorno = Retorno.ler(FIXTURES / "retorno" / arq)
        for registro in retorno.registros:
            item = retorno_item_para_api(registro, layout=retorno.layout)
            valida_contrato(item, "RetornoItem")


def test_validador_rejeita_obrigatorio_ausente() -> None:
    with pytest.raises(ErroDeContrato):
        valida_contrato({"agencia": "1234"}, "BoletoData")


def test_validador_rejeita_tipo_incorreto() -> None:
    dados = {
        "agencia": "1234",
        "conta_corrente": "56789",
        "nosso_numero": "1",
        "valor": "127.50",  # deveria ser number, não string
        "cedente": "X",
        "documento_cedente": "1",
        "sacado": "Y",
        "sacado_documento": "1",
    }
    with pytest.raises(ErroDeContrato):
        valida_contrato(dados, "BoletoData")
