"""Modelo **Carnê**: 3 parcelas por A4, canhoto aberto à esquerda e ficha compacta.

Cada parcela usa o mesmo contrato de contexto do boleto; os dados são extraídos
por :func:`pycobranca.render.dados.extrai_dados`. O carnê tem sistema de
coordenadas próprio (uma faixa por parcela, medida a partir do topo da faixa),
por isso desenha direto com as primitivas de :mod:`pycobranca.render.comum` em vez
de usar a :class:`~pycobranca.render.tela.Tela` do boleto.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from ..comum import (
    _CINZA_BORDA,
    _CINZA_ROTULO,
    _COR_PIX,
    _DESTAQUE_BG,
    _LARGURA,
    _MARGEM,
    _PT,
    _canvas_e_libs,
    _carrega_logo,
    _desenha_barcode,
    _desenha_logo,
    _desenha_qr,
    _faz_texto,
)
from ..dados import extrai_dados

__all__ = ["render_carne_pdf"]


def render_carne_pdf(contexto: dict[str, Any]) -> bytes:
    """Gera o PDF do carnê no modelo moderno (3 parcelas por A4).

    Layout: canhoto
    aberto à esquerda (Vencimento, Agência/Código, Nosso número, Valor,
    Nº documento, Sacado, "Recibo do Pagador"), ficha compacta com coluna
    direita fixa, célula PIX teal e código de barras de 32pt.

    Args:
        contexto: ``{"parcelas": [ctx, ...]}`` — cada parcela usa o mesmo
            contrato do boleto, com ``codigo_barras`` (44 dígitos) e
            ``pix.qrcode_matrix`` opcional.

    Returns:
        Bytes do PDF (uma página A4 a cada 3 parcelas).
    """
    parcelas = contexto["parcelas"]
    colors, A4, mm, Canvas = _canvas_e_libs()
    HexColor, black, white = colors.HexColor, colors.black, colors.white

    borda = HexColor(_CINZA_BORDA)
    rotulo = HexColor(_CINZA_ROTULO)
    destaque_bg = HexColor(_DESTAQUE_BG)
    pix_cor = HexColor(_COR_PIX)

    buf = BytesIO()
    canvas = Canvas(buf, pagesize=A4)
    _, altura_pagina = A4

    faixa_h = 90.0
    canhoto_w = 42.0
    gap = 3.5

    def texto(x, y_abs, s, *, fonte="Helvetica", tam=8, cor=black, dir_x=None, centro_x=None):
        _faz_texto(
            canvas, x, y_abs, s, fonte=fonte, tam=tam, cor=cor, dir_x=dir_x, centro_x=centro_x
        )

    def desenha_parcela(idx, d):
        pos = idx % 3
        if idx > 0 and pos == 0:
            canvas.showPage()
        info = extrai_dados(d)
        tem_pix = info.tem_pix
        qrcode_matrix = info.qrcode_matrix
        logo_reader = _carrega_logo(info.banco_logo)
        y0 = altura_pagina - (_MARGEM + pos * (faixa_h + gap)) * mm

        def x_(v):
            return (_MARGEM + v) * mm

        def yl(dy, *, _y0=y0):
            return _y0 - dy * mm

        # separador horizontal tracejado entre faixas
        if pos > 0:
            canvas.setStrokeColor(rotulo)
            canvas.setLineWidth(0.4)
            canvas.setDash(2, 2)
            canvas.line(x_(0), y0 + (gap / 2) * mm, x_(_LARGURA), y0 + (gap / 2) * mm)
            canvas.setDash()

        # ---------------- canhoto aberto (sem moldura) ----------------
        if logo_reader is not None:
            _desenha_logo(canvas, mm, logo_reader, x_(0), y0, canhoto_w - 12.0, 5.0)
        else:
            texto(x_(0), yl(4.6), info.banco_nome, fonte="Helvetica-Bold", tam=9)
        texto(
            0,
            yl(4.6),
            info.banco_dv,
            fonte="Helvetica-Bold",
            tam=10,
            dir_x=x_(canhoto_w - 1),
        )
        canvas.setStrokeColor(black)
        canvas.setLineWidth(0.8)
        canvas.line(x_(0), yl(6.2), x_(canhoto_w - 1), yl(6.2))

        campos = [
            ("Vencimento", info.vencimento, True),
            ("Agência/Código do Beneficiário", info.agencia_codigo, False),
            ("Nosso número", info.nosso_numero, False),
            ("(=) Valor do documento", info.valor_documento, True),
            ("Nº documento", info.doc_numero, False),
            ("Sacado", info.sacado_nome, False),
        ]
        cy = 8.0
        for rot_c, val_c, negrito_c in campos:
            texto(x_(0), yl(cy + 2.2), rot_c, tam=5, cor=rotulo)
            texto(
                x_(0),
                yl(cy + 6.0),
                val_c,
                fonte="Helvetica-Bold" if negrito_c else "Helvetica",
                tam=7.5,
            )
            canvas.setStrokeColor(borda)
            canvas.setLineWidth(0.4)
            canvas.line(x_(0), yl(cy + 7.4), x_(canhoto_w - 1), yl(cy + 7.4))
            cy += 8.6
        texto(
            0,
            yl(cy + 4.0),
            "Recibo do Pagador",
            fonte="Helvetica-Oblique",
            tam=6.5,
            cor=rotulo,
            centro_x=x_(canhoto_w / 2),
        )

        # separador vertical tracejado
        canvas.setStrokeColor(rotulo)
        canvas.setLineWidth(0.4)
        canvas.setDash(2, 2)
        canvas.line(x_(canhoto_w + 1.5), y0, x_(canhoto_w + 1.5), yl(faixa_h))
        canvas.setDash()

        # ---------------- ficha compacta ----------------
        fx = canhoto_w + 4.0
        fw = _LARGURA - fx
        if logo_reader is not None:
            _desenha_logo(canvas, mm, logo_reader, x_(fx), y0, 28.0, 5.0)
        else:
            texto(x_(fx), yl(4.6), info.banco_nome, fonte="Helvetica-Bold", tam=9)
        canvas.setStrokeColor(black)
        canvas.setLineWidth(0.8)
        canvas.line(x_(fx + 30), yl(0.8), x_(fx + 30), yl(6.2))
        canvas.line(x_(fx + 46), yl(0.8), x_(fx + 46), yl(6.2))
        texto(
            0,
            yl(4.8),
            info.banco_dv,
            fonte="Helvetica-Bold",
            tam=11,
            centro_x=x_(fx + 38),
        )
        texto(0, yl(4.6), info.linha_digitavel, fonte="Helvetica-Bold", tam=8.2, dir_x=x_(_LARGURA))
        canvas.line(x_(fx), yl(6.2), x_(_LARGURA), yl(6.2))

        def fcel(cx, cw, cy, ch, rot_c, val_c, *, negrito=False, destaque=False, tam=7.5, _fx=fx):
            if destaque:
                canvas.setFillColor(destaque_bg)
                canvas.rect(x_(_fx + cx), yl(cy + ch), cw * mm, ch * mm, stroke=0, fill=1)
            canvas.setLineWidth(0.4)
            canvas.setStrokeColor(borda)
            canvas.rect(x_(_fx + cx), yl(cy + ch), cw * mm, ch * mm, stroke=1, fill=0)
            texto(x_(_fx + cx) + 1 * mm, yl(cy + 2.3), rot_c, tam=5, cor=rotulo)
            texto(
                x_(_fx + cx) + 1 * mm,
                yl(cy + ch - 1.5),
                val_c,
                fonte="Helvetica-Bold" if negrito else "Helvetica",
                tam=tam,
            )

        row_f = 6.4
        w_dir = fw * 0.28
        w_esq = fw - w_dir
        cy = 6.2
        fcel(0, w_esq, cy, row_f, "Local de pagamento", info.local_pagamento, negrito=True)
        fcel(w_esq, w_dir, cy, row_f, "Vencimento", info.vencimento, negrito=True, destaque=True)
        cy += row_f
        fcel(
            0,
            w_esq,
            cy,
            row_f,
            "Beneficiário",
            info.beneficiario,
            negrito=True,
        )
        fcel(
            w_esq,
            w_dir,
            cy,
            row_f,
            "Agência/Código do Beneficiário",
            info.agencia_codigo,
        )
        cy += row_f
        w5 = w_esq / 5
        r_doc = [
            ("Data documento", info.doc_data),
            ("Nº documento", info.doc_numero),
            ("Espécie doc.", info.doc_especie),
            ("Aceite", info.doc_aceite),
            ("Data process.", info.doc_processamento),
        ]
        for i, (rot_c, val_c) in enumerate(r_doc):
            fcel(i * w5, w5, cy, row_f, rot_c, val_c, tam=6.8)
        fcel(w_esq, w_dir, cy, row_f, "Nosso número", info.nosso_numero)
        cy += row_f
        r_uso = [
            ("Uso do banco", ""),
            ("Carteira", info.carteira),
            ("Espécie", info.especie_moeda),
            ("Quantidade", info.quantidade),
            ("Valor", ""),
        ]
        for i, (rot_c, val_c) in enumerate(r_uso):
            fcel(i * w5, w5, cy, row_f, rot_c, val_c, tam=6.8)
        fcel(
            w_esq,
            w_dir,
            cy,
            row_f,
            "(=) Valor documento",
            info.valor_documento,
            negrito=True,
            destaque=True,
        )
        cy += row_f

        # bloco instruções + sacado, com célula PIX à direita
        bloco_h = 31.0
        pix_w = 24.0 if tem_pix else 0.0
        canvas.setStrokeColor(borda)
        canvas.setLineWidth(0.4)
        canvas.rect(x_(fx), yl(cy + bloco_h), (fw - pix_w) * mm, bloco_h * mm, stroke=1, fill=0)
        texto(
            x_(fx) + 1 * mm,
            yl(cy + 2.3),
            "Instruções (texto de responsabilidade do beneficiário)",
            tam=5,
            cor=rotulo,
        )
        for i, ln in enumerate(info.instrucoes[:6]):
            texto(x_(fx) + 1 * mm, yl(cy + 5.6 + 3.2 * i), ln, tam=6.8)
        div_y = cy + bloco_h - 7.5
        canvas.setStrokeColor(borda)
        canvas.line(x_(fx), yl(div_y), x_(fx) + (fw - pix_w) * mm, yl(div_y))
        texto(x_(fx) + 1 * mm, yl(div_y + 2.3), "Sacado", tam=5, cor=rotulo)
        texto(
            x_(fx) + 1 * mm,
            yl(div_y + 5.8),
            info.sacado_completo,
            tam=6.8,
        )
        if tem_pix:
            px = fx + fw - pix_w
            canvas.setStrokeColor(borda)
            canvas.rect(x_(px), yl(cy + bloco_h), pix_w * mm, bloco_h * mm, stroke=1, fill=0)
            cab_h = 3.2
            canvas.setFillColor(pix_cor)
            canvas.rect(x_(px), yl(cy + cab_h), pix_w * mm, cab_h * mm, stroke=0, fill=1)
            texto(
                0,
                yl(cy + 2.3),
                "PAGUE COM PIX",
                fonte="Helvetica-Bold",
                tam=4.6,
                cor=white,
                centro_x=x_(px) + pix_w / 2 * mm,
            )
            lado_qr = min(bloco_h - cab_h - 3.0, pix_w - 3.0)
            _desenha_qr(
                canvas,
                mm,
                qrcode_matrix,
                x_(px) + (pix_w - lado_qr) / 2 * mm,
                yl(cy + cab_h + 1.5 + lado_qr),
                lado_qr,
                black,
            )
        cy += bloco_h

        # código de barras (32pt) + autenticação à direita
        bar_h = 32 * _PT
        bar_w = fw * 0.72
        cy += 1.2
        texto(
            0,
            yl(cy + 2.0),
            "Autenticação mecânica - Ficha de Compensação",
            tam=5,
            cor=rotulo,
            dir_x=x_(_LARGURA),
        )
        _desenha_barcode(
            canvas, mm, info.codigo_barras, x_(fx), yl(cy + bar_h), bar_w, bar_h, black
        )

    for idx, d in enumerate(parcelas):
        desenha_parcela(idx, d)

    canvas.showPage()
    canvas.save()
    return buf.getvalue()
