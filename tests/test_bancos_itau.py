"""Itaú (341) ponta a ponta: campo livre, código de barras, linha digitável e PDF."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pycobranca.bancos import BancoBase, Bancos, Itau
from pycobranca.exceptions import BancoNaoRegistrado, BoletoInvalido


def boleto_exemplo(**kwargs) -> Itau:
    dados = dict(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11.222.333/0001-81",
        cedente_endereco="Av. Central, 1000 - São Paulo/SP",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        data_documento=date(2026, 7, 23),
        numero_documento="DOC-2026-0001",
        sacado="Cliente Final da Silva",
        sacado_documento="529.982.247-25",
        sacado_endereco="Rua das Flores, 100 - Belo Horizonte/MG",
    )
    dados.update(kwargs)
    return Itau(**dados)


# --- registro ----------------------------------------------------------------


def test_registro_de_bancos() -> None:
    assert Bancos.find("341") is Itau
    assert Bancos.find(341) is Itau  # aceita sem zeros à esquerda
    assert Itau in Bancos.todos()
    assert Itau in Bancos.com_pix()
    with pytest.raises(BancoNaoRegistrado):
        Bancos.find("999")


# --- campo livre e DACs (valores calculados à mão) ---------------------------


def test_dacs_e_campo_livre() -> None:
    b = boleto_exemplo()
    assert b.dac_conta == 7  # módulo 10 de "005712345"
    assert b.dac_nosso_numero == 0  # módulo 10 de "00571234510912345678"
    # carteira(109) + nn(12345678) + DAC nn(0) + agência(0057) + conta(12345) + DAC(7) + "000"
    assert b.campo_livre() == "1091234567800057123457000"
    assert len(b.campo_livre()) == 25


# --- DAC do nosso número: a composição muda por carteira ---------------------
#
# Manual *Cobrança CNAB 400* (jan/2017), nota 23: o DAC sai de
# agência+conta+carteira+nosso número, "exceto as carteiras escriturais e na
# modalidade direta as carteiras 126, 131, 145, 150 e 168, cujo DAC do 'Nosso
# Número' é composto apenas dos campos: Carteira e Nosso Número".
#
# Pela tabela de carteiras do próprio manual (nota 5), 104, 112, 115 e 188 são
# ESCRITURAIS e 109 é DIRETA. A biblioteca aplicava a composição longa nas sete,
# o que dava boleto válido em estrutura e com o dígito errado nas quatro
# escriturais (issue #40, confirmada contra boletos emitidos pelo próprio Itaú).


@pytest.mark.parametrize(
    ("carteira", "dac"),
    [("104", 2), ("112", 5), ("115", 8), ("188", 5)],
)
def test_carteira_escritural_usa_so_carteira_e_nosso_numero(carteira, dac) -> None:
    b = boleto_exemplo(carteira=carteira)
    assert b.dac_nosso_numero == dac
    assert b.campo_livre().startswith(f"{carteira}12345678{dac}")


def test_carteira_direta_usa_agencia_e_conta_no_dac() -> None:
    """A 109 é direta: nada muda para quem já emitia — e o vetor de referência prova."""
    assert boleto_exemplo(carteira="109").dac_nosso_numero == 0


@pytest.mark.parametrize("carteira", ["104", "112", "115", "188"])
def test_o_dac_escritural_nao_depende_de_agencia_nem_de_conta(carteira) -> None:
    """É o que distingue as duas composições: mudar a conta não pode mexer no dígito."""
    a = boleto_exemplo(carteira=carteira, agencia="0057", conta="12345")
    b = boleto_exemplo(carteira=carteira, agencia="9999", conta="99999")
    assert a.dac_nosso_numero == b.dac_nosso_numero


def test_o_dac_direto_depende_de_agencia_e_conta() -> None:
    """O par é escolhido a dedo: o dígito tem só 10 valores, e ``9999/99999``
    colide com ``0057/12345`` na 109 — o que faria o teste passar por sorte."""
    a = boleto_exemplo(carteira="109", agencia="0057", conta="12345")
    b = boleto_exemplo(carteira="109", agencia="1234", conta="56789")
    assert a.dac_nosso_numero == 0
    assert b.dac_nosso_numero == 4


def test_codigo_barras_estrutura() -> None:
    b = boleto_exemplo()
    cb = b.codigo_barras
    assert len(cb) == 44 and cb.isdigit()
    assert cb.startswith("3419")  # banco + moeda
    assert 1 <= int(cb[4]) <= 9  # DV geral
    fator = 1000 + (date(2026, 8, 15) - date(2025, 2, 22)).days
    assert cb[5:9] == f"{fator:04d}"
    assert cb[9:19] == "0000012750"  # R$ 127,50
    assert cb[19:] == b.campo_livre()


def test_linha_digitavel_estrutura_e_roundtrip() -> None:
    b = boleto_exemplo()
    ld = b.linha_digitavel
    blocos = ld.split(" ")
    assert len(blocos) == 5
    # reconstrução: campos 1-3 carregam banco+moeda+campo livre; 4 = DV; 5 = fator+valor
    digitos = "".join(ch for ch in ld if ch.isdigit())
    cb = b.codigo_barras
    assert digitos[:4] == cb[:4]
    assert blocos[3] == cb[4]  # DV geral
    assert blocos[4] == cb[5:19]  # fator + valor


def test_formatadores() -> None:
    b = boleto_exemplo()
    assert b.nosso_numero_formatado() == "109/12345678-0"
    assert b.agencia_conta_formatado() == "0057 / 12345-7"
    assert b.valor_centavos == 12750
    assert isinstance(b.valor, Decimal)


# --- validação ---------------------------------------------------------------


def test_validacoes() -> None:
    with pytest.raises(BoletoInvalido):
        boleto_exemplo(valor="0").codigo_barras  # noqa: B018
    with pytest.raises(BoletoInvalido):
        boleto_exemplo(carteira="999").validar()
    with pytest.raises(BoletoInvalido):
        boleto_exemplo(sacado_documento="111.111.111-11").validar()
    boleto_exemplo().validar()  # dados válidos não levantam


# --- serialização e render ---------------------------------------------------


def test_to_dict_para_api_rest() -> None:
    d = boleto_exemplo().to_dict()
    assert d["banco"] == "341"
    assert d["conta_corrente"] == "12345"
    assert len(d["codigo_barras"]) == 44
    assert d["data_vencimento"] == "2026-08-15"


def test_boleto_para_pdf_reportlab() -> None:
    """Fatia vertical completa: domínio -> contexto -> PDF ReportLab."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    ctx = boleto_exemplo().contexto_render()
    assert ctx["codigo_barras"].isdigit() and len(ctx["codigo_barras"]) == 44
    pdf = render_boleto_pdf(ctx, modelo="moderno")
    assert pdf.startswith(b"%PDF")
    assert isinstance(boleto_exemplo(), BancoBase)


def test_logo_optin_flui_para_o_contexto() -> None:
    """O ``logo`` opt-in do banco é propagado para ``banco.logo`` no contexto;
    sem logo, a chave nem aparece."""
    assert "logo" not in boleto_exemplo().contexto_render()["banco"]
    ctx = boleto_exemplo(logo=b"\x89PNG-bytes").contexto_render()
    assert ctx["banco"]["logo"] == b"\x89PNG-bytes"
