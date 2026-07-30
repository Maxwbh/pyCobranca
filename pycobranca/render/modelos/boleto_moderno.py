"""Modelo **Boleto Moderno**: Recibo do Pagador com chips, célula PIX e paleta cinza/teal.

Blocos: :func:`cabecalho_moderno`, :func:`desenha_tema`, :func:`recibo_moderno` e
:func:`ficha_moderna`. Cada um recebe a :class:`~pycobranca.render.tela.Tela` e os
dados (:class:`~pycobranca.render.dados.DadosBoleto`) e desenha avançando o cursor.

:func:`desenha` é o ponto de entrada do modelo (contrato do catálogo em
:mod:`pycobranca.render.modelos`): monta a página inteira na ordem correta.
"""

from __future__ import annotations

from ..blocos import bloco_demonstrativo, corte, rotulo_dir
from ..comum import (
    _BARCODE_FRAC,
    _BARCODE_H,
    _LARGURA,
    _PT,
    _TOT_H,
    _desenha_barcode,
    _desenha_logo,
    _desenha_qr,
)

__all__ = ["desenha", "cabecalho_moderno", "desenha_tema", "recibo_moderno", "ficha_moderna"]

#: paleta do modelo (cinza/teal); ver :class:`pycobranca.render.tela.Tela`
MODERNO = True

# larguras/posições das linhas de 6 colunas (reutilizadas no recibo e na ficha)
_C6 = [30.0, 40.0, 20.0, 16.0, 34.0, 50.0]
_X6 = [0.0, 30.0, 70.0, 90.0, 106.0, 140.0]

_TOTALIZADORES = [
    "(-) Desconto / Abatimento",
    "(-) Outras deduções",
    "(+) Mora / Multa",
    "(+) Outros Acréscimos",
    "(=) Valor cobrado",
]


def desenha(tela, info, contexto) -> None:
    """Página inteira do boleto moderno, na ordem: tema, recibo, demonstrativo, corte, ficha."""
    tema = contexto.get("tema") or {}
    if tema.get("habilitado"):
        desenha_tema(tela, tema)
    recibo_moderno(tela, info)
    if info.demonstrativo:
        bloco_demonstrativo(tela, info)
    corte(tela)
    ficha_moderna(tela, info)


def _linhas6(info):
    """As duas linhas de 6 colunas: dados do documento e uso do banco."""
    r2 = [
        ("Data do documento", info.doc_data),
        ("N. do Documento", info.doc_numero),
        ("Espécie", info.doc_especie),
        ("Aceite", info.doc_aceite),
        ("Data Processamento", info.doc_processamento),
        ("Agência/Código Beneficiário", info.agencia_codigo),
    ]
    r3 = [
        ("Uso do banco", ""),
        ("Carteira", info.carteira),
        ("Espécie", info.especie_moeda),
        ("Quantidade", info.quantidade),
        ("Valor", info.valor_documento),
        ("Nosso número", info.nosso_numero),
    ]
    return r2, r3


def cabecalho_moderno(tela, info, texto_dir) -> None:
    """Cabeçalho do modelo moderno: nome do banco em texto, barras pretas, régua fina."""
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    h = 9.0
    y_topo = tela.y_()
    if tela.logo_reader is not None:
        _desenha_logo(canvas, mm, tela.logo_reader, x_(0), y_topo, 40.0, h - 1.0)
    else:
        texto(x_(0), y_topo - 6.2 * mm, info.banco_nome, fonte="Helvetica-Bold", tam=12)
    canvas.setStrokeColor(tela.black)
    canvas.setLineWidth(1.0)
    canvas.line(x_(42), y_topo - 1 * mm, x_(42), y_topo - h * mm)
    canvas.line(x_(64), y_topo - 1 * mm, x_(64), y_topo - h * mm)
    texto(
        0,
        y_topo - 6.6 * mm,
        info.banco_dv,
        fonte="Helvetica-Bold",
        tam=14,
        centro_x=x_(53),
    )
    texto(0, y_topo - 6.4 * mm, texto_dir, fonte="Helvetica-Bold", tam=11.5, dir_x=x_(_LARGURA))
    canvas.setLineWidth(0.8)
    canvas.line(x_(0), y_topo - h * mm, x_(_LARGURA), y_topo - h * mm)
    tela.avanca(h)


def desenha_tema(tela, tema) -> None:
    """TEMA (referência ``boleto_tema.png``): faixa de marca, marca d'água e rodapé."""
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    cor_tema = tela.HexColor(tema.get("cor", "#1B4F8A"))

    # marca d'água diagonal (tinta clara da cor do tema), atrás de todo o conteúdo
    marca_dagua = tema.get("marca_dagua")
    if marca_dagua:
        r, g, b = cor_tema.red, cor_tema.green, cor_tema.blue
        tinta = tela.colors.Color(1 - (1 - r) * 0.12, 1 - (1 - g) * 0.12, 1 - (1 - b) * 0.12)
        canvas.saveState()
        canvas.setFillColor(tinta)
        canvas.setFont("Helvetica-Bold", 40)
        for wx, wy in ((25, 120), (35, 215)):
            canvas.saveState()
            canvas.translate(wx * mm, tela.altura_pagina - wy * mm)
            canvas.rotate(35)
            canvas.drawString(0, 0, marca_dagua)
            canvas.restoreState()
        canvas.restoreState()

    # faixa de marca no topo: logo em caixa branca + empresa + badge de parcela
    faixa_h = 10.0
    y_topo = tela.y_()
    canvas.setFillColor(cor_tema)
    canvas.rect(x_(0), y_topo - faixa_h * mm, _LARGURA * mm, faixa_h * mm, stroke=0, fill=1)
    logo_texto = tema.get("logo_texto")
    empresa_x = 3.0
    if logo_texto:
        canvas.setFillColor(tela.white)
        canvas.roundRect(x_(2), y_topo - 8.2 * mm, 24 * mm, 6.4 * mm, 1.0 * mm, stroke=0, fill=1)
        texto(
            0,
            y_topo - 6.2 * mm,
            logo_texto,
            fonte="Helvetica-Bold",
            tam=8,
            cor=cor_tema,
            centro_x=x_(14),
        )
        empresa_x = 30.0
    if tema.get("empresa"):
        texto(
            x_(empresa_x),
            y_topo - 6.4 * mm,
            tema["empresa"],
            fonte="Helvetica-Bold",
            tam=10,
            cor=tela.white,
        )
    if tema.get("parcela_texto"):
        texto(
            0,
            y_topo - 6.6 * mm,
            tema["parcela_texto"],
            fonte="Helvetica-Bold",
            tam=11,
            cor=tela.white,
            dir_x=x_(_LARGURA - 2),
        )
    tela.avanca(faixa_h + 2.0)

    # rodapé: contatos centralizados na cor do tema + barra full-bleed na base
    if tema.get("rodape"):
        texto(0, 7.5 * mm, tema["rodape"], tam=7, cor=cor_tema, centro_x=x_(_LARGURA / 2))
    canvas.setFillColor(cor_tema)
    canvas.rect(0, 0, 210 * mm, 3.0 * mm, stroke=0, fill=1)


def recibo_moderno(tela, info) -> None:
    """Recibo do Pagador: chips (vencimento/valor/nosso número), dados e totalizadores."""
    canvas, mm, x_, texto, celula = tela.canvas, tela.mm, tela.x_, tela.texto, tela.celula
    r2, r3 = _linhas6(info)

    rotulo_dir(tela, "Recibo do Pagador", italico=True)
    cabecalho_moderno(tela, info, info.linha_digitavel)
    tela.avanca(1.5)

    chip_h = 32 * _PT
    chip_w = (_LARGURA - 2 * 3.0) / 3
    chips = [
        ("Vencimento", info.vencimento),
        ("Valor do Documento", info.valor_documento),
        ("Nosso Número", info.nosso_numero),
    ]
    y_topo = tela.y_()
    for i, (rot_c, val_c) in enumerate(chips):
        cx = i * (chip_w + 3.0)
        canvas.setFillColor(tela.destaque_bg)
        canvas.roundRect(
            x_(cx), y_topo - chip_h * mm, chip_w * mm, chip_h * mm, 1.0 * mm, stroke=0, fill=1
        )
        canvas.setStrokeColor(tela.borda)
        canvas.setLineWidth(0.5)
        canvas.roundRect(
            x_(cx), y_topo - chip_h * mm, chip_w * mm, chip_h * mm, 1.0 * mm, stroke=1, fill=0
        )
        texto(x_(cx) + 2.2 * mm, y_topo - 3.6 * mm, rot_c.upper(), tam=6, cor=tela.rotulo)
        texto(
            x_(cx) + 2.2 * mm,
            y_topo - (chip_h - 3.2) * mm,
            val_c,
            fonte="Helvetica-Bold",
            tam=12,
        )
    tela.avanca(chip_h + 2.0)

    celula(
        0,
        142,
        12.0,
        "Beneficiário",
        info.beneficiario,
        negrito=True,
        linha2=info.beneficiario_endereco,
    )
    celula(142, 48, 12.0, "Valor do Documento", info.valor_documento, negrito=True, destaque=True)
    tela.avanca(12.0)

    for (rot_c, val_c), cx, cw in zip(r2, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot_c, val_c)
    tela.avanca(7.0)

    for (rot_c, val_c), cx, cw in zip(r3, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot_c, val_c)
    tela.avanca(7.0)

    # totalizadores horizontais (5 colunas)
    w5 = _LARGURA / 5
    for i, rot_c in enumerate(_TOTALIZADORES):
        celula(i * w5, w5, 6.5, rot_c, "")
    tela.avanca(6.5)

    celula(0, 190, 12.0, "Sacado", info.sacado_curto, negrito=True, linha2=info.sacado_endereco)
    tela.avanca(12.0)
    rotulo_dir(tela, "Autenticação mecânica - Recibo do Pagador")


def ficha_moderna(tela, info) -> None:
    """Ficha de Compensação: instruções (57%) | PIX (18%) | totalizadores (25%)."""
    canvas, mm, x_, texto, celula = tela.canvas, tela.mm, tela.x_, tela.texto, tela.celula
    r2, r3 = _linhas6(info)
    tem_pix = info.tem_pix

    cabecalho_moderno(tela, info, info.linha_digitavel)

    celula(0, 142, 7.5, "Local de pagamento", info.local_pagamento, negrito=True)
    celula(142, 48, 7.5, "Vencimento", info.vencimento, negrito=True, destaque=True)
    tela.avanca(7.5)

    celula(
        0,
        142,
        12.0,
        "Beneficiário",
        info.beneficiario,
        negrito=True,
        linha2=info.beneficiario_endereco,
    )
    celula(142, 48, 12.0, "Valor do Documento", info.valor_documento, negrito=True, destaque=True)
    tela.avanca(12.0)

    for (rot_c, val_c), cx, cw in zip(r2, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot_c, val_c)
    tela.avanca(7.0)
    for (rot_c, val_c), cx, cw in zip(r3, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot_c, val_c)
    tela.avanca(7.0)

    # bloco instruções [57% | 18% PIX | 25% totalizadores empilhados]
    n_tot = 6 if tem_pix else 5
    h_instr = _TOT_H * n_tot
    w_instr = _LARGURA * (0.57 if tem_pix else 0.75)
    w_pix = _LARGURA * 0.18 if tem_pix else 0.0
    w_tot = _LARGURA - w_instr - w_pix
    y_topo = tela.y_()
    canvas.setLineWidth(0.5)
    canvas.setStrokeColor(tela.borda)
    canvas.rect(x_(0), y_topo - h_instr * mm, w_instr * mm, h_instr * mm, stroke=1, fill=0)
    texto(
        x_(1.2),
        y_topo - 2.8 * mm,
        "Instruções (Texto de responsabilidade do beneficiário)",
        tam=5.8,
        cor=tela.rotulo,
    )
    for i, ln in enumerate(info.instrucoes[:7]):
        texto(x_(1.2), y_topo - (7.0 + (10 * _PT) * i) * mm, ln, tam=8.5)
    if tem_pix:
        px = w_instr
        canvas.setStrokeColor(tela.borda)
        canvas.rect(x_(px), y_topo - h_instr * mm, w_pix * mm, h_instr * mm, stroke=1, fill=0)
        cab_h = 10 * _PT
        canvas.setFillColor(tela.pix_cor)
        canvas.rect(x_(px), y_topo - cab_h * mm, w_pix * mm, cab_h * mm, stroke=0, fill=1)
        texto(
            0,
            y_topo - 2.6 * mm,
            "PAGUE COM PIX",
            fonte="Helvetica-Bold",
            tam=5.5,
            cor=tela.white,
            centro_x=x_(px) + w_pix / 2 * mm,
        )
        lado_qr = min(h_instr - cab_h - 3.0, w_pix - 4.0)
        _desenha_qr(
            canvas,
            mm,
            info.qrcode_matrix,
            x_(px) + (w_pix - lado_qr) / 2 * mm,
            y_topo - (cab_h + 1.5 + lado_qr) * mm,
            lado_qr,
            tela.black,
        )
    h_lado = h_instr / len(_TOTALIZADORES)
    x_tot = w_instr + w_pix
    for i, rot_c in enumerate(_TOTALIZADORES):
        canvas.setStrokeColor(tela.borda)
        canvas.rect(
            x_(x_tot), y_topo - (i + 1) * h_lado * mm, w_tot * mm, h_lado * mm, stroke=1, fill=0
        )
        texto(
            x_(x_tot) + 1.2 * mm, y_topo - (i * h_lado + 2.8) * mm, rot_c, tam=5.8, cor=tela.rotulo
        )
    tela.avanca(h_instr)

    celula(0, 190, 12.0, "Sacado", info.sacado_curto, negrito=True, linha2=info.sacado_endereco)
    tela.avanca(12.0)
    celula(0, 142, 6.5, "Sacador/Avalista", info.sacador_avalista or "")
    celula(142, 48, 6.5, "Cód. baixa", info.codigo_baixa)
    tela.avanca(6.5)

    rotulo_dir(tela, "Autenticação mecânica - Ficha de Compensação")
    bar_w, bar_h = _LARGURA * _BARCODE_FRAC, _BARCODE_H
    _desenha_barcode(
        canvas, mm, info.codigo_barras, x_(0), tela.y_(bar_h), bar_w, bar_h, tela.black
    )
