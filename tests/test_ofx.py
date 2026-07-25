"""Leitura de extrato OFX, extração de nosso número e conciliação.

Usa extratos OFX reais (dados fictícios) em ``tests/fixtures/ofx/`` — os mesmos
do cobranca-api — para travar o parser e a extração de nosso número, e cobre a
conciliação contra nossos números esperados.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pycobranca.contracts import valida_contrato
from pycobranca.ofx import Extrato, concilia, extrair_nosso_numero

FIXTURES = Path(__file__).parent / "fixtures" / "ofx"


def _extrato(nome: str) -> Extrato:
    return Extrato.ler(FIXTURES / f"extrato_{nome}.ofx")


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #
def test_parser_itau() -> None:
    e = _extrato("itau")
    assert (e.org, e.fid) == ("ITAU", "341")
    assert (e.agencia, e.conta_numero, e.conta_tipo) == ("1234", "56789-0", "CHECKING")
    assert e.saldo_valor == pytest.approx(5230.75)
    assert e.saldo_data == date(2025, 2, 28)
    assert len(e.transacoes) == 2

    credito = e.creditos[0]
    assert credito.tipo == "CREDIT"
    assert credito.data == date(2025, 2, 5)
    assert credito.valor == pytest.approx(890.00)
    assert credito.nosso_numero_extraido == "12345678"  # do memo "RECEBIMENTO BOLETO 12345678"

    debito = e.debitos[0]
    assert debito.tipo == "DEBIT"
    assert debito.valor == pytest.approx(450.00)  # valor absoluto
    assert debito.nosso_numero_extraido is None  # "PAGAMENTO ALUGUEL" não tem nosso número


def test_parser_sicoob_resumo_e_periodo() -> None:
    e = _extrato("sicoob")
    assert (e.org, e.fid) == ("SICOOB", "756")
    assert e.periodo == (date(2025, 1, 15), date(2025, 1, 25))
    d = e.to_dict()
    assert d["resumo"] == {
        "total_transacoes": 4,
        "total_creditos": 2,
        "total_debitos": 2,
        "soma_creditos": pytest.approx(3750.00),
        "soma_debitos": pytest.approx(530.50),
    }
    # nosso número extraído dos créditos Sicoob
    assert [t.nosso_numero_extraido for t in e.creditos] == ["0000012345", "9876543"]


def test_somente_creditos() -> None:
    e = _extrato(
        "sicoob",
    )
    apenas = Extrato.ler(FIXTURES / "extrato_sicoob.ofx", somente_creditos=True)
    assert len(e.transacoes) == 4
    assert len(apenas.transacoes) == 2
    assert all(t.tipo == "CREDIT" for t in apenas.transacoes)


def test_encoding_latin1_em_bytes() -> None:
    """Aceita bytes e normaliza Latin-1 → UTF-8 sem quebrar."""
    conteudo = (FIXTURES / "extrato_itau.ofx").read_bytes()
    e = Extrato.ler(conteudo.decode("utf-8").encode("iso-8859-1"))
    assert e.org == "ITAU"
    assert len(e.transacoes) == 2


# --------------------------------------------------------------------------- #
# Extrator de nosso número (unit)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("memo", "banco", "esperado"),
    [
        ("RECEBIMENTO BOLETO 12345678", "ITAU", "12345678"),
        ("COBRANCA SICOOB 0000012345", "756", "0000012345"),
        ("TARIFA", "341", None),
        ("", "341", None),
        ("PAGAMENTO 123456789012", "BANCO DO BRASIL", "123456789012"),
        ("DOC 12345678901", "bradesco", "12345678901"),
        ("CREDITO 12345678901234567", "caixa", "12345678901234567"),
        ("REF 9998887", "banco_desconhecido", "9998887"),  # genérico
    ],
)
def test_extrair_nosso_numero(memo: str, banco: str, esperado: str | None) -> None:
    assert extrair_nosso_numero(memo, banco) == esperado


# --------------------------------------------------------------------------- #
# Conciliação
# --------------------------------------------------------------------------- #
def test_conciliacao_casa_por_nosso_numero() -> None:
    e = _extrato("sicoob")
    # "12345" casa com "0000012345" (sem zeros à esquerda); "9876543" casa exato.
    resultado = concilia(e, ["12345", "9876543", "55555"])
    assert {nn for _, nn in resultado.conciliadas} == {"12345", "9876543"}
    assert len(resultado.conciliadas) == 2
    assert resultado.pendentes == ["55555"]  # esperado que não apareceu no extrato


@pytest.mark.parametrize("nome", ["itau", "sicoob"])
def test_ofx_to_dict_valida_contrato(nome: str) -> None:
    """A serialização do extrato bate com o schema ``ExtratoOFX`` do contrato REST."""
    valida_contrato(_extrato(nome).to_dict(), "ExtratoOFX")


def test_conciliacao_debito_ignorado_por_padrao() -> None:
    e = _extrato("itau")
    resultado = concilia(e, ["12345678"])
    assert len(resultado.conciliadas) == 1
    assert resultado.conciliadas[0][1] == "12345678"
    assert resultado.nao_conciliadas == []  # débitos não entram (somente_creditos)
    assert resultado.to_dict()["resumo"]["total_conciliadas"] == 1
