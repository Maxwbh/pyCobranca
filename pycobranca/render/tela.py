"""A :class:`Tela` — canvas + cursor + coordenadas do boleto.

Encapsula o que antes eram *closures* dentro de ``render_boleto_pdf``
(``x_``, ``y_``, ``texto``, ``rot_fmt``, ``celula``) junto do estado que elas
capturavam: o canvas ReportLab, o cursor vertical, a paleta do modelo e o logo.

É isso que permite que os blocos de layout (recibo, ficha, tema…) sejam funções
de módulo normais — cada uma recebe a ``Tela`` e desenha, avançando o cursor.
"""

from __future__ import annotations

from .comum import (
    _CINZA_BORDA,
    _CINZA_ROTULO,
    _COR_PIX,
    _DESTAQUE_BG,
    _MARGEM,
    _canvas_e_libs,
    _carrega_logo,
    _Cursor,
    _faz_texto,
)

__all__ = ["Tela"]


class Tela:
    """Superfície de desenho do boleto (página A4 com margens de ``_MARGEM`` mm).

    Args:
        canvas: ``reportlab.pdfgen.canvas.Canvas`` de destino.
        moderno: ``True`` para o modelo moderno (paleta cinza/teal), ``False``
            para o clássico (bordas pretas).
        cor_marca: cor do banco (usada no cabeçalho clássico).
        logo: fonte do logo opt-in (bytes, caminho, ``ImageReader`` ou ``None``).
    """

    def __init__(self, canvas, *, moderno: bool, cor_marca: str = "#003a70", logo=None):
        colors, A4, mm, _Canvas = _canvas_e_libs()
        self.colors = colors
        self.HexColor = colors.HexColor
        self.black = colors.black
        self.white = colors.white
        self.canvas = canvas
        self.mm = mm
        _, self.altura_pagina = A4

        self.cur = _Cursor()
        self.moderno = moderno
        self.logo_reader = _carrega_logo(logo)
        self.marca = self.HexColor(cor_marca)
        self.borda = self.HexColor(_CINZA_BORDA) if moderno else self.black
        self.rotulo = self.HexColor(_CINZA_ROTULO) if moderno else self.HexColor("#5b6672")
        self.destaque_bg = self.HexColor(_DESTAQUE_BG)
        self.pix_cor = self.HexColor(_COR_PIX)

    # ---- coordenadas (mm a partir da margem / do topo da área útil) ----
    def x_(self, v):
        return (_MARGEM + v) * self.mm

    def y_(self, h=0.0):
        return self.altura_pagina - (_MARGEM + self.cur.y + h) * self.mm

    def avanca(self, mm_: float) -> None:
        self.cur.avanca(mm_)

    # ---- texto ----
    def texto(
        self, x, y_abs, s, *, fonte="Helvetica", tam=8.5, cor=None, dir_x=None, centro_x=None
    ):
        _faz_texto(
            self.canvas,
            x,
            y_abs,
            s,
            fonte=fonte,
            tam=tam,
            cor=self.black if cor is None else cor,
            dir_x=dir_x,
            centro_x=centro_x,
        )

    def rot_fmt(self, rot):
        """Rótulos vão em CAIXA ALTA no modelo clássico e como escritos no moderno."""
        return rot if self.moderno else rot.upper()

    # ---- célula rotulada (o tijolo do layout) ----
    def celula(
        self,
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
        canvas, mm, x_, texto = self.canvas, self.mm, self.x_, self.texto
        y_topo = self.y_() - dy * mm
        if destaque and self.moderno:
            canvas.setFillColor(self.destaque_bg)
            canvas.rect(x_(x), y_topo - h * mm, w * mm, h * mm, stroke=0, fill=1)
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(self.borda)
        canvas.rect(x_(x), y_topo - h * mm, w * mm, h * mm, stroke=1, fill=0)
        texto(x_(x) + 1.2 * mm, y_topo - 2.8 * mm, self.rot_fmt(rot), tam=5.8, cor=self.rotulo)
        fonte = "Helvetica-Bold" if negrito else "Helvetica"
        y_val = y_topo - (6.4 if linha2 else h - 1.8) * mm
        if alinhar_dir:
            texto(0, y_val, val, fonte=fonte, tam=tam, dir_x=x_(x) + (w - 1.5) * mm)
        else:
            texto(x_(x) + 1.2 * mm, y_val, val, fonte=fonte, tam=tam)
        if linha2:
            texto(x_(x) + 1.2 * mm, y_topo - (h - 2.0) * mm, linha2, tam=8)
