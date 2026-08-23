"""Modelo **Boleto Clássico**: layout tradicional (bordas pretas, rótulos em caixa alta).

Blocos: :func:`cabecalho_classico`, :func:`recibo_classico` e :func:`ficha_classica`.
Cada um recebe a :class:`~pycobranca.render.tela.Tela` e os dados
(:class:`~pycobranca.render.dados.DadosBoleto`) e desenha avançando o cursor.

:func:`desenha` é o ponto de entrada do modelo (contrato do catálogo em
:mod:`pycobranca.render.modelos`): monta a página inteira na ordem correta.
"""

from __future__ import annotations

from ..blocos import bloco_demonstrativo, corte, rotulo_dir
from ..comum import _LARGURA, _desenha_barcode, _desenha_logo, _desenha_qr

__all__ = ["desenha", "cabecalho_classico", "recibo_classico", "ficha_classica"]

#: paleta do modelo (bordas pretas); ver :class:`pycobranca.render.tela.Tela`
MODERNO = False


def desenha(tela, info, contexto) -> None:
    """Página inteira do boleto clássico, na ordem: recibo, demonstrativo, corte, ficha."""
    recibo_classico(tela, info)
    if info.demonstrativo:
        bloco_demonstrativo(tela, info)
    corte(tela)
    ficha_classica(tela, info)


def cabecalho_classico(tela, info, texto_dir, *, linha_digitavel) -> None:
    """Cabeçalho clássico: sigla/logo do banco, código-DV entre réguas e texto à direita."""
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    h = 10.0
    y_topo = tela.y_()
    if tela.logo_reader is not None:
        _desenha_logo(canvas, mm, tela.logo_reader, x_(0), y_topo, 56.0, h - 2.0)
    else:
        canvas.setFillColor(tela.marca)
        canvas.roundRect(x_(0), y_topo - 9 * mm, 8 * mm, 8 * mm, 1.4 * mm, stroke=0, fill=1)
        texto(
            0,
            y_topo - 6.8 * mm,
            info.banco_sigla,
            fonte="Helvetica-Bold",
            tam=11,
            cor=tela.white,
            dir_x=x_(0) + 7.0 * mm,
        )
        # Da sigla até a régua de x_(62). Os 18 nomes cabem a 10 pt; a contenção
        # é para o nome vindo de um banco novo ou personalizado.
        nome, corpo = tela.cabe_corpo(info.banco_nome, (62 - 10 - 1.5) * mm, tam=10)
        texto(x_(10), y_topo - 6.5 * mm, nome, fonte="Helvetica-Bold", tam=corpo)
    canvas.setStrokeColor(tela.marca)
    canvas.setLineWidth(1.2)
    canvas.line(x_(62), y_topo, x_(62), y_topo - h * mm)
    canvas.line(x_(82), y_topo, x_(82), y_topo - h * mm)
    texto(
        0,
        y_topo - 7 * mm,
        info.banco_dv,
        fonte="Helvetica-Bold",
        tam=13,
        centro_x=x_(72),
    )
    if linha_digitavel:
        # 9,5 dava 307,8 pt de largura para um vão de 306,1 — a régua de x_(82)
        # passava por cima do primeiro dígito, e o "3" era lido como "B". Como o
        # texto é alinhado à direita, a ponta esquerda cai onde a largura levar.
        # 9,0 é o maior corpo que ainda cabe: a linha digitável é para ser lida
        # e digitada, então encolher mais do que o necessário é prejuízo.
        texto(0, y_topo - 7 * mm, texto_dir, fonte="Courier-Bold", tam=9.0, dir_x=x_(_LARGURA))
    else:
        texto(0, y_topo - 7.2 * mm, texto_dir, fonte="Helvetica-Bold", tam=12, dir_x=x_(_LARGURA))
    canvas.setStrokeColor(tela.marca)
    canvas.setLineWidth(1.8)
    canvas.line(x_(0), y_topo - h * mm, x_(_LARGURA), y_topo - h * mm)
    tela.avanca(h)


def recibo_classico(tela, info) -> None:
    """Recibo do Sacado (topo da folha, acima do corte)."""
    celula = tela.celula
    cabecalho_classico(tela, info, "Recibo do Sacado", linha_digitavel=False)
    rotulo_dir(tela, "AUTENTICAÇÃO MECÂNICA")
    h = 8.0
    celula(0, 76, h, "Cedente", info.beneficiario_nome, negrito=True)
    celula(
        76,
        38,
        h,
        "Agência / Código Cedente",
        info.agencia_codigo,
        alinhar_dir=True,
    )
    celula(114, 38, h, "CPF/CNPJ Cedente", info.beneficiario_documento, alinhar_dir=True)
    celula(152, 38, h, "Vencimento", info.vencimento, negrito=True, alinhar_dir=True)
    tela.avanca(h)
    celula(0, 76, h, "Sacado", info.sacado_curto, negrito=True)
    celula(76, 38, h, "Nosso Número", info.nosso_numero, alinhar_dir=True)
    celula(114, 38, h, "Nº do documento", info.doc_numero, alinhar_dir=True)
    celula(152, 38, h, "Data Documento", info.doc_data, alinhar_dir=True)
    tela.avanca(h)
    celula(0, 142, h, "Endereço Cedente", info.beneficiario_endereco)
    celula(
        142,
        48,
        h,
        "(=) Valor Documento",
        info.valor_documento,
        negrito=True,
        tam=10,
        alinhar_dir=True,
    )
    tela.avanca(h)


def ficha_classica(tela, info) -> None:
    """Ficha de Compensação clássica: instruções, sacado com QR e código de barras 103×13mm."""
    canvas, mm, x_, texto, celula = tela.canvas, tela.mm, tela.x_, tela.texto, tela.celula
    tem_pix = info.tem_pix

    cabecalho_classico(tela, info, info.linha_digitavel, linha_digitavel=True)
    h = 8.0
    celula(0, 142, h, "Local de pagamento", info.local_pagamento)
    celula(142, 48, h, "Vencimento", info.vencimento, negrito=True, tam=10, alinhar_dir=True)
    tela.avanca(h)
    celula(0, 142, h, "Cedente", info.beneficiario, negrito=True)
    celula(
        142,
        48,
        h,
        "Agência/Código cedente",
        info.agencia_codigo,
        alinhar_dir=True,
    )
    tela.avanca(h)
    celula(0, 32, h, "Data do documento", info.doc_data)
    celula(32, 40, h, "N. do documento", info.doc_numero)
    celula(72, 22, h, "Espécie doc", info.doc_especie)
    celula(94, 18, h, "Aceite", info.doc_aceite)
    celula(112, 34, h, "Data processamento", info.doc_processamento)
    celula(146, 44, h, "Nosso número", info.nosso_numero, negrito=True, alinhar_dir=True)
    tela.avanca(h)
    celula(0, 32, h, "Uso do Banco", "")
    celula(32, 40, h, "Carteira", info.carteira)
    celula(72, 22, h, "Espécie", info.especie_moeda)
    celula(94, 18, h, "Quantidade", info.quantidade, alinhar_dir=True)
    celula(112, 34, h, "Valor", "")
    celula(
        146,
        44,
        h,
        "(=) Valor documento",
        info.valor_documento,
        negrito=True,
        tam=10,
        alinhar_dir=True,
    )
    tela.avanca(h)

    # 30 mm davam 6 mm por totalizador: rótulo e valor caíam na mesma linha, e
    # "(-) DESCONTO / ABATIMENTOS" deixava 46 pt — um valor de sete dígitos
    # (49,6 pt) passava por cima do rótulo. A 40 mm o número tem linha própria.
    # De quebra, o bloco de instruções passa a comportar 8 linhas: a sétima
    # chegava a 31 mm e transbordava a moldura.
    h_instr = 40.0
    y_topo = tela.y_()
    canvas.setLineWidth(0.5)
    canvas.setStrokeColor(tela.borda)
    canvas.rect(x_(0), y_topo - h_instr * mm, 142 * mm, h_instr * mm, stroke=1, fill=0)
    texto(
        x_(1.2),
        y_topo - 3.0 * mm,
        "INSTRUÇÕES (TEXTO DE RESPONSABILIDADE DO BENEFICIÁRIO)",
        tam=5.5,
        cor=tela.rotulo,
    )
    # A instrução é texto livre do beneficiário: sem corte, uma linha comprida
    # saía pela lateral da página (708 pt numa folha de 595), e a nona linha
    # caía abaixo da moldura. O moderno já limitava os dois; aqui não.
    cabem = int((h_instr - 7.0 - 1.5) / 4.0) + 1
    util_instr = (142 - 2.4) * mm
    for i, ln in enumerate(info.instrucoes[:cabem]):
        texto(x_(1.2), y_topo - (7.0 + 4.0 * i) * mm, tela.cabe(ln, util_instr), tam=8.5)
    lados = [
        ("(-) DESCONTO / ABATIMENTOS", "desconto_abatimento"),
        ("(-) OUTRAS DEDUÇÕES", "outras_deducoes"),
        ("(+) MORA / MULTA", "mora_multa"),
        ("(+) OUTROS ACRÉSCIMOS", "outros_acrescimos"),
        ("(=) VALOR COBRADO", "valor_cobrado"),
    ]
    h_lado = h_instr / len(lados)
    for i, (rot_c, chave) in enumerate(lados):
        canvas.setStrokeColor(tela.borda)
        canvas.rect(x_(142), y_topo - (i + 1) * h_lado * mm, 48 * mm, h_lado * mm, stroke=1, fill=0)
        texto(x_(143.2), y_topo - (i * h_lado + 2.8) * mm, rot_c, tam=5.5, cor=tela.rotulo)
        texto(
            0,
            y_topo - (i * h_lado + h_lado - 1.6) * mm,
            info.total(chave),
            fonte="Helvetica-Bold",
            tam=8.5,
            dir_x=x_(188.5),
        )
    tela.avanca(h_instr)

    h_sac = 26.0
    y_topo = tela.y_()
    canvas.setStrokeColor(tela.borda)
    canvas.rect(x_(0), y_topo - h_sac * mm, 142 * mm, h_sac * mm, stroke=1, fill=0)
    # Este bloco é desenhado fora de `celula`, então a contenção de largura
    # precisa ser explícita: a moldura tem 142 mm e o recuo é de 1,2 mm.
    util = (142 - 2.4) * mm
    texto(x_(1.2), y_topo - 3.0 * mm, "SACADO", tam=5.5, cor=tela.rotulo)
    texto(
        x_(1.2),
        y_topo - 7.0 * mm,
        tela.cabe(info.sacado_curto, util, fonte="Helvetica-Bold", tam=8.5),
        fonte="Helvetica-Bold",
        tam=8.5,
    )
    texto(x_(1.2), y_topo - 11.0 * mm, tela.cabe(info.sacado_endereco, util, tam=8.5), tam=8.5)
    texto(
        x_(1.2),
        y_topo - (h_sac - 2.5) * mm,
        tela.cabe(
            f"SACADOR / AVALISTA: {info.sacador_avalista or '—'}    "
            f"CÓDIGO DE BAIXA: {info.codigo_baixa}",
            util,
            tam=6,
        ),
        tam=6,
        cor=tela.rotulo,
    )
    canvas.setStrokeColor(tela.borda)
    canvas.rect(x_(142), y_topo - h_sac * mm, 48 * mm, h_sac * mm, stroke=1, fill=0)
    if tem_pix:
        texto(
            0,
            y_topo - 3.4 * mm,
            "PAGUE COM PIX",
            fonte="Helvetica-Bold",
            tam=6,
            cor=tela.pix_cor,
            dir_x=x_(142) + 46 * mm,
        )
        lado_qr = 20.0
        _desenha_qr(
            canvas,
            mm,
            info.qrcode_matrix,
            x_(142) + (48 - lado_qr) / 2 * mm,
            y_topo - 25 * mm,
            lado_qr,
            tela.black,
        )
    tela.avanca(h_sac)

    tela.avanca(3.0)
    bar_w, bar_h = 103.0, 13.0
    y_base = tela.y_(bar_h)
    _desenha_barcode(canvas, mm, info.codigo_barras, x_(0), y_base, bar_w, bar_h, tela.black)
    texto(
        0,
        y_base + 1 * mm,
        "AUTENTICAÇÃO MECÂNICA · FICHA DE COMPENSAÇÃO",
        tam=6,
        cor=tela.rotulo,
        dir_x=x_(_LARGURA),
    )
