"""Primitivas de desenho compartilhadas pelo boleto e pelo carnê (ReportLab).

Aqui ficam as peças que **não conhecem o layout**: constantes de página/paleta,
o cursor vertical e as funções elementares de desenho (código de barras, QR,
logo e texto). Os módulos :mod:`pycobranca.render.boleto` e
:mod:`pycobranca.render.carne` montam o layout em cima destas primitivas.

O ``reportlab`` é importado sob demanda (só ao gerar o PDF), mantendo o import
do pacote leve; ele é dependência padrão, então já vem instalado.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from ..exceptions import DependenciaAusente
from .barcode import sequencia_i2of5

__all__ = [
    "_PT",
    "_LARGURA",
    "_MARGEM",
    "_CINZA_BORDA",
    "_CINZA_FORTE",
    "_CINZA_ROTULO",
    "_DESTAQUE_BG",
    "_COR_PIX",
    "_TOT_H",
    "_BARCODE_H",
    "_BARCODE_FRAC",
    "_Cursor",
    "_canvas_e_libs",
    "_desenha_barcode",
    "_desenha_qr",
    "_carrega_logo",
    "_desenha_logo",
    "_faz_texto",
]


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
        raise DependenciaAusente(
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
