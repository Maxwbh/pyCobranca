"""Modelo **Boleto Moderno**: chips de destaque, faixa de marca, PIX e grade alinhada.

Blocos: :func:`cabecalho_moderno`, :func:`desenha_tema`, :func:`recibo_moderno` e
:func:`ficha_moderna`. Cada um recebe a :class:`~pycobranca.render.tela.Tela` e os dados
(:class:`~pycobranca.render.dados.DadosBoleto`) e desenha avançando o cursor.

:func:`desenha` é o ponto de entrada do modelo (contrato do catálogo em
:mod:`pycobranca.render.modelos`): monta a página inteira na ordem correta.

Características do layout:

* chips de Vencimento / Valor / Nosso Número com fundo ``#F0F3F7`` e borda na cor do tema;
* faixa de marca de 12 mm com logo-texto, parcela e rodapé, quando há tema;
* grade de 6 colunas alinhada ao eixo de Vencimento/Valor (última coluna em 142 mm);
* valores monetários alinhados à direita — numa coluna de totais é a vírgula alinhada
  que deixa a soma legível de relance;
* destaque leve em ``(=) Valor cobrado``.
"""

from __future__ import annotations

from ..blocos import bloco_demonstrativo, rotulo_dir
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

# Grade de 6 colunas alinhada à coluna direita de Vencimento/Valor (142–190 = 48 mm)
_C6 = [30.0, 40.0, 20.0, 16.0, 36.0, 48.0]
_X6 = [0.0, 30.0, 70.0, 90.0, 106.0, 142.0]

_CHIP_H = 38 * _PT
#: Corpo do valor nos chips — é o que distingue o chip de uma célula comum.
_CHIP_TAM = 13.5
_CHIP_GAP = 3.5
_RADIUS = 1.5
_CORTE_H = 8.0
_RESPIRO = 1.4

#: Altura da faixa horizontal de totalizadores no recibo. A 6,5 mm o rótulo e o
#: valor caíam praticamente na mesma linha de base, e como o valor é alinhado à
#: direita ele cresce em direção ao rótulo: "(-) Desconto / Abatimento" não
#: deixava espaço para um valor na casa dos milhões. A 9,0 mm o número tem linha
#: própria — e número de dinheiro não pode ser abreviado.
_FAIXA_TOTAIS_H = 9.0

#: Entressilha das linhas de instrução, e o recuo do topo da moldura.
_LINHA_INSTR = 10 * _PT
_TOPO_INSTR = 7.0

#: ``(rótulo, chave em DadosBoleto.totalizadores)`` na ordem da faixa FEBRABAN.
_TOTALIZADORES = [
    ("(-) Desconto / Abatimento", "desconto_abatimento"),
    ("(-) Outras deduções", "outras_deducoes"),
    ("(+) Mora / Multa", "mora_multa"),
    ("(+) Outros Acréscimos", "outros_acrescimos"),
    ("(=) Valor cobrado", "valor_cobrado"),
]


def desenha(tela, info, contexto) -> None:
    """Página inteira do boleto moderno: tema, recibo, demonstrativo, corte, ficha."""
    tema = contexto.get("tema") or {}
    if tema.get("habilitado"):
        desenha_tema(tela, tema)
    recibo_moderno(tela, info, tema=tema if tema.get("habilitado") else None)
    if info.demonstrativo:
        bloco_demonstrativo(tela, info)
    _linha_corte(tela)
    ficha_moderna(tela, info, tema=tema if tema.get("habilitado") else None)


def _linhas6(info):
    """As duas linhas de 6 colunas: ``(rótulo, valor, alinhar_dir)`` por coluna.

    Campo numérico vai à direita; texto, à esquerda. É o que permite comparar
    duas vias lado a lado sem reler dígito por dígito.
    """
    r2 = [
        ("Data do documento", info.doc_data, False),
        ("N. do Documento", info.doc_numero, False),
        ("Espécie", info.doc_especie, False),
        ("Aceite", info.doc_aceite, False),
        ("Data Processamento", info.doc_processamento, False),
        ("Agência/Código Beneficiário", info.agencia_codigo, True),
    ]
    r3 = [
        ("Uso do banco", "", False),
        ("Carteira", info.carteira, False),
        ("Espécie", info.especie_moeda, False),
        ("Quantidade", info.quantidade, True),
        ("Valor", info.valor_documento, True),
        ("Nosso número", info.nosso_numero, True),
    ]
    return r2, r3


def _cor_tema(tela, tema: dict | None):
    hex_cor = (tema or {}).get("cor") or "#1B4F8A"
    return tela.HexColor(hex_cor)


def cabecalho_moderno(tela, info, texto_dir: str) -> None:
    """Cabeçalho: logo/nome do banco, código/DV e linha digitável."""
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    h = 9.5
    y_topo = tela.y_()

    if tela.logo_reader is not None:
        _desenha_logo(canvas, mm, tela.logo_reader, x_(0), y_topo, 40.0, h - 1.2)
    else:
        # O nome vai da margem até a régua de x_(42); "Caixa Econômica Federal"
        # a 12 pt media 145 pt para um vão de 115 e escrevia por cima do
        # código-DV, deixando os dois ilegíveis.
        nome, corpo = tela.cabe_corpo(info.banco_nome, (42 - 1.5) * mm, tam=12)
        texto(x_(0), y_topo - 6.4 * mm, nome, fonte="Helvetica-Bold", tam=corpo)

    canvas.setStrokeColor(tela.black)
    canvas.setLineWidth(1.0)
    canvas.line(x_(42), y_topo - 1 * mm, x_(42), y_topo - h * mm)
    canvas.line(x_(64), y_topo - 1 * mm, x_(64), y_topo - h * mm)

    texto(0, y_topo - 6.8 * mm, info.banco_dv, fonte="Helvetica-Bold", tam=14, centro_x=x_(53))
    texto(0, y_topo - 6.6 * mm, texto_dir, fonte="Helvetica-Bold", tam=11.5, dir_x=x_(_LARGURA))

    canvas.setLineWidth(0.7)
    canvas.line(x_(0), y_topo - h * mm, x_(_LARGURA), y_topo - h * mm)
    tela.avanca(h)


def desenha_tema(tela, tema: dict) -> None:
    """Faixa de marca + marca d'água + rodapé."""
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    cor_tema = _cor_tema(tela, tema)

    marca_dagua = tema.get("marca_dagua")
    if marca_dagua:
        r, g, b = cor_tema.red, cor_tema.green, cor_tema.blue
        tinta = tela.colors.Color(1 - (1 - r) * 0.10, 1 - (1 - g) * 0.10, 1 - (1 - b) * 0.10)
        canvas.saveState()
        canvas.setFillColor(tinta)
        canvas.setFont("Helvetica-Bold", 42)
        for wx, wy in ((22, 115), (38, 210)):
            canvas.saveState()
            canvas.translate(wx * mm, tela.altura_pagina - wy * mm)
            canvas.rotate(35)
            canvas.drawString(0, 0, marca_dagua)
            canvas.restoreState()
        canvas.restoreState()

    faixa_h = 12.0
    y_topo = tela.y_()
    canvas.setFillColor(cor_tema)
    canvas.rect(x_(0), y_topo - faixa_h * mm, _LARGURA * mm, faixa_h * mm, stroke=0, fill=1)

    canvas.setFillColor(
        tela.colors.Color(
            min(1, cor_tema.red + 0.12),
            min(1, cor_tema.green + 0.12),
            min(1, cor_tema.blue + 0.12),
        )
    )
    canvas.rect(x_(0), y_topo - 1.2 * mm, _LARGURA * mm, 1.2 * mm, stroke=0, fill=1)

    logo_texto = tema.get("logo_texto")
    empresa_x = 3.5
    largura_selo = 26.0
    if logo_texto:
        canvas.setFillColor(tela.white)
        canvas.roundRect(
            x_(2.5), y_topo - 9.5 * mm, largura_selo * mm, 7.0 * mm, 1.2 * mm, stroke=0, fill=1
        )
        # O selo tem largura fixa: nome de empresa mais longo encolhe até caber
        # em vez de transbordar para cima da faixa.
        marca, corpo = tela.cabe_corpo(logo_texto, (largura_selo - 2.0) * mm, tam=8.5, minimo=5.5)
        texto(
            0,
            y_topo - 7.2 * mm,
            marca,
            fonte="Helvetica-Bold",
            tam=corpo,
            cor=cor_tema,
            centro_x=x_(2.5 + largura_selo / 2),
        )
        empresa_x = 32.0

    if tema.get("empresa"):
        # Da esquerda até onde a parcela começa, à direita.
        limite = _LARGURA - 3 - empresa_x
        if tema.get("parcela_texto"):
            limite -= tela.canvas.stringWidth(tema["parcela_texto"], "Helvetica-Bold", 11) / mm + 4
        empresa, corpo = tela.cabe_corpo(tema["empresa"], limite * mm, tam=11, minimo=7)
        texto(
            x_(empresa_x),
            y_topo - 7.4 * mm,
            empresa,
            fonte="Helvetica-Bold",
            tam=corpo,
            cor=tela.white,
        )

    if tema.get("parcela_texto"):
        texto(
            0,
            y_topo - 7.6 * mm,
            tema["parcela_texto"],
            fonte="Helvetica-Bold",
            tam=11,
            cor=tela.white,
            dir_x=x_(_LARGURA - 3),
        )

    tela.avanca(faixa_h + 2.5)

    if tema.get("rodape"):
        texto(0, 8.0 * mm, tema["rodape"], tam=7, cor=cor_tema, centro_x=x_(_LARGURA / 2))
    canvas.setFillColor(cor_tema)
    canvas.rect(0, 0, 210 * mm, 3.5 * mm, stroke=0, fill=1)


def _chips_destaque(tela, chips: list[tuple[str, str]], tema: dict | None = None) -> None:
    """Chips com contraste, tipografia forte e borda na cor do tema.

    Os três valores ficam alinhados à esquerda, de propósito: o chip é um cartão
    de leitura, não coluna de soma — é o único lugar do boleto em que o valor
    acompanha o rótulo.
    """
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    chip_w = (_LARGURA - 2 * _CHIP_GAP) / 3
    y_topo = tela.y_()
    cor_borda = _cor_tema(tela, tema) if tema else tela.borda

    for i, (rotulo, valor) in enumerate(chips):
        cx = i * (chip_w + _CHIP_GAP)

        canvas.setFillColor(tela.HexColor("#F0F3F7"))
        canvas.roundRect(
            x_(cx),
            y_topo - _CHIP_H * mm,
            chip_w * mm,
            _CHIP_H * mm,
            _RADIUS * mm,
            stroke=0,
            fill=1,
        )
        canvas.setStrokeColor(cor_borda)
        canvas.setLineWidth(0.9 if tema else 0.5)
        canvas.roundRect(
            x_(cx),
            y_topo - _CHIP_H * mm,
            chip_w * mm,
            _CHIP_H * mm,
            _RADIUS * mm,
            stroke=1,
            fill=0,
        )

        if tema:
            canvas.setFillColor(cor_borda)
            canvas.roundRect(
                x_(cx),
                y_topo - 2.2 * mm,
                chip_w * mm,
                2.2 * mm,
                _RADIUS * mm,
                stroke=0,
                fill=1,
            )
            canvas.rect(x_(cx), y_topo - 2.2 * mm, chip_w * mm, 1.1 * mm, stroke=0, fill=1)

        util = (chip_w - 5.2) * mm
        texto(
            x_(cx) + 2.6 * mm,
            y_topo - 5.0 * mm,
            tela.cabe(rotulo.upper(), util, tam=6),
            tam=6,
            cor=tela.rotulo,
        )
        texto(
            x_(cx) + 2.6 * mm,
            y_topo - (_CHIP_H - 4.0) * mm,
            tela.cabe(valor, util, fonte="Helvetica-Bold", tam=_CHIP_TAM),
            fonte="Helvetica-Bold",
            tam=_CHIP_TAM,
        )

    tela.avanca(_CHIP_H + 2.0 + _RESPIRO)


def _linha_corte(tela) -> None:
    canvas, mm, x_ = tela.canvas, tela.mm, tela.x_
    tela.avanca(3.2)
    canvas.setStrokeColor(tela.HexColor("#999999"))
    canvas.setLineWidth(0.35)
    canvas.line(x_(0), tela.y_(), x_(_LARGURA), tela.y_())
    tela.texto(0, tela.y_() - 2.3 * mm, "Corte aqui", tam=5.2, cor=tela.rotulo, dir_x=x_(_LARGURA))
    tela.avanca(_CORTE_H)


def _bloco_instrucoes_pix(tela, info, tem_pix: bool, tema: dict | None = None) -> None:
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    n_tot = 6 if tem_pix else 5
    h_instr = _TOT_H * n_tot
    w_instr = _LARGURA * (0.57 if tem_pix else 0.75)
    w_pix = _LARGURA * 0.18 if tem_pix else 0.0
    w_tot = _LARGURA - w_instr - w_pix
    y_topo = tela.y_()
    cor_pix = _cor_tema(tela, tema) if tema else tela.pix_cor

    canvas.setLineWidth(0.45)
    canvas.setStrokeColor(tela.borda)
    canvas.rect(x_(0), y_topo - h_instr * mm, w_instr * mm, h_instr * mm, stroke=1, fill=0)
    texto(
        x_(1.2),
        y_topo - 2.8 * mm,
        "Instruções (Texto de responsabilidade do beneficiário)",
        tam=5.8,
        cor=tela.rotulo,
    )
    # Quantas linhas cabem na moldura: sem PIX ela tem 28,2 mm e a sétima linha
    # cairia em 28,2 — na própria borda. O limite sai da altura, não de um
    # número fixo, porque a moldura muda de tamanho conforme haja PIX.
    cabem = int((h_instr - _TOPO_INSTR - 1.5) / _LINHA_INSTR) + 1
    util_instr = (w_instr - 2.4) * mm
    for i, ln in enumerate(info.instrucoes[:cabem]):
        texto(x_(1.2), y_topo - (_TOPO_INSTR + _LINHA_INSTR * i) * mm, tela.cabe(ln, util_instr))

    if tem_pix:
        px = w_instr
        canvas.rect(x_(px), y_topo - h_instr * mm, w_pix * mm, h_instr * mm, stroke=1, fill=0)
        cab_h = 11 * _PT
        canvas.setFillColor(cor_pix)
        canvas.rect(x_(px), y_topo - cab_h * mm, w_pix * mm, cab_h * mm, stroke=0, fill=1)
        texto(
            0,
            y_topo - 2.8 * mm,
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
    for i, (rot, chave) in enumerate(_TOTALIZADORES):
        canvas.setStrokeColor(tela.borda)
        canvas.rect(
            x_(x_tot),
            y_topo - (i + 1) * h_lado * mm,
            w_tot * mm,
            h_lado * mm,
            stroke=1,
            fill=0,
        )
        if i == len(_TOTALIZADORES) - 1:
            canvas.setFillColor(tela.HexColor("#F0F3F7"))
            canvas.rect(
                x_(x_tot) + 0.3,
                y_topo - (i + 1) * h_lado * mm + 0.3,
                w_tot * mm - 0.6,
                h_lado * mm - 0.6,
                stroke=0,
                fill=1,
            )
        texto(
            x_(x_tot) + 1.2 * mm,
            y_topo - (i * h_lado + 2.8) * mm,
            rot,
            tam=5.8,
            cor=tela.rotulo,
        )
        texto(
            0,
            y_topo - (i * h_lado + h_lado - 1.6) * mm,
            info.total(chave),
            fonte="Helvetica-Bold",
            tam=8.5,
            dir_x=x_(x_tot + w_tot - 1.5),
        )
    tela.avanca(h_instr)


def recibo_moderno(tela, info, tema: dict | None = None) -> None:
    """Recibo do Pagador com chips destacados e grade alinhada."""
    celula = tela.celula
    r2, r3 = _linhas6(info)

    rotulo_dir(tela, "Recibo do Pagador", italico=True)
    cabecalho_moderno(tela, info, info.linha_digitavel)
    tela.avanca(1.8 + _RESPIRO * 0.5)

    _chips_destaque(
        tela,
        [
            ("Vencimento", info.vencimento),
            ("Valor do Documento", info.valor_documento),
            ("Nosso Número", info.nosso_numero),
        ],
        tema=tema,
    )

    celula(
        0,
        142,
        12.0,
        "Beneficiário",
        info.beneficiario,
        negrito=True,
        linha2=info.beneficiario_endereco,
    )
    celula(
        142,
        48,
        12.0,
        "Valor do Documento",
        info.valor_documento,
        negrito=True,
        destaque=True,
        alinhar_dir=True,
    )
    tela.avanca(12.0 + _RESPIRO * 0.3)

    for (rot, val, dir_), cx, cw in zip(r2, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot, val, alinhar_dir=dir_)
    tela.avanca(7.0)
    for (rot, val, dir_), cx, cw in zip(r3, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot, val, alinhar_dir=dir_)
    tela.avanca(7.0 + _RESPIRO * 0.3)

    w5 = _LARGURA / 5
    for i, (rot, chave) in enumerate(_TOTALIZADORES):
        celula(i * w5, w5, _FAIXA_TOTAIS_H, rot, info.total(chave), alinhar_dir=True)
    tela.avanca(_FAIXA_TOTAIS_H + _RESPIRO * 0.3)

    celula(0, 190, 12.0, "Sacado", info.sacado_curto, negrito=True, linha2=info.sacado_endereco)
    tela.avanca(12.0)
    rotulo_dir(tela, "Autenticação mecânica - Recibo do Pagador")


def ficha_moderna(tela, info, tema: dict | None = None) -> None:
    """Ficha de Compensação: instruções | PIX | totalizadores, grade alinhada."""
    canvas, mm, x_ = tela.canvas, tela.mm, tela.x_
    celula = tela.celula
    r2, r3 = _linhas6(info)
    tem_pix = info.tem_pix

    cabecalho_moderno(tela, info, info.linha_digitavel)
    tela.avanca(_RESPIRO * 0.3)

    celula(0, 142, 7.5, "Local de pagamento", info.local_pagamento, negrito=True)
    celula(
        142, 48, 7.5, "Vencimento", info.vencimento, negrito=True, destaque=True, alinhar_dir=True
    )
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
    celula(
        142,
        48,
        12.0,
        "Valor do Documento",
        info.valor_documento,
        negrito=True,
        destaque=True,
        alinhar_dir=True,
    )
    tela.avanca(12.0)

    for (rot, val, dir_), cx, cw in zip(r2, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot, val, alinhar_dir=dir_)
    tela.avanca(7.0)
    for (rot, val, dir_), cx, cw in zip(r3, _X6, _C6, strict=True):
        celula(cx, cw, 7.0, rot, val, alinhar_dir=dir_)
    tela.avanca(7.0 + _RESPIRO * 0.3)

    _bloco_instrucoes_pix(tela, info, tem_pix, tema=tema)

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
