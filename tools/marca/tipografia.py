"""Texto em curvas: molda com HarfBuzz e devolve o `d` de um <path> SVG.

Sem isso o SVG depende de a fonte existir na máquina que renderiza — foi
exatamente o que quebrou o card anterior (o SVG pedia Segoe UI e o
rasterizador substituiu por uma serifada).
"""

from __future__ import annotations

import functools

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

MANROPE = "Manrope.ttf"
MONO = "JetBrainsMono.ttf"


@functools.cache
def _instancia(caminho: str, peso: int):
    """Instância estática da fonte variável no peso pedido (bytes + TTFont)."""
    fonte = instancer.instantiateVariableFont(TTFont(caminho), {"wght": peso})
    import io

    buf = io.BytesIO()
    fonte.save(buf)
    dados = buf.getvalue()
    return dados, TTFont(io.BytesIO(dados))


@functools.cache
def _hb_font(caminho: str, peso: int):
    dados, _ = _instancia(caminho, peso)
    face = hb.Face(dados)
    return hb.Font(face)


def medir(
    texto: str, *, tamanho: float, peso: int = 400, fonte: str = MANROPE, espacamento: float = 0.0
) -> float:
    """Largura do texto em unidades de usuário do SVG."""
    _, tt = _instancia(fonte, peso)
    upem = tt["head"].unitsPerEm
    hbf = _hb_font(fonte, peso)
    buf = hb.Buffer()
    buf.add_str(texto)
    buf.guess_segment_properties()
    hb.shape(hbf, buf)
    avanco = sum(p.x_advance for p in buf.glyph_positions)
    return avanco * tamanho / upem + espacamento * max(len(texto) - 1, 0)


def caminho(
    texto: str,
    *,
    x: float,
    y: float,
    tamanho: float,
    peso: int = 400,
    fonte: str = MANROPE,
    espacamento: float = 0.0,
    ancora: str = "start",
) -> str:
    """`d` de um <path> com o texto já posicionado (y = linha de base)."""
    _, tt = _instancia(fonte, peso)
    upem = tt["head"].unitsPerEm
    escala = tamanho / upem
    glifos = tt.getGlyphSet()
    ordem = tt.getGlyphOrder()

    if ancora != "start":
        largura = medir(texto, tamanho=tamanho, peso=peso, fonte=fonte, espacamento=espacamento)
        x -= largura if ancora == "end" else largura / 2

    hbf = _hb_font(fonte, peso)
    buf = hb.Buffer()
    buf.add_str(texto)
    buf.guess_segment_properties()
    hb.shape(hbf, buf)

    # Um <path> por bloco de texto: a transformação é assada nas coordenadas,
    # em vez de um <g transform> por glifo. Corta o arquivo pela metade.
    caneta = SVGPathPen(glifos, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    cursor_x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions, strict=True):
        nome = ordem[info.codepoint]
        tx = x + (cursor_x + pos.x_offset) * escala
        ty = y - pos.y_offset * escala
        # Fonte tem Y para cima, SVG tem Y para baixo — daí o -escala.
        glifos[nome].draw(TransformPen(caneta, (escala, 0, 0, -escala, tx, ty)))
        cursor_x += pos.x_advance + (espacamento / escala if espacamento else 0)
    d = caneta.getCommands()
    return f'<path d="{d}"/>' if d else ""


def bloco(texto: str, **kw) -> str:
    """Alias legível: devolve os <g> com os glifos já em curvas."""
    return caminho(texto, **kw)
