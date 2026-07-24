"""Backend ReportLab — boletos em Python puro, nos modelos clássico e moderno.

Renderização de alto volume ou serverless, sem dependências de sistema. O
código de barras é desenhado nativamente a partir de ``codigo_barras`` (os 44
dígitos) e o QR do Bolepix a partir de ``pix.qrcode_matrix`` (matriz de 0/1 por
linha), quando presente.

Logo opt-in: se ``banco.logo`` (bytes de PNG/JPEG ou caminho de arquivo) for
informado, ele é desenhado no cabeçalho no lugar do nome do banco em texto,
preservando a proporção. É um **mecanismo** — a biblioteca desenha o asset que o
chamador fornecer e **não embute marcas registradas** de bancos.

Modelos do boleto:

- ``modelo="classico"``: layout tradicional (bordas pretas, rótulo do recibo no
  cabeçalho, código de barras 103×13mm, QR na linha do sacado).
- ``modelo="moderno"``: Recibo do Pagador com chips, célula PIX central no bloco
  de instruções (57% | 18% | 25%) com cabeçalho teal ``#32BCAD``, paleta cinza,
  "Corte aqui" e código de barras 68% × 48pt.

:func:`render_carne_pdf` gera o carnê: 3 parcelas por A4, canhoto
aberto à esquerda (~42mm), ficha compacta com célula PIX e código de barras de
32pt.

O ``reportlab`` é importado sob demanda (só ao gerar o PDF), mantendo o import
do pacote leve; ele é dependência padrão, então já vem instalado.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from .barcode import sequencia_i2of5

__all__ = ["render_boleto_pdf", "render_carne_pdf"]


@dataclass
class _Cursor:
    """Posição vertical corrente (mm a partir do topo da área útil).

    Substitui o antigo truque ``topo = [0.0]`` (lista de 1 elemento usada como
    célula mutável para escrita em closures): ``cur.avanca(h)`` avança o cursor
    e lê-se ``cur.y``, o que torna o fluxo de layout explícito e legível.
    """

    y: float = 0.0

    def avanca(self, mm_: float) -> None:
        self.y += mm_


_PT = 0.352778  # 1pt em mm
_LARGURA = 190.0  # área útil A4 (margens de 10mm)
_MARGEM = 10.0

# Constantes do modelo moderno (boleto com Bolepix e carnê)
_CINZA_BORDA = "#B3B3B3"
_CINZA_FORTE = "#333333"
_CINZA_ROTULO = "#777777"
_DESTAQUE_BG = "#F7F7F7"
_COR_PIX = "#32BCAD"
_TOT_H = 16 * _PT  # TOTALIZADORES_HEIGHT
_BARCODE_H = 48 * _PT  # BARCODE_HEIGHT (boleto)
_BARCODE_FRAC = 0.68


def _canvas_e_libs():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen.canvas import Canvas
    except ModuleNotFoundError as exc:  # pragma: no cover - dependência opcional
        raise RuntimeError(
            "ReportLab não está instalado. Reinstale: pip install --force-reinstall pycobranca."
        ) from exc
    return colors, A4, mm, Canvas


def _desenha_barcode(canvas, mm, codigo, x_abs, y_base, largura_mm, altura_mm, cor):
    seq = sequencia_i2of5(codigo)
    total = sum(u for _, u in seq)
    x_dim = largura_mm / total
    canvas.setFillColor(cor)
    x = x_abs
    for e_barra, unidades in seq:
        w = unidades * x_dim * mm
        if e_barra:
            canvas.rect(x, y_base, w, altura_mm * mm, stroke=0, fill=1)
        x += w


def _desenha_qr(canvas, mm, matriz, x_abs, y_base, lado_mm, cor):
    modulo = lado_mm / len(matriz)
    canvas.setFillColor(cor)
    n = len(matriz)
    for ri, linha in enumerate(matriz):
        for ci, on in enumerate(linha):
            if on:
                canvas.rect(
                    x_abs + ci * modulo * mm,
                    y_base + (n - 1 - ri) * modulo * mm,
                    modulo * mm,
                    modulo * mm,
                    stroke=0,
                    fill=1,
                )


def _carrega_logo(fonte):
    """Converte a fonte do logo num ``ImageReader`` do ReportLab (ou ``None``).

    O logo é **opcional e fornecido pelo chamador** (``banco.logo`` no contexto):
    a biblioteca desenha o que for entregue e **não embute marcas registradas**
    de bancos. Aceita:

    - ``bytes`` de um PNG/JPEG;
    - caminho de arquivo (``str``/``os.PathLike``);
    - um ``ImageReader`` já pronto;
    - ``None`` (sem logo — usa o nome do banco em texto).
    """
    if fonte is None:
        return None
    from reportlab.lib.utils import ImageReader

    if isinstance(fonte, ImageReader):
        return fonte
    if isinstance(fonte, bytes | bytearray):
        return ImageReader(BytesIO(bytes(fonte)))
    return ImageReader(fonte)


def _desenha_logo(canvas, mm, reader, x_abs, y_topo, max_w, max_h):
    """Desenha o logo dentro da caixa ``max_w × max_h`` (mm), a partir do topo
    ``y_topo``, preservando a proporção e centralizado na vertical da caixa.

    ``x_abs``/``y_topo`` já vêm em pontos; ``max_w``/``max_h`` em mm.
    """
    lw, lh = reader.getSize()
    escala = min(max_w / lw, max_h / lh)
    dw, dh = lw * escala, lh * escala
    y_base = y_topo - ((max_h + dh) / 2) * mm
    canvas.drawImage(reader, x_abs, y_base, dw * mm, dh * mm, mask="auto", preserveAspectRatio=True)


def _faz_texto(canvas, x, y_abs, s, *, fonte, tam, cor, dir_x, centro_x):
    """Escreve ``s`` no canvas: à direita (``dir_x``), centralizado (``centro_x``)
    ou à esquerda (``x``). Primitivo compartilhado pelo boleto e pelo carnê."""
    canvas.setFont(fonte, tam)
    canvas.setFillColor(cor)
    if dir_x is not None:
        canvas.drawRightString(dir_x, y_abs, s)
    elif centro_x is not None:
        canvas.drawCentredString(centro_x, y_abs, s)
    else:
        canvas.drawString(x, y_abs, s)


@dataclass(frozen=True)
class _Info:
    """Informações de um boleto/parcela — **fonte única de dados** dos renderizadores.

    Separa dados (isto) do desenho (layout): boleto e carnê consomem estes campos e
    não acessam o dicionário de contexto diretamente, o que facilita criar novos
    temas/layouts sem mexer na extração de dados.
    """

    banco_nome: str
    banco_dv: str
    banco_sigla: str
    banco_cor: str
    banco_logo: Any
    linha_digitavel: str
    local_pagamento: str
    vencimento: str
    valor_documento: str
    nosso_numero: str
    carteira: str
    especie_moeda: str
    quantidade: str
    beneficiario_nome: str
    beneficiario_documento: str
    beneficiario_endereco: str
    agencia_codigo: str
    doc_data: str
    doc_numero: str
    doc_especie: str
    doc_aceite: str
    doc_processamento: str
    sacado_nome: str
    sacado_documento: str
    sacado_endereco: str
    instrucoes: list
    demonstrativo: str
    codigo_barras: str
    sacador_avalista: str | None
    codigo_baixa: str
    tem_pix: bool
    qrcode_matrix: list | None

    @property
    def beneficiario(self) -> str:
        return f"{self.beneficiario_nome} - {self.beneficiario_documento}"

    @property
    def sacado_curto(self) -> str:
        return f"{self.sacado_nome} - {self.sacado_documento}"

    @property
    def sacado_completo(self) -> str:
        return f"{self.sacado_nome} - {self.sacado_documento} — {self.sacado_endereco}"


def _informacoes(d: dict[str, Any]) -> _Info:
    """Constrói o view-model a partir do dicionário de contexto."""
    banco = d.get("banco", {})
    benef = d["beneficiario"]
    doc = d["documento"]
    pagador = d["pagador"]
    pix = d.get("pix") or {}
    return _Info(
        banco_nome=banco["nome"],
        banco_dv=banco["codigo_dv"],
        banco_sigla=banco.get("sigla", ""),
        banco_cor=banco.get("cor", "#003a70"),
        banco_logo=banco.get("logo"),
        linha_digitavel=d["linha_digitavel"],
        local_pagamento=d["local_pagamento"],
        vencimento=d["vencimento"],
        valor_documento=d["valor_documento"],
        nosso_numero=d["nosso_numero"],
        carteira=d["carteira"],
        especie_moeda=d["especie_moeda"],
        quantidade=str(d.get("quantidade") or ""),
        beneficiario_nome=benef["nome"],
        beneficiario_documento=benef["documento"],
        beneficiario_endereco=benef["endereco"],
        agencia_codigo=benef["agencia_codigo"],
        doc_data=doc["data"],
        doc_numero=doc["numero"],
        doc_especie=doc["especie"],
        doc_aceite=doc["aceite"],
        doc_processamento=doc["data_processamento"],
        sacado_nome=pagador["nome"],
        sacado_documento=pagador["documento"],
        sacado_endereco=pagador["endereco"],
        instrucoes=d.get("instrucoes") or [],
        demonstrativo=d.get("demonstrativo") or "",
        codigo_barras=d["codigo_barras"],
        sacador_avalista=d.get("sacador_avalista"),
        codigo_baixa=d.get("codigo_baixa") or "",
        tem_pix=bool(pix.get("habilitado") and pix.get("qrcode_matrix")),
        qrcode_matrix=pix.get("qrcode_matrix"),
    )


def render_boleto_pdf(contexto: dict[str, Any], modelo: str = "moderno") -> bytes:
    """Gera o PDF do boleto (recibo + ficha) com ReportLab.

    Args:
        contexto: dicionário de contexto do boleto; usa ``codigo_barras``
            (44 dígitos) e, opcionalmente, ``pix.qrcode_matrix`` e ``banco.logo``
            (bytes de PNG/JPEG ou caminho — logo opt-in do cabeçalho).
        modelo: ``"moderno"`` (padrão — Recibo do Pagador com chips, célula PIX
            e paleta teal; a célula PIX aparece só quando há dados de PIX) ou
            ``"classico"`` (layout tradicional).

    Returns:
        Bytes do PDF (uma página A4).
    """
    if modelo not in ("classico", "moderno"):
        raise ValueError(f"modelo inválido: {modelo!r} (use 'classico' ou 'moderno')")
    colors, A4, mm, Canvas = _canvas_e_libs()
    HexColor, black, white = colors.HexColor, colors.black, colors.white

    d = contexto
    info = _informacoes(d)
    logo_reader = _carrega_logo(info.banco_logo)
    moderno = modelo == "moderno"
    marca = HexColor(info.banco_cor)
    borda = HexColor(_CINZA_BORDA) if moderno else black
    rotulo = HexColor(_CINZA_ROTULO) if moderno else HexColor("#5b6672")
    destaque_bg = HexColor(_DESTAQUE_BG)
    pix_cor = HexColor(_COR_PIX)

    buf = BytesIO()
    canvas = Canvas(buf, pagesize=A4)
    _, altura_pagina = A4

    cur = _Cursor()

    def x_(v):
        return (_MARGEM + v) * mm

    def y_(h=0.0):
        return altura_pagina - (_MARGEM + cur.y + h) * mm

    def texto(x, y_abs, s, *, fonte="Helvetica", tam=8.5, cor=black, dir_x=None, centro_x=None):
        _faz_texto(
            canvas, x, y_abs, s, fonte=fonte, tam=tam, cor=cor, dir_x=dir_x, centro_x=centro_x
        )

    def rot_fmt(rot):
        return rot if moderno else rot.upper()

    def celula(
        x,
        w,
        h,
        rot,
        val,
        *,
        negrito=False,
        tam=8.5,
        alinhar_dir=False,
        destaque=False,
        dy=0.0,
        linha2=None,
    ):
        y_topo = y_() - dy * mm
        if destaque and moderno:
            canvas.setFillColor(destaque_bg)
            canvas.rect(x_(x), y_topo - h * mm, w * mm, h * mm, stroke=0, fill=1)
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(borda)
        canvas.rect(x_(x), y_topo - h * mm, w * mm, h * mm, stroke=1, fill=0)
        texto(x_(x) + 1.2 * mm, y_topo - 2.8 * mm, rot_fmt(rot), tam=5.8, cor=rotulo)
        fonte = "Helvetica-Bold" if negrito else "Helvetica"
        y_val = y_topo - (6.4 if linha2 else h - 1.8) * mm
        if alinhar_dir:
            texto(0, y_val, val, fonte=fonte, tam=tam, dir_x=x_(x) + (w - 1.5) * mm)
        else:
            texto(x_(x) + 1.2 * mm, y_val, val, fonte=fonte, tam=tam)
        if linha2:
            texto(x_(x) + 1.2 * mm, y_topo - (h - 2.0) * mm, linha2, tam=8)

    def cabecalho_moderno(texto_dir):
        """Cabeçalho do modelo moderno: nome do banco em texto, barras pretas, régua fina."""
        h = 9.0
        y_topo = y_()
        if logo_reader is not None:
            _desenha_logo(canvas, mm, logo_reader, x_(0), y_topo, 40.0, h - 1.0)
        else:
            texto(x_(0), y_topo - 6.2 * mm, info.banco_nome, fonte="Helvetica-Bold", tam=12)
        canvas.setStrokeColor(black)
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
        cur.avanca(h)

    def cabecalho_classico(texto_dir, *, linha_digitavel):
        h = 10.0
        y_topo = y_()
        if logo_reader is not None:
            _desenha_logo(canvas, mm, logo_reader, x_(0), y_topo, 56.0, h - 2.0)
        else:
            canvas.setFillColor(marca)
            canvas.roundRect(x_(0), y_topo - 9 * mm, 8 * mm, 8 * mm, 1.4 * mm, stroke=0, fill=1)
            texto(
                0,
                y_topo - 6.8 * mm,
                info.banco_sigla,
                fonte="Helvetica-Bold",
                tam=11,
                cor=white,
                dir_x=x_(0) + 7.0 * mm,
            )
            texto(x_(10), y_topo - 6.5 * mm, info.banco_nome, fonte="Helvetica-Bold", tam=10)
        canvas.setStrokeColor(marca)
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
            texto(0, y_topo - 7 * mm, texto_dir, fonte="Courier-Bold", tam=9.5, dir_x=x_(_LARGURA))
        else:
            texto(
                0, y_topo - 7.2 * mm, texto_dir, fonte="Helvetica-Bold", tam=12, dir_x=x_(_LARGURA)
            )
        canvas.setStrokeColor(marca)
        canvas.setLineWidth(1.8)
        canvas.line(x_(0), y_topo - h * mm, x_(_LARGURA), y_topo - h * mm)
        cur.avanca(h)

    def rotulo_dir(txt, *, italico=False):
        texto(
            0,
            y_() - 2.6 * mm,
            txt,
            fonte="Helvetica-Oblique" if italico else "Helvetica",
            tam=6.5,
            cor=rotulo,
            dir_x=x_(_LARGURA),
        )
        cur.avanca(4.0)

    tem_pix = info.tem_pix
    qrcode_matrix = info.qrcode_matrix
    benef_2li = info.beneficiario
    sacado_li = info.sacado_curto

    # ---- TEMA (referência boleto_tema.png) — só no modelo moderno ----
    tema = d.get("tema") or {}
    tem_tema = bool(moderno and tema.get("habilitado"))

    def desenha_tema():
        cor_tema = HexColor(tema.get("cor", "#1B4F8A"))

        # marca d'água diagonal (tinta clara da cor do tema), atrás de todo o conteúdo
        marca_dagua = tema.get("marca_dagua")
        if marca_dagua:
            r, g, b = cor_tema.red, cor_tema.green, cor_tema.blue
            tinta = colors.Color(1 - (1 - r) * 0.12, 1 - (1 - g) * 0.12, 1 - (1 - b) * 0.12)
            canvas.saveState()
            canvas.setFillColor(tinta)
            canvas.setFont("Helvetica-Bold", 40)
            for wx, wy in ((25, 120), (35, 215)):
                canvas.saveState()
                canvas.translate(wx * mm, altura_pagina - wy * mm)
                canvas.rotate(35)
                canvas.drawString(0, 0, marca_dagua)
                canvas.restoreState()
            canvas.restoreState()

        # faixa de marca no topo: logo em caixa branca + empresa + badge de parcela
        faixa_h = 10.0
        y_topo = y_()
        canvas.setFillColor(cor_tema)
        canvas.rect(x_(0), y_topo - faixa_h * mm, _LARGURA * mm, faixa_h * mm, stroke=0, fill=1)
        logo_texto = tema.get("logo_texto")
        empresa_x = 3.0
        if logo_texto:
            canvas.setFillColor(white)
            canvas.roundRect(
                x_(2), y_topo - 8.2 * mm, 24 * mm, 6.4 * mm, 1.0 * mm, stroke=0, fill=1
            )
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
                cor=white,
            )
        if tema.get("parcela_texto"):
            texto(
                0,
                y_topo - 6.6 * mm,
                tema["parcela_texto"],
                fonte="Helvetica-Bold",
                tam=11,
                cor=white,
                dir_x=x_(_LARGURA - 2),
            )
        cur.avanca(faixa_h + 2.0)

        # rodapé: contatos centralizados na cor do tema + barra full-bleed na base
        if tema.get("rodape"):
            texto(0, 7.5 * mm, tema["rodape"], tam=7, cor=cor_tema, centro_x=x_(_LARGURA / 2))
        canvas.setFillColor(cor_tema)
        canvas.rect(0, 0, 210 * mm, 3.0 * mm, stroke=0, fill=1)

    # larguras/valores das linhas de 6 colunas (reutilizados no recibo e na ficha)
    c6 = [30.0, 40.0, 20.0, 16.0, 34.0, 50.0]
    x6 = [0.0, 30.0, 70.0, 90.0, 106.0, 140.0]
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

    def recibo_moderno():
        # ================= Recibo do Pagador (modelo moderno) =================
        rotulo_dir("Recibo do Pagador", italico=True)
        cabecalho_moderno(info.linha_digitavel)
        cur.avanca(1.5)

        chip_h = 32 * _PT
        chip_w = (_LARGURA - 2 * 3.0) / 3
        chips = [
            ("Vencimento", info.vencimento),
            ("Valor do Documento", info.valor_documento),
            ("Nosso Número", info.nosso_numero),
        ]
        y_topo = y_()
        for i, (rot_c, val_c) in enumerate(chips):
            cx = i * (chip_w + 3.0)
            canvas.setFillColor(destaque_bg)
            canvas.roundRect(
                x_(cx), y_topo - chip_h * mm, chip_w * mm, chip_h * mm, 1.0 * mm, stroke=0, fill=1
            )
            canvas.setStrokeColor(borda)
            canvas.setLineWidth(0.5)
            canvas.roundRect(
                x_(cx), y_topo - chip_h * mm, chip_w * mm, chip_h * mm, 1.0 * mm, stroke=1, fill=0
            )
            texto(x_(cx) + 2.2 * mm, y_topo - 3.6 * mm, rot_c.upper(), tam=6, cor=rotulo)
            texto(
                x_(cx) + 2.2 * mm,
                y_topo - (chip_h - 3.2) * mm,
                val_c,
                fonte="Helvetica-Bold",
                tam=12,
            )
        cur.avanca(chip_h + 2.0)

        celula(
            0,
            142,
            12.0,
            "Beneficiário",
            benef_2li,
            negrito=True,
            linha2=info.beneficiario_endereco,
        )
        celula(
            142, 48, 12.0, "Valor do Documento", info.valor_documento, negrito=True, destaque=True
        )
        cur.avanca(12.0)

        for (rot_c, val_c), cx, cw in zip(r2, x6, c6, strict=True):
            celula(cx, cw, 7.0, rot_c, val_c)
        cur.avanca(7.0)

        for (rot_c, val_c), cx, cw in zip(r3, x6, c6, strict=True):
            celula(cx, cw, 7.0, rot_c, val_c)
        cur.avanca(7.0)

        # totalizadores horizontais (5 colunas)
        lados = [
            "(-) Desconto / Abatimento",
            "(-) Outras deduções",
            "(+) Mora / Multa",
            "(+) Outros Acréscimos",
            "(=) Valor cobrado",
        ]
        w5 = _LARGURA / 5
        for i, rot_c in enumerate(lados):
            celula(i * w5, w5, 6.5, rot_c, "")
        cur.avanca(6.5)

        celula(0, 190, 12.0, "Sacado", sacado_li, negrito=True, linha2=info.sacado_endereco)
        cur.avanca(12.0)
        rotulo_dir("Autenticação mecânica - Recibo do Pagador")

    def recibo_classico():
        # ================= Recibo do Sacado (modelo clássico) =================
        cabecalho_classico("Recibo do Sacado", linha_digitavel=False)
        rotulo_dir("AUTENTICAÇÃO MECÂNICA")
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
        cur.avanca(h)
        celula(0, 76, h, "Sacado", sacado_li, negrito=True)
        celula(76, 38, h, "Nosso Número", info.nosso_numero, alinhar_dir=True)
        celula(114, 38, h, "Nº do documento", info.doc_numero, alinhar_dir=True)
        celula(152, 38, h, "Data Documento", info.doc_data, alinhar_dir=True)
        cur.avanca(h)
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
        cur.avanca(h)

    demonstrativo = info.demonstrativo

    def bloco_demonstrativo():
        linhas = demonstrativo.splitlines() or [demonstrativo]
        h_dem = max(10.0, 5.0 + 3.6 * len(linhas))
        y_topo = y_()
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(borda)
        canvas.rect(x_(0), y_topo - h_dem * mm, _LARGURA * mm, h_dem * mm, stroke=1, fill=0)
        texto(x_(1.2), y_topo - 3.0 * mm, rot_fmt("Demonstrativo"), tam=5.8, cor=rotulo)
        for i, ln in enumerate(linhas):
            texto(x_(1.2), y_topo - (6.5 + 3.6 * i) * mm, ln, fonte="Courier", tam=8)
        cur.avanca(h_dem)

    def corte():
        # ================= corte =================
        cur.avanca(3.5)
        canvas.setStrokeColor(HexColor(_CINZA_ROTULO))
        canvas.setLineWidth(0.4)
        canvas.setDash(2, 2)
        canvas.line(x_(0), y_(), x_(_LARGURA), y_())
        canvas.setDash()
        if moderno:
            texto(0, y_() - 2.4 * mm, "Corte aqui", tam=5.5, cor=rotulo, dir_x=x_(_LARGURA))
        cur.avanca(4.0)

    # ================= Ficha de Compensação =================
    def ficha_moderna():
        cabecalho_moderno(info.linha_digitavel)

        celula(0, 142, 7.5, "Local de pagamento", info.local_pagamento, negrito=True)
        celula(142, 48, 7.5, "Vencimento", info.vencimento, negrito=True, destaque=True)
        cur.avanca(7.5)

        celula(
            0,
            142,
            12.0,
            "Beneficiário",
            benef_2li,
            negrito=True,
            linha2=info.beneficiario_endereco,
        )
        celula(
            142, 48, 12.0, "Valor do Documento", info.valor_documento, negrito=True, destaque=True
        )
        cur.avanca(12.0)

        for (rot_c, val_c), cx, cw in zip(r2, x6, c6, strict=True):
            celula(cx, cw, 7.0, rot_c, val_c)
        cur.avanca(7.0)
        for (rot_c, val_c), cx, cw in zip(r3, x6, c6, strict=True):
            celula(cx, cw, 7.0, rot_c, val_c)
        cur.avanca(7.0)

        # bloco instruções [57% | 18% PIX | 25% totalizadores empilhados]
        n_tot = 6 if tem_pix else 5
        h_instr = _TOT_H * n_tot
        w_instr = _LARGURA * (0.57 if tem_pix else 0.75)
        w_pix = _LARGURA * 0.18 if tem_pix else 0.0
        w_tot = _LARGURA - w_instr - w_pix
        y_topo = y_()
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(borda)
        canvas.rect(x_(0), y_topo - h_instr * mm, w_instr * mm, h_instr * mm, stroke=1, fill=0)
        texto(
            x_(1.2),
            y_topo - 2.8 * mm,
            "Instruções (Texto de responsabilidade do beneficiário)",
            tam=5.8,
            cor=rotulo,
        )
        for i, ln in enumerate(info.instrucoes[:7]):
            texto(x_(1.2), y_topo - (7.0 + (10 * _PT) * i) * mm, ln, tam=8.5)
        if tem_pix:
            px = w_instr
            canvas.setStrokeColor(borda)
            canvas.rect(x_(px), y_topo - h_instr * mm, w_pix * mm, h_instr * mm, stroke=1, fill=0)
            cab_h = 10 * _PT
            canvas.setFillColor(pix_cor)
            canvas.rect(x_(px), y_topo - cab_h * mm, w_pix * mm, cab_h * mm, stroke=0, fill=1)
            texto(
                0,
                y_topo - 2.6 * mm,
                "PAGUE COM PIX",
                fonte="Helvetica-Bold",
                tam=5.5,
                cor=white,
                centro_x=x_(px) + w_pix / 2 * mm,
            )
            lado_qr = min(h_instr - cab_h - 3.0, w_pix - 4.0)
            _desenha_qr(
                canvas,
                mm,
                qrcode_matrix,
                x_(px) + (w_pix - lado_qr) / 2 * mm,
                y_topo - (cab_h + 1.5 + lado_qr) * mm,
                lado_qr,
                black,
            )
        lados = [
            "(-) Desconto / Abatimento",
            "(-) Outras deduções",
            "(+) Mora / Multa",
            "(+) Outros Acréscimos",
            "(=) Valor cobrado",
        ]
        h_lado = h_instr / len(lados)
        x_tot = w_instr + w_pix
        for i, rot_c in enumerate(lados):
            canvas.setStrokeColor(borda)
            canvas.rect(
                x_(x_tot), y_topo - (i + 1) * h_lado * mm, w_tot * mm, h_lado * mm, stroke=1, fill=0
            )
            texto(
                x_(x_tot) + 1.2 * mm, y_topo - (i * h_lado + 2.8) * mm, rot_c, tam=5.8, cor=rotulo
            )
        cur.avanca(h_instr)

        celula(0, 190, 12.0, "Sacado", sacado_li, negrito=True, linha2=info.sacado_endereco)
        cur.avanca(12.0)
        celula(0, 142, 6.5, "Sacador/Avalista", info.sacador_avalista or "")
        celula(142, 48, 6.5, "Cód. baixa", info.codigo_baixa)
        cur.avanca(6.5)

        rotulo_dir("Autenticação mecânica - Ficha de Compensação")
        bar_w, bar_h = _LARGURA * _BARCODE_FRAC, _BARCODE_H
        _desenha_barcode(canvas, mm, info.codigo_barras, x_(0), y_(bar_h), bar_w, bar_h, black)

    def ficha_classica():
        cabecalho_classico(info.linha_digitavel, linha_digitavel=True)
        h = 8.0
        celula(0, 142, h, "Local de pagamento", info.local_pagamento)
        celula(142, 48, h, "Vencimento", info.vencimento, negrito=True, tam=10, alinhar_dir=True)
        cur.avanca(h)
        celula(0, 142, h, "Cedente", benef_2li, negrito=True)
        celula(
            142,
            48,
            h,
            "Agência/Código cedente",
            info.agencia_codigo,
            alinhar_dir=True,
        )
        cur.avanca(h)
        celula(0, 32, h, "Data do documento", info.doc_data)
        celula(32, 40, h, "N. do documento", info.doc_numero)
        celula(72, 22, h, "Espécie doc", info.doc_especie)
        celula(94, 18, h, "Aceite", info.doc_aceite)
        celula(112, 34, h, "Data processamento", info.doc_processamento)
        celula(146, 44, h, "Nosso número", info.nosso_numero, negrito=True, alinhar_dir=True)
        cur.avanca(h)
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
        cur.avanca(h)

        h_instr = 30.0
        y_topo = y_()
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(borda)
        canvas.rect(x_(0), y_topo - h_instr * mm, 142 * mm, h_instr * mm, stroke=1, fill=0)
        texto(
            x_(1.2),
            y_topo - 3.0 * mm,
            "INSTRUÇÕES (TEXTO DE RESPONSABILIDADE DO BENEFICIÁRIO)",
            tam=5.5,
            cor=rotulo,
        )
        for i, ln in enumerate(info.instrucoes):
            texto(x_(1.2), y_topo - (7.0 + 4.0 * i) * mm, ln, tam=8.5)
        lados = [
            "(-) DESCONTO / ABATIMENTOS",
            "(-) OUTRAS DEDUÇÕES",
            "(+) MORA / MULTA",
            "(+) OUTROS ACRÉSCIMOS",
            "(=) VALOR COBRADO",
        ]
        h_lado = h_instr / len(lados)
        for i, rot_c in enumerate(lados):
            canvas.setStrokeColor(borda)
            canvas.rect(
                x_(142), y_topo - (i + 1) * h_lado * mm, 48 * mm, h_lado * mm, stroke=1, fill=0
            )
            texto(x_(143.2), y_topo - (i * h_lado + 2.8) * mm, rot_c, tam=5.5, cor=rotulo)
        cur.avanca(h_instr)

        h_sac = 26.0
        y_topo = y_()
        canvas.setStrokeColor(borda)
        canvas.rect(x_(0), y_topo - h_sac * mm, 142 * mm, h_sac * mm, stroke=1, fill=0)
        texto(x_(1.2), y_topo - 3.0 * mm, "SACADO", tam=5.5, cor=rotulo)
        texto(x_(1.2), y_topo - 7.0 * mm, sacado_li, fonte="Helvetica-Bold", tam=8.5)
        texto(x_(1.2), y_topo - 11.0 * mm, info.sacado_endereco, tam=8.5)
        texto(
            x_(1.2),
            y_topo - (h_sac - 2.5) * mm,
            f"SACADOR / AVALISTA: {info.sacador_avalista or '—'}    "
            f"CÓDIGO DE BAIXA: {info.codigo_baixa}",
            tam=6,
            cor=rotulo,
        )
        canvas.setStrokeColor(borda)
        canvas.rect(x_(142), y_topo - h_sac * mm, 48 * mm, h_sac * mm, stroke=1, fill=0)
        if tem_pix:
            texto(
                0,
                y_topo - 3.4 * mm,
                "PAGUE COM PIX",
                fonte="Helvetica-Bold",
                tam=6,
                cor=pix_cor,
                dir_x=x_(142) + 46 * mm,
            )
            lado_qr = 20.0
            _desenha_qr(
                canvas,
                mm,
                qrcode_matrix,
                x_(142) + (48 - lado_qr) / 2 * mm,
                y_topo - 25 * mm,
                lado_qr,
                black,
            )
        cur.avanca(h_sac)

        cur.avanca(3.0)
        bar_w, bar_h = 103.0, 13.0
        y_base = y_(bar_h)
        _desenha_barcode(canvas, mm, info.codigo_barras, x_(0), y_base, bar_w, bar_h, black)
        texto(
            0,
            y_base + 1 * mm,
            "AUTENTICAÇÃO MECÂNICA · FICHA DE COMPENSAÇÃO",
            tam=6,
            cor=rotulo,
            dir_x=x_(_LARGURA),
        )

    # ---- orquestração: mesma ordem de desenho da versão procedural original ----
    if tem_tema:
        desenha_tema()
    if moderno:
        recibo_moderno()
    else:
        recibo_classico()
    if demonstrativo:
        bloco_demonstrativo()
    corte()
    if moderno:
        ficha_moderna()
    else:
        ficha_classica()

    canvas.showPage()
    canvas.save()
    return buf.getvalue()


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
        info = _informacoes(d)
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
