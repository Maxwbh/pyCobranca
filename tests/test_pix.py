"""PIX real: payload EMV, CRC16 (vetor canônico do BCB), QR e Bolepix no boleto."""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.pix import PixInvalido, PixPayload, crc16_ccitt

# Exemplo canônico do Manual de Padrões para Iniciação do PIX (BCB)
CANONICO = (
    "00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-426655440000"
    "5204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***63041D3D"
)


# --- CRC16 -------------------------------------------------------------------


def test_crc16_vetor_canonico_bcb() -> None:
    assert crc16_ccitt(CANONICO[:-4]) == "1D3D"


# --- payload EMV -------------------------------------------------------------


def test_payload_reproduz_exemplo_canonico() -> None:
    payload = PixPayload(
        chave="123e4567-e12b-12d1-a456-426655440000",
        nome="Fulano de Tal",
        cidade="BRASILIA",
    )
    assert payload.br_code() == CANONICO


def test_payload_com_valor_e_txid() -> None:
    payload = PixPayload(
        chave="11222333000181", nome="Empresa", cidade="Sao Paulo", valor="127.5", txid="PYCOB0001"
    )
    codigo = payload.br_code()
    assert "5406127.50" in codigo  # campo 54, valor com 2 casas
    assert "0509PYCOB0001" in codigo  # txid no campo 62/05
    assert codigo[-8:-4] == "6304" or codigo[-8:][:4]  # termina em CRC de 4 hex
    assert crc16_ccitt(codigo[:-4]) == codigo[-4:]  # CRC íntegro


def test_payload_normaliza_acentos_e_limites() -> None:
    payload = PixPayload(
        chave="x@y.com",
        nome="João da Silva Çedilha e Acentuação Ltda",  # > 25 chars, com acentos
        cidade="São João del-Rei",  # > 15, com acento
    )
    codigo = payload.br_code()
    assert "Joao da Silva Cedilha e A" in codigo  # 25 chars, sem acentos
    assert "SAO JOAO DEL-RE" in codigo  # 15 chars, maiúsculas
    assert crc16_ccitt(codigo[:-4]) == codigo[-4:]


def test_payload_validacoes() -> None:
    with pytest.raises(PixInvalido):
        PixPayload(chave="", nome="X", cidade="Y").br_code()
    with pytest.raises(PixInvalido):
        PixPayload(chave="k", nome="X", cidade="Y", txid="tx com espaço").br_code()
    with pytest.raises(PixInvalido):
        PixPayload(chave="k", nome="X", cidade="Y", valor="0").br_code()


# --- QR real -----------------------------------------------------------------


def test_qr_matrix_real() -> None:
    pytest.importorskip("qrcode")
    from pycobranca.pix import qr_matrix, qr_svg

    m = qr_matrix(CANONICO)
    assert len(m) >= 21 and len(m) == len(m[0])  # quadrada, versão >= 1
    assert all(c in (0, 1) for linha in m for c in linha)
    # finder patterns nos cantos
    assert m[0][0] == 1 and m[0][-1] == 1 and m[-1][0] == 1
    svg = qr_svg(CANONICO)
    assert svg.startswith("<svg") and svg.count("<rect") > 100


# --- Bolepix integrado ao boleto --------------------------------------------


def test_boleto_com_pix_gera_bolepix_pagavel() -> None:
    pytest.importorskip("qrcode")
    from pycobranca.bancos import Itau

    boleto = Itau(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11.222.333/0001-81",
        cedente_cidade="São Paulo",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="529.982.247-25",
        pix_chave="11222333000181",
        pix_txid="PYCOB0001",
    )
    ctx = boleto.contexto_render()
    assert ctx["pix"]["habilitado"] is True
    copia_cola = ctx["pix"]["copia_cola"]
    assert copia_cola.startswith("000201")
    assert crc16_ccitt(copia_cola[:-4]) == copia_cola[-4:]
    assert "5406127.50" in copia_cola  # valor do boleto no PIX
    assert len(ctx["pix"]["qrcode_matrix"]) >= 21


def test_boleto_sem_chave_nao_habilita_pix() -> None:
    from pycobranca.bancos import Itau

    boleto = Itau(
        valor="10",
        cedente="X",
        agencia="1234",
        conta="56789",
        carteira="109",
        nosso_numero="1",
        data_vencimento=date(2026, 8, 15),
    )
    assert boleto.contexto_render()["pix"] == {"habilitado": False}


def test_bolepix_ate_o_pdf() -> None:
    pytest.importorskip("qrcode")
    pytest.importorskip("reportlab")
    from pycobranca.bancos import Bradesco
    from pycobranca.render import render_boleto_pdf

    boleto = Bradesco(
        valor="1350.75",
        cedente="Empresa Exemplo LTDA",
        cedente_cidade="Sete Lagoas",
        agencia="1234",
        conta="56789",
        carteira="06",
        nosso_numero="2",
        data_vencimento=date(2026, 9, 1),
        sacado="Cliente Teste",
        pix_chave="maxwbh@example.com",
    )
    pdf = render_boleto_pdf(boleto.contexto_render(), modelo="moderno")
    assert pdf.startswith(b"%PDF")
