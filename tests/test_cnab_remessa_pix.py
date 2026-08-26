"""Remessa com segmento PIX (Bolepix) — validada byte a byte contra vetores de referência.

CNAB 400 acrescenta o **registro tipo 8** e CNAB 240 o **segmento Y-03** após o
detalhe/segmentos de cada título ``PagamentoPix``. As fixtures foram geradas
por uma implementação de referência com os mesmos dados.

Divergência arbitrada pela FEBRABAN (CNAB 240 com PIX): a **quantidade de
registros do arquivo** no trailer de arquivo conta **todos** os registros físicos
(tipos 0/1/3/5/9), incluindo os segmentos Y. A implementação de referência omitia
os segmentos Y dessa contagem (o trailer de lote os contava, o de arquivo não), o
que um validador de intake rejeitaria. Os fixtures ``*_pix_cnab240.rem`` refletem
a contagem correta (ver ``tests/test_cnab_estrutura.py``).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pycobranca.cnab import (
    PagamentoPix,
    RemessaBancoBrasil240Pix,
    RemessaBancoC6_400Pix,
    RemessaBradesco400Pix,
    RemessaCaixa240Pix,
    RemessaItau400Pix,
    RemessaSantander400Pix,
    RemessaSicoob240Pix,
)
from pycobranca.exceptions import BoletoInvalido

FIXTURES = Path(__file__).parent / "fixtures"


def _pagamentos() -> list[PagamentoPix]:
    return [
        PagamentoPix(
            valor=199.90,
            data_vencimento=date(2026, 8, 15),
            data_emissao=date(2026, 7, 23),
            nosso_numero="12345678",
            numero="DOC0001",
            documento_sacado="52998224725",
            nome_sacado="Cliente Final da Silva",
            endereco_sacado="Rua das Flores, 100",
            bairro_sacado="Centro",
            cep_sacado="30110000",
            cidade_sacado="Belo Horizonte",
            uf_sacado="MG",
            tipo_chave_dict="cnpj",
            codigo_chave_dict="11222333000181",
            txid="TX2026080100000000000000001",
        ),
        PagamentoPix(
            valor=1350.75,
            data_vencimento=date(2026, 9, 1),
            data_emissao=date(2026, 7, 23),
            nosso_numero="87654321",
            numero="DOC0002",
            documento_sacado="11222333000181",
            nome_sacado="Empresa Compradora Ltda & Cia",
            endereco_sacado="Av. Paulista, 1578",
            bairro_sacado="Bela Vista",
            cep_sacado="01310200",
            cidade_sacado="Sao Paulo",
            uf_sacado="SP",
            tipo_chave_dict="email",
            codigo_chave_dict="cobranca@empresa.com.br",
            txid="TX2026090100000000000000002",
        ),
    ]


_COMUM = dict(empresa_mae="Empresa Exemplo LTDA", documento_cedente="11222333000181")
_C400 = dict(**_COMUM, data_geracao=date(2026, 7, 23))
_C240 = dict(
    **_COMUM, sequencial_remessa="1", data_geracao_fixa="23072026", hora_geracao_fixa="120000"
)


def _remessas():
    return {
        ("cnab400", "itau"): RemessaItau400Pix(
            pagamentos=_pagamentos(),
            agencia="0057",
            conta_corrente="12345",
            digito_conta="7",
            carteira="109",
            **_C400,
        ),
        ("cnab400", "bradesco"): RemessaBradesco400Pix(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="56789",
            digito_conta="0",
            carteira="06",
            codigo_empresa="4587",
            sequencial_remessa="1",
            **_C400,
        ),
        ("cnab400", "banco_c6"): RemessaBancoC6_400Pix(
            pagamentos=_pagamentos(),
            codigo_beneficiario="123456789012",
            carteira="20",
            sequencial_remessa="1",
            **_C400,
        ),
        ("cnab400", "santander"): RemessaSantander400Pix(
            pagamentos=_pagamentos(),
            codigo_transmissao="9876543210",
            **_C400,
        ),
        ("cnab240", "banco_brasil"): RemessaBancoBrasil240Pix(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="123456789012",
            convenio="1234567",
            variacao="019",
            carteira="17",
            **_C240,
        ),
        ("cnab240", "caixa"): RemessaCaixa240Pix(
            pagamentos=_pagamentos(),
            agencia="1234",
            digito_agencia="5",
            convenio="123456",
            versao_aplicativo="1234",
            conta_corrente="1234567",
            **_C240,
        ),
        ("cnab240", "sicoob"): RemessaSicoob240Pix(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345678",
            convenio="123456",
            modalidade_carteira="01",
            parcela="01",
            digito_conta="5",
            **_C240,
        ),
    }


@pytest.mark.parametrize(("layout", "banco"), sorted(_remessas()))
def test_remessa_pix_byte_a_byte(layout, banco) -> None:
    remessa = _remessas()[(layout, banco)]
    esperado = (FIXTURES / f"remessa_{banco}_pix_{layout}.rem").read_bytes()
    assert remessa.gera_arquivo().encode("latin-1") == esperado


def test_registro_tipo_8_presente_no_400() -> None:
    remessa = _remessas()[("cnab400", "itau")]
    linhas = remessa.gera_arquivo().splitlines()
    # header + (detalhe + registro 8) x2 + trailer = 6 linhas
    assert len(linhas) == 6
    registros_pix = [linha for linha in linhas if linha.startswith("8")]
    assert len(registros_pix) == 2
    assert all(len(linha) == 400 for linha in linhas)


def test_segmento_y_presente_no_240() -> None:
    remessa = _remessas()[("cnab240", "sicoob")]
    linhas = remessa.gera_arquivo().splitlines()
    segmentos_y = [linha for linha in linhas if linha[13:14] == "Y"]
    assert len(segmentos_y) == 2
    assert all(len(linha) == 240 for linha in linhas)


def test_pagamento_pix_sem_chave_levanta() -> None:
    with pytest.raises(BoletoInvalido):
        PagamentoPix(
            valor=10.0,
            data_vencimento=date(2026, 8, 15),
            nosso_numero="1",
            documento_sacado="52998224725",
            nome_sacado="X",
            endereco_sacado="Y",
            cep_sacado="30110000",
        ).validar()


def test_pagamento_pix_tipo_chave_invalido_levanta() -> None:
    with pytest.raises(BoletoInvalido):
        PagamentoPix(
            valor=10.0,
            data_vencimento=date(2026, 8, 15),
            nosso_numero="1",
            documento_sacado="52998224725",
            nome_sacado="X",
            endereco_sacado="Y",
            cep_sacado="30110000",
            codigo_chave_dict="11222333000181",
            tipo_chave_dict="pix",
        ).validar()
