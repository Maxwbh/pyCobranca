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

#: Reticências usadas ao cortar texto que não cabe. Um caractere só, e presente
#: no WinAnsi das fontes base do PDF — três pontos consumiriam largura útil.
_RETICENCIAS = "…"


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

    # ---- contenção de largura ----
    def cabe(self, s, largura_pt: float, *, fonte="Helvetica", tam=8.5) -> str:
        """``s`` reduzido ao que cabe em ``largura_pt``, com reticências no corte.

        Sem isso o texto simplesmente continua desenhando: razão social longa
        atravessava a borda da célula e saía da página, num PDF válido em bytes
        e errado no papel. Cortar acompanha o que o CNAB já faz — os registros
        gravam o nome do sacado truncado no tamanho do campo.
        """
        if not s:
            return s
        largura = self.canvas.stringWidth
        if largura(s, fonte, tam) <= largura_pt:
            return s
        reticencias = largura(_RETICENCIAS, fonte, tam)
        if reticencias > largura_pt:  # célula estreita demais até para o corte
            return ""
        disponivel = largura_pt - reticencias
        corte = len(s)
        while corte > 0 and largura(s[:corte], fonte, tam) > disponivel:
            corte -= 1
        return s[:corte].rstrip() + _RETICENCIAS

    def cabe_corpo(self, s, largura_pt: float, *, fonte="Helvetica-Bold", tam=12.0, minimo=8.0):
        """``(texto, corpo)`` — o maior corpo até ``tam`` em que ``s`` cabe.

        Para um título curto e conhecido, como o nome do banco, encolher é
        melhor do que cortar: "Caixa Econômica Federal" media 145 pt para um vão
        de 115 e atravessava a régua do cabeçalho, colidindo com o código-DV.
        Abaixo de ``minimo`` a redução deixaria de ser legível e o corte assume.
        """
        if not s:
            return s, tam
        largura = self.canvas.stringWidth
        corpo = tam
        while corpo > minimo and largura(s, fonte, corpo) > largura_pt:
            corpo -= 0.25
        if largura(s, fonte, corpo) > largura_pt:
            return self.cabe(s, largura_pt, fonte=fonte, tam=corpo), corpo
        return s, corpo

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
        # 2,5 mm e não 2,8: numa célula de 7 mm o valor fica 2,4 mm abaixo do
        # rótulo, e cap(8,5 pt) + descida(5,8 pt) pede 2,58 mm. Rótulo com 'g',
        # 'p' ou 'ç' — "Espécie", "Agência/Código Beneficiário" — encostava o
        # rabo da letra no topo do valor. Subir o rótulo 0,3 mm abre a folga sem
        # mexer na altura de nenhuma célula.
        texto(x_(x) + 1.2 * mm, y_topo - 2.5 * mm, self.rot_fmt(rot), tam=5.8, cor=self.rotulo)
        fonte = "Helvetica-Bold" if negrito else "Helvetica"
        y_val = y_topo - (6.4 if linha2 else h - 1.8) * mm
        # A célula conhece a própria largura; o texto, não. É aqui que a
        # contenção precisa acontecer — o recuo de 1,2 mm existe dos dois lados.
        util = (w - 2.4) * mm
        if alinhar_dir:
            # O valor vem da direita e cresce em direção ao rótulo, então a
            # célula precisa de altura para que o número tenha linha própria —
            # é responsabilidade do modelo, e ``test_render_totalizadores``
            # cobre isso. Aqui basta não ultrapassar a moldura.
            val = self.cabe(val, (w - 2.7) * mm, fonte=fonte, tam=tam)
            texto(0, y_val, val, fonte=fonte, tam=tam, dir_x=x_(x) + (w - 1.5) * mm)
        else:
            texto(
                x_(x) + 1.2 * mm,
                y_val,
                self.cabe(val, util, fonte=fonte, tam=tam),
                fonte=fonte,
                tam=tam,
            )
        if linha2:
            texto(x_(x) + 1.2 * mm, y_topo - (h - 2.0) * mm, self.cabe(linha2, util, tam=8), tam=8)
