"""Testes do backend de renderização (ReportLab + código de barras)."""

from __future__ import annotations

import base64

import pytest

from pycobranca.render import interleaved_2of5_svg
from pycobranca.render.barcode import InvalidBarcodeError


def contexto_exemplo() -> dict:
    codigo_barras = "99991923400000127509999123456789012345678901"
    return {
        "banco": {"codigo_dv": "999-8", "nome": "Banco Exemplo", "sigla": "BE", "cor": "#003a70"},
        "linha_digitavel": "99991.23456 78901.234567 89012.345678 9 91230000012750",
        "local_pagamento": "Pagável em qualquer banco ou pelo PIX até o vencimento",
        "vencimento": "15/08/2026",
        "valor_documento": "127,50",
        "beneficiario": {
            "nome": "Empresa Exemplo LTDA",
            "documento": "CNPJ 12.345.678/0001-90",
            "endereco": "Av. Central, 1000 · São Paulo/SP",
            "agencia_codigo": "1234 / 56789-0",
        },
        "documento": {
            "data": "23/07/2026",
            "numero": "DOC-2026-0001",
            "especie": "DM",
            "aceite": "N",
            "data_processamento": "23/07/2026",
        },
        "nosso_numero": "109/12345678-9",
        "carteira": "109",
        "especie_moeda": "R$",
        "quantidade": "",
        "instrucoes": ["Após o vencimento, multa de 2%.", "Não receber após 30 dias."],
        "pagador": {
            "nome": "Cliente Final da Silva",
            "documento": "CPF 123.456.789-09",
            "endereco": "Rua das Flores, 100 · Belo Horizonte/MG",
        },
        "sacador_avalista": "—",
        "demonstrativo": "Referente à nota fiscal 0001.",
        "codigo_barras_svg": interleaved_2of5_svg(codigo_barras),
        "pix": {
            "habilitado": True,
            "qrcode_svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>',
            "copia_cola": "00020126...br.gov.bcb.pix...6304ABCD",
        },
    }


# --- código de barras -------------------------------------------------------


def test_barcode_gera_svg_valido() -> None:
    svg = interleaved_2of5_svg("1234567890")
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert "viewBox" in svg
    assert svg.count("<rect") > 10


def test_barcode_par_e_impar_tem_mesmo_numero_de_barras() -> None:
    # odd length é preenchido com zero à esquerda -> mesma contagem que o par equivalente.
    assert interleaved_2of5_svg("123").count("<rect") == interleaved_2of5_svg("0123").count("<rect")


def test_barcode_rejeita_nao_digito() -> None:
    with pytest.raises(InvalidBarcodeError):
        interleaved_2of5_svg("12AB")


def test_reportlab_gera_pdf() -> None:
    """Backend ReportLab gera PDF válido a partir do mesmo contexto."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    # QR do PIX no ReportLab entra como matriz de módulos (0/1)
    ctx["pix"]["qrcode_matrix"] = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
    pdf = render_boleto_pdf(ctx)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2000


def test_reportlab_modelo_moderno() -> None:
    """Modelo moderno: recibo com linha digitável e colunas esquerda/direita."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    pdf = render_boleto_pdf(ctx, modelo="moderno")
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 2000


def test_reportlab_modelo_invalido_levanta() -> None:
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    with pytest.raises(ValueError):
        render_boleto_pdf(contexto_exemplo(), modelo="xyz")


def test_reportlab_modelo_moderno_com_tema() -> None:
    """Tema: faixa de marca, marca d'água, rodapé — PDF válido e maior."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    sem_tema = render_boleto_pdf(ctx, modelo="moderno")
    ctx["tema"] = {
        "habilitado": True,
        "cor": "#1B4F8A",
        "logo_texto": "GESTAO+",
        "empresa": "Empresa Exemplo LTDA",
        "parcela_texto": "PARCELA 5/12",
        "marca_dagua": "EMPRESA EXEMPLO LTDA",
        "rodape": "contato@empresaexemplo.com.br - (11) 3000-0000",
    }
    com_tema = render_boleto_pdf(ctx, modelo="moderno")
    assert com_tema.startswith(b"%PDF")
    assert len(com_tema) > len(sem_tema)  # tema adiciona conteúdo (faixa, marca d'água, rodapé)


def test_reportlab_carne_gera_pdf_e_pagina_por_3_parcelas() -> None:
    """Carnê: PDF válido; 4 parcelas quebram em 2 páginas A4."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_carne_pdf

    def parcela(i: int) -> dict:
        c = contexto_exemplo()
        c["codigo_barras"] = "99991923400000127509999123456789012345678901"
        c["pix"]["qrcode_matrix"] = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
        c["nosso_numero"] = f"0000017{i}"
        return c

    pdf3 = render_carne_pdf({"parcelas": [parcela(i) for i in range(1, 4)]})
    assert pdf3.startswith(b"%PDF")
    pdf4 = render_carne_pdf({"parcelas": [parcela(i) for i in range(1, 5)]})
    assert pdf4.startswith(b"%PDF")
    assert b"/Count 2" in pdf4  # 4 parcelas -> 2 páginas
    assert b"/Count 1" in pdf3  # 3 parcelas -> 1 página


def test_reportlab_sem_pix_e_sem_demonstrativo() -> None:
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    ctx["pix"] = {"habilitado": False}
    ctx["demonstrativo"] = ""
    pdf = render_boleto_pdf(ctx)
    assert pdf.startswith(b"%PDF")


def test_reportlab_pix_autodetectado_por_modelo() -> None:
    """O `modelo` (clássico/moderno) é escolha do chamador; o PIX/SemPix é
    auto-selecionado pelos dados: com ``pix.qrcode_matrix`` a célula/QR é
    desenhada, sem ele é omitida — de forma independente em cada modelo."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    def ctx(com_pix: bool) -> dict:
        c = contexto_exemplo()
        c["codigo_barras"] = "99991923400000127509999123456789012345678901"
        if com_pix:
            c["pix"]["qrcode_matrix"] = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]
        else:
            c["pix"] = {"habilitado": False}
        return c

    for modelo in ("classico", "moderno"):
        com = render_boleto_pdf(ctx(True), modelo=modelo)
        sem = render_boleto_pdf(ctx(False), modelo=modelo)
        assert com.startswith(b"%PDF") and sem.startswith(b"%PDF")
        # a célula/QR do PIX adiciona conteúdo → com PIX é maior que sem PIX
        assert len(com) > len(sem), f"modelo {modelo}: PIX não foi auto-detectado"


# PNG 8×4 azul, válido — logo de teste fornecido pelo chamador (opt-in)
_LOGO_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAECAIAAAA8r+mnAAAAEUlEQVR42mMQCViAFTFQTwIA"
    "SD4ggUH7Js0AAAAASUVORK5CYII="
)


def test_reportlab_logo_optin_por_modelo() -> None:
    """Logo é opt-in via ``banco.logo``: quando presente, o cabeçalho embute a
    imagem (PDF maior) em ambos os modelos; quando ausente, nada muda."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    for modelo in ("classico", "moderno"):
        ctx = contexto_exemplo()
        ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
        sem = render_boleto_pdf(ctx, modelo=modelo)
        ctx["banco"]["logo"] = _LOGO_PNG
        com = render_boleto_pdf(ctx, modelo=modelo)
        assert com.startswith(b"%PDF") and sem.startswith(b"%PDF")
        assert b"/Image" in com or b"/XObject" in com, f"modelo {modelo}: logo não embutido"
        assert len(com) > len(sem), f"modelo {modelo}: logo não aumentou o PDF"


def test_reportlab_logo_aceita_caminho(tmp_path) -> None:
    """A fonte do logo também pode ser um caminho de arquivo, não só bytes."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    p = tmp_path / "logo.png"
    p.write_bytes(_LOGO_PNG)
    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    ctx["banco"]["logo"] = str(p)
    pdf = render_boleto_pdf(ctx, modelo="moderno")
    assert pdf.startswith(b"%PDF")
    assert b"/XObject" in pdf


def test_logo_do_banco_empacotado() -> None:
    """Logos empacotados: código normalizado, bytes de PNG, ``None`` p/ desconhecido."""
    from pycobranca.render import bancos_com_logo, logo_do_banco

    codigos = bancos_com_logo()
    assert "237" in codigos and "001" in codigos and len(codigos) >= 12
    b = logo_do_banco("237")
    assert isinstance(b, bytes) and b.startswith(b"\x89PNG\r\n\x1a\n")
    assert logo_do_banco(33) == logo_do_banco("033")  # normaliza 2->3 dígitos
    assert logo_do_banco("999") is None


def test_logo_empacotado_renderiza_no_boleto() -> None:
    """O logo empacotado alimenta ``banco.logo`` e é embutido no PDF."""
    pytest.importorskip("reportlab")
    from pycobranca.render import logo_do_banco, render_boleto_pdf

    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    sem = render_boleto_pdf(ctx, modelo="moderno")
    ctx["banco"]["logo"] = logo_do_banco("237")
    com = render_boleto_pdf(ctx, modelo="moderno")
    assert b"/XObject" in com and len(com) > len(sem)


def test_reportlab_carne_com_logo() -> None:
    """O carnê também aceita o logo opt-in (canhoto + ficha de cada parcela)."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_carne_pdf

    def parcela(com_logo: bool) -> dict:
        c = contexto_exemplo()
        c["codigo_barras"] = "99991923400000127509999123456789012345678901"
        if com_logo:
            c["banco"]["logo"] = _LOGO_PNG
        return c

    sem = render_carne_pdf({"parcelas": [parcela(False) for _ in range(3)]})
    com = render_carne_pdf({"parcelas": [parcela(True) for _ in range(3)]})
    assert com.startswith(b"%PDF") and sem.startswith(b"%PDF")
    assert len(com) > len(sem)


def test_reportlab_saida_deterministica() -> None:
    """Mesma entrada deve gerar o mesmo PDF (byte a byte) sob ``rl_config.invariant``.

    Guarda a reprodutibilidade da renderização — importante para conciliação e
    para tornar refatorações do backend verificáveis por comparação direta.
    """
    pytest.importorskip("reportlab")
    import reportlab.rl_config as rc

    from pycobranca.render import render_boleto_pdf

    ctx = contexto_exemplo()
    ctx["codigo_barras"] = "99991923400000127509999123456789012345678901"
    ctx["pix"]["qrcode_matrix"] = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]

    anterior = rc.invariant
    rc.invariant = 1
    try:
        a = render_boleto_pdf(ctx, modelo="moderno")
        b = render_boleto_pdf(ctx, modelo="moderno")
    finally:
        rc.invariant = anterior
    assert a == b
