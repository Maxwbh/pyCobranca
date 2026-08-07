"""Fatura: demonstrativo de itens + boleto na mesma página."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pycobranca.bancos import Itau
from pycobranca.render.modelos.fatura import normaliza_itens

pytest.importorskip("reportlab")

from pycobranca.render import render_boleto_pdf, render_fatura_pdf  # noqa: E402

ITENS = [
    {"descricao": "Mensalidade — agosto/2026", "quantidade": 1, "valor": 99.90},
    {"descricao": "Serviço adicional de suporte", "quantidade": 2, "valor_unitario": 13.80},
]


def _contexto(**extra):
    boleto = Itau(
        valor="127.50",
        cedente="EMPRESA EXEMPLO LTDA",
        cedente_documento="11222333000181",
        cedente_endereco="Rua das Flores, 100 - Centro",
        agencia="1234",
        conta="56789",
        carteira="109",
        nosso_numero="12345678",
        sacado="Cliente Final",
        sacado_documento="12345678909",
        data_vencimento=date(2026, 8, 15),
        data_documento=date(2026, 7, 15),
    )
    ctx = boleto.contexto_render()
    ctx.update(extra)
    return ctx


# ---- normalização dos itens ----


def test_normaliza_valor_total_da_linha() -> None:
    itens, total = normaliza_itens([{"descricao": "X", "valor": 50.0}])
    assert itens[0]["total"] == Decimal("50.0")
    assert itens[0]["quantidade"] == Decimal("1")
    assert total == Decimal("50.0")


def test_normaliza_quantidade_vezes_unitario() -> None:
    itens, total = normaliza_itens([{"descricao": "X", "quantidade": 3, "valor_unitario": 10.0}])
    assert itens[0]["total"] == Decimal("30.0")
    assert total == Decimal("30.0")


def test_normaliza_soma_o_total() -> None:
    _itens, total = normaliza_itens(ITENS)
    assert total == Decimal("127.50")  # 99,90 + 2 x 13,80


def test_normaliza_aceita_valor_em_texto_brasileiro() -> None:
    itens, _total = normaliza_itens([{"descricao": "X", "valor": "1.234,56"}])
    assert itens[0]["total"] == Decimal("1234.56")


def test_normaliza_sem_itens() -> None:
    assert normaliza_itens(None) == ([], Decimal("0"))


# ---- PDF ----


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_fatura_gera_pdf(modelo: str) -> None:
    pdf = render_fatura_pdf(_contexto(itens=ITENS), modelo=modelo)
    assert pdf.startswith(b"%PDF-")
    # a fatura é maior que o boleto puro (tem a tabela de itens)
    assert len(pdf) > len(render_boleto_pdf(_contexto(), modelo=modelo))


def test_fatura_sem_itens_degrada_para_boleto() -> None:
    assert len(render_fatura_pdf(_contexto())) == len(render_boleto_pdf(_contexto()))


def test_fatura_modelo_invalido() -> None:
    with pytest.raises(ValueError, match="modelo inválido"):
        render_fatura_pdf(_contexto(itens=ITENS), modelo="xyz")


def test_fatura_contem_itens_e_total() -> None:
    fitz = pytest.importorskip("fitz")
    pdf = render_fatura_pdf(_contexto(itens=ITENS))
    texto = fitz.open(stream=pdf, filetype="pdf")[0].get_text()
    assert "FATURA" in texto
    assert "Mensalidade — agosto/2026" in texto
    assert "27,60" in texto  # 2 x 13,80
    assert "Total da fatura" in texto
    # o boleto continua presente abaixo da tabela
    assert "Recibo do Pagador" in texto


# ---- nível 2: blocos declarativos ----

BLOCOS_CONSUMO = {
    "titulo": "FATURA DE CONSUMO",
    "blocos": [
        {"tipo": "campos", "itens": [("Período", "01/08 a 31/08"), ("Contrato", "4471")]},
        {
            "tipo": "tabela",
            "colunas": ["Descrição", "Qtd.", "Unitário", "Total"],
            "larguras": [110, 18, 28, 34],
            "alinhamento": "lrrr",
            "linhas": [["Consumo de água (m³)", "18", "3,50", "63,00"]],
        },
        {"tipo": "texto", "conteudo": "Leitura em <b>18/08/2026</b>."},
        {"tipo": "separador"},
        {"tipo": "espaco", "altura": 3},
        {"tipo": "total", "rotulo": "Total da fatura", "valor": 127.50},
    ],
}


def test_fatura_blocos_gera_pdf() -> None:
    pdf = render_fatura_pdf(_contexto(fatura=BLOCOS_CONSUMO))
    assert pdf.startswith(b"%PDF-")


def test_fatura_blocos_conteudo() -> None:
    fitz = pytest.importorskip("fitz")
    pdf = render_fatura_pdf(_contexto(fatura=BLOCOS_CONSUMO))
    texto = fitz.open(stream=pdf, filetype="pdf")[0].get_text()
    assert "FATURA DE CONSUMO" in texto  # título customizado
    assert "Período" in texto and "01/08 a 31/08" in texto  # bloco campos
    assert "Consumo de água (m³)" in texto  # bloco tabela
    assert "Leitura em" in texto and "18/08/2026" in texto  # bloco texto (mini-HTML)
    assert "Total da fatura" in texto  # bloco total
    assert "Recibo do Pagador" in texto  # boleto abaixo


def test_fatura_blocos_tem_precedencia_sobre_itens() -> None:
    fitz = pytest.importorskip("fitz")
    pdf = render_fatura_pdf(_contexto(itens=ITENS, fatura=BLOCOS_CONSUMO))
    texto = fitz.open(stream=pdf, filetype="pdf")[0].get_text()
    assert "Consumo de água (m³)" in texto
    assert "Mensalidade — agosto/2026" not in texto


def test_fatura_bloco_invalido() -> None:
    with pytest.raises(ValueError, match="bloco de fatura inválido"):
        render_fatura_pdf(_contexto(fatura={"blocos": [{"tipo": "xyz"}]}))


# ---- nível 3: callable ----


def test_fatura_desenhar_callable() -> None:
    fitz = pytest.importorskip("fitz")
    chamadas = []

    def arte(tela, info):
        chamadas.append(info.beneficiario_nome)
        tela.texto(tela.x_(0), tela.y_() - 6 * tela.mm, "ARTE LIVRE", fonte="Helvetica-Bold")
        tela.avanca(12)

    pdf = render_fatura_pdf(_contexto(fatura={"desenhar": arte}))
    texto = fitz.open(stream=pdf, filetype="pdf")[0].get_text()
    assert chamadas == ["EMPRESA EXEMPLO LTDA"]  # recebeu os dados preenchidos
    assert "ARTE LIVRE" in texto
    assert "Recibo do Pagador" in texto  # boleto composto abaixo


def test_fatura_contrato_rest() -> None:
    """Os campos da fatura são serializáveis pelo contrato existente (`BoletoData`)."""
    from pycobranca.contracts import valida_contrato

    dados = {
        "banco": "341",
        "valor": 127.50,
        "cedente": "Empresa",
        "documento_cedente": "11222333000181",
        "agencia": "1234",
        "conta_corrente": "56789",
        "carteira": "109",
        "nosso_numero": "12345678",
        "data_vencimento": "2026-08-15",
        "sacado": "Cliente",
        "sacado_documento": "12345678909",
        "itens": [{"descricao": "Mensalidade", "quantidade": 1, "valor": 99.90}],
        "fatura": BLOCOS_CONSUMO,
    }
    valida_contrato(dados, "BoletoData")
    valida_contrato(dados["itens"][0], "ItemFatura")
    valida_contrato(dados["fatura"], "FaturaCorpo")
    for bloco in dados["fatura"]["blocos"]:
        valida_contrato(bloco, "BlocoFatura")


def test_fatura_contrato_barra_bloco_invalido() -> None:
    from pycobranca.contracts import ErroDeContrato, valida_contrato

    with pytest.raises(ErroDeContrato):
        valida_contrato({"tipo": "xyz"}, "BlocoFatura")


def test_fatura_desenhar_tem_precedencia_maxima() -> None:
    fitz = pytest.importorskip("fitz")
    ctx = _contexto(itens=ITENS, fatura=dict(BLOCOS_CONSUMO))
    ctx["fatura"]["desenhar"] = lambda tela, info: tela.avanca(2)
    texto = fitz.open(stream=render_fatura_pdf(ctx), filetype="pdf")[0].get_text()
    assert "FATURA DE CONSUMO" not in texto
    assert "Mensalidade — agosto/2026" not in texto
