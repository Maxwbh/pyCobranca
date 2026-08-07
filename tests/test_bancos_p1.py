"""Bancos P1 restantes: BB (001), Bradesco (237), Santander (033), Caixa (104)."""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.bancos import BancoDoBrasil, Bancos, Bradesco, Caixa, Santander
from pycobranca.exceptions import BoletoInvalido

BASE = dict(
    valor="1350.75",
    cedente="Empresa Exemplo LTDA",
    cedente_documento="11.222.333/0001-81",
    data_vencimento=date(2026, 9, 1),
    sacado="Cliente Teste da Silva",
    sacado_documento="529.982.247-25",
)


def test_registro_completo_p1() -> None:
    codigos = {b.codigo for b in Bancos.todos()}
    assert {"001", "033", "104", "237", "341"} <= codigos
    assert Bancos.find("001") is BancoDoBrasil
    assert Bancos.find("033") is Santander
    assert Bancos.find("104") is Caixa
    assert Bancos.find("237") is Bradesco
    assert len(Bancos.com_pix()) >= 5


# --- Banco do Brasil ---------------------------------------------------------


def test_bb_convenio7_campo_livre() -> None:
    b = BancoDoBrasil(**BASE, convenio="1234567", nosso_numero="123", carteira="18")
    cl = b.campo_livre()
    assert cl == "000000" + "1234567" + "0000000123" + "18"
    assert len(cl) == 25
    assert b.nosso_numero_formatado() == "12345670000000123"  # convênio + sequencial (17)
    assert len(b.codigo_barras) == 44 and b.codigo_barras.startswith("0019")


def test_bb_convenio4_e_6_usam_agencia_conta() -> None:
    b4 = BancoDoBrasil(
        **BASE,
        convenio="1234",
        nosso_numero="1234567",
        carteira="18",
        agencia="1234",
        conta="56789",
    )
    assert b4.campo_livre() == "1234" + "1234567" + "1234" + "00056789" + "18"
    b6 = BancoDoBrasil(
        **BASE,
        convenio="123456",
        nosso_numero="12345",
        carteira="18",
        agencia="1234",
        conta="56789",
    )
    assert b6.campo_livre() == "123456" + "12345" + "1234" + "00056789" + "18"


def test_bb_convenio_invalido() -> None:
    with pytest.raises(BoletoInvalido):
        BancoDoBrasil(**BASE, convenio="12345", nosso_numero="1", carteira="18").validar()


# --- Bradesco ----------------------------------------------------------------


def test_bradesco_campo_livre_e_dv() -> None:
    b = Bradesco(**BASE, agencia="1234", conta="56789", carteira="06", nosso_numero="2")
    cl = b.campo_livre()
    assert cl == "1234" + "06" + "00000000002" + "0056789" + "0"
    assert len(cl) == 25
    # DV módulo 11 base 7 de "0600000000002": soma = 2*2 + 6*7 + 0... = 4+42=46; 46%11=2; dv=9
    assert b.dv_nosso_numero == "9"
    assert b.nosso_numero_formatado() == "06/00000000002-9"


def test_bradesco_dv_restos_especiais() -> None:
    # resto 0 -> "0" e resto 1 -> "P" (procura exemplares por varredura)
    achou = {"0": False, "P": False}
    for nn in range(1, 200):
        b = Bradesco(**BASE, agencia="1", conta="2", carteira="06", nosso_numero=str(nn))
        dv = b.dv_nosso_numero
        if dv in achou:
            achou[dv] = True
    assert all(achou.values())


# --- Santander ---------------------------------------------------------------


def test_santander_campo_livre() -> None:
    b = Santander(**BASE, convenio="3300123", carteira="101", nosso_numero="566612457800")
    cl = b.campo_livre()
    assert len(cl) == 25
    assert cl[0] == "9"
    assert cl[1:8] == "3300123"
    assert cl[8:20] == "566612457800"
    assert cl[20] == b.dv_nosso_numero
    assert cl[21] == "0"  # IOS
    assert cl[22:] == "101"
    assert len(b.codigo_barras) == 44 and b.codigo_barras.startswith("0339")


def test_santander_dv_maior_que_9_vira_zero() -> None:
    # dv calculado sempre em "0".."9"
    for nn in ("1", "10", "999999999999"):
        b = Santander(**BASE, convenio="1", carteira="101", nosso_numero=nn)
        assert b.dv_nosso_numero in "0123456789"


# --- Caixa (SIGCB) -----------------------------------------------------------


def test_caixa_campo_livre_sigcb() -> None:
    b = Caixa(**BASE, convenio="123456", agencia="1234", carteira="14", nosso_numero="123")
    nn = b._nosso_numero17
    assert nn == "14" + "000000000000123"
    cl = b.campo_livre()
    assert len(cl) == 25
    assert cl[0:6] == "123456"  # beneficiário
    assert cl[6] == b.dv_beneficiario
    assert cl[7:10] == nn[2:5]
    assert cl[10] == nn[0]  # tipo de cobrança (1 = registrada)
    assert cl[11:14] == nn[5:8]
    assert cl[14] == nn[1]  # identificador de emissão (4 = beneficiário)
    assert cl[15:24] == nn[8:17]
    assert cl[24] in "0123456789"  # DV do campo livre
    assert b.nosso_numero_formatado() == "14000000000000123-1"  # 17 posições + DV (SIGCB)
    assert len(b.codigo_barras) == 44 and b.codigo_barras.startswith("1049")


def test_caixa_modalidade_carteira_invalida() -> None:
    with pytest.raises(BoletoInvalido):
        Caixa(**BASE, convenio="123456", carteira="99", nosso_numero="1").validar()


# --- todos geram PDF ---------------------------------------------------------


def test_todos_p1_geram_pdf_reportlab() -> None:
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    boletos = [
        BancoDoBrasil(**BASE, convenio="1234567", nosso_numero="123", carteira="18"),
        Bradesco(**BASE, agencia="1234", conta="56789", carteira="06", nosso_numero="2"),
        Santander(**BASE, convenio="3300123", carteira="101", nosso_numero="566612457800"),
        Caixa(**BASE, convenio="123456", agencia="1234", carteira="14", nosso_numero="123"),
    ]
    for boleto in boletos:
        pdf = render_boleto_pdf(boleto.contexto_render(), modelo="moderno")
        assert pdf.startswith(b"%PDF"), boleto.codigo
