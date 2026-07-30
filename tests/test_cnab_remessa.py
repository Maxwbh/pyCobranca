"""Remessa CNAB (400 e 240) — validada byte a byte contra vetores de referência.

As fixtures em ``tests/fixtures/*.rem`` foram geradas por uma implementação de referência (Ruby)
com os mesmos dados de entrada; os testes garantem que a PyCobrança produz
arquivos **byte a byte idênticos** (incluindo CRLF, maiúsculas e remoção de
acentos).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pycobranca.cnab import (
    Pagamento,
    RemessaAilos240,
    RemessaBancoBrasil240,
    RemessaBancoBrasil400,
    RemessaBancoBrasilia400,
    RemessaBancoC6_400,
    RemessaBancoNordeste400,
    RemessaBanrisul400,
    RemessaBradesco400,
    RemessaCaixa240,
    RemessaCitibank400,
    RemessaCredisis400,
    RemessaItau400,
    RemessaSantander240,
    RemessaSantander400,
    RemessaSicoob240,
    RemessaSicoob400,
    RemessaSicredi240,
    RemessaUnicred240,
    RemessaUnicred400,
)
from pycobranca.exceptions import BoletoInvalido

FIXTURES = Path(__file__).parent / "fixtures"


def _pagamentos() -> list[Pagamento]:
    return [
        Pagamento(
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
        ),
        Pagamento(
            valor=1350.75,
            data_vencimento=date(2026, 9, 1),
            data_emissao=date(2026, 7, 23),
            nosso_numero="87654321",
            numero="DOC0002",
            documento_sacado="11222333000181",
            nome_sacado="Empresa Compradora Ltda & Çia",
            endereco_sacado="Av. Paulista, 1578, conj. 405",
            bairro_sacado="Bela Vista",
            cep_sacado="01310200",
            cidade_sacado="São Paulo",
            uf_sacado="SP",
        ),
    ]


_COMUM = dict(empresa_mae="Empresa Exemplo LTDA", documento_cedente="11222333000181")
_COMUM_400 = dict(**_COMUM, data_geracao=date(2026, 7, 23))
_COMUM_240 = dict(
    **_COMUM,
    sequencial_remessa="1",
    data_geracao_fixa="23072026",
    hora_geracao_fixa="120000",
)


def _remessas_400():
    return {
        "itau": RemessaItau400(
            pagamentos=_pagamentos(),
            agencia="0057",
            conta_corrente="12345",
            digito_conta="7",
            carteira="109",
            **_COMUM_400,
        ),
        "bradesco": RemessaBradesco400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="56789",
            digito_conta="0",
            carteira="06",
            codigo_empresa="4587",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banco_brasil": RemessaBancoBrasil400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            convenio="1234567",
            variacao_carteira="019",
            carteira="18",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "santander": RemessaSantander400(
            pagamentos=_pagamentos(),
            codigo_transmissao="9876543210",
            **_COMUM_400,
        ),
        "sicoob": RemessaSicoob400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345678",
            convenio="123456789",
            digito_conta="5",
            carteira="01",
            sequencial_remessa="0000001",
            **_COMUM_400,
        ),
        "unicred": RemessaUnicred400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            digito_conta="5",
            codigo_beneficiario="12345",
            carteira="21",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banrisul": RemessaBanrisul400(
            pagamentos=_pagamentos(),
            agencia="1234",
            convenio="1234567890123",
            carteira="1",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banco_nordeste": RemessaBancoNordeste400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="1234567",
            digito_conta="5",
            carteira="21",
            **_COMUM_400,
        ),
        "banco_brasilia": RemessaBancoBrasilia400(
            pagamentos=_pagamentos(),
            agencia="123",
            conta_corrente="1234567",
            digito_conta="5",
            carteira="1",
            data_formacao="20260723120000",
            **_COMUM_400,
        ),
        "citibank": RemessaCitibank400(
            pagamentos=_pagamentos(),
            portfolio="12345678901234567890",
            carteira="1",
            **_COMUM_400,
        ),
        "credisis": RemessaCredisis400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345678",
            codigo_cedente="1234",
            digito_conta="5",
            carteira="18",
            convenio="1234567",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banco_c6": RemessaBancoC6_400(
            pagamentos=_pagamentos(),
            codigo_beneficiario="123456789012",
            carteira="20",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
    }


def _remessas_240():
    return {
        "ailos": RemessaAilos240(
            pagamentos=_pagamentos(),
            agencia="0134",
            digito_agencia="5",
            conta_corrente="1234567",
            convenio="123456",
            **_COMUM_240,
        ),
        "banco_brasil": RemessaBancoBrasil240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="123456789012",
            convenio="1234567",
            variacao="019",
            carteira="17",
            **_COMUM_240,
        ),
        "caixa": RemessaCaixa240(
            pagamentos=_pagamentos(),
            agencia="1234",
            digito_agencia="5",
            convenio="123456",
            versao_aplicativo="1234",
            conta_corrente="1234567",
            **_COMUM_240,
        ),
        "santander": RemessaSantander240(
            pagamentos=_pagamentos(),
            codigo_transmissao="123456789012345",
            agencia="1234",
            conta_corrente="123456789",
            digito_conta="5",
            **_COMUM_240,
        ),
        "sicoob": RemessaSicoob240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345678",
            convenio="123456",
            modalidade_carteira="01",
            tipo_formulario="4",
            parcela="01",
            digito_conta="5",
            **_COMUM_240,
        ),
        "sicredi": RemessaSicredi240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            byte_idt="2",
            modalidade_carteira="01",
            parcela="01",
            posto="00",
            digito_conta="5",
            **_COMUM_240,
        ),
        "unicred": RemessaUnicred240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            byte_idt="2",
            modalidade_carteira="01",
            parcela="01",
            posto="00",
            digito_conta="5",
            **_COMUM_240,
        ),
    }


@pytest.mark.parametrize("banco", sorted(_remessas_400()))
def test_remessa_cnab400_byte_a_byte(banco: str) -> None:
    remessa = _remessas_400()[banco]
    esperado = (FIXTURES / f"remessa_{banco}_cnab400.rem").read_bytes()
    assert remessa.gera_arquivo().encode("ascii") == esperado


@pytest.mark.parametrize("banco", sorted(_remessas_240()))
def test_remessa_cnab240_byte_a_byte(banco: str) -> None:
    remessa = _remessas_240()[banco]
    esperado = (FIXTURES / f"remessa_{banco}_cnab240.rem").read_bytes()
    assert remessa.gera_arquivo().encode("ascii") == esperado


def test_estrutura_dos_registros_400() -> None:
    remessa = _remessas_400()["itau"]
    linhas = remessa.gera_arquivo().splitlines()
    assert len(linhas) == 4  # header + 2 detalhes + trailer
    assert all(len(linha) == 400 for linha in linhas)
    assert linhas[0].startswith("01REMESSA01COBRANCA")
    assert linhas[-1].startswith("9")
    assert linhas[-1].endswith("000004")


def test_estrutura_dos_registros_240() -> None:
    remessa = _remessas_240()["caixa"]
    linhas = remessa.gera_arquivo().splitlines()
    # header arq + header lote + (P+Q+R)*2 + trailer lote + trailer arq
    assert len(linhas) == 10
    assert all(len(linha) == 240 for linha in linhas)
    assert linhas[0][:3] == "104"
    assert linhas[-1][:8] == "10499999"


def test_remessa_sem_pagamentos_levanta() -> None:
    with pytest.raises(BoletoInvalido):
        RemessaItau400(empresa_mae="X").gera_arquivo()


def test_pagamento_incompleto_levanta() -> None:
    with pytest.raises(BoletoInvalido):
        Pagamento(valor=10.0).validar()
