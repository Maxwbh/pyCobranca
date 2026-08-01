"""Blocos comuns aos dois modelos de boleto: rótulo à direita, demonstrativo e corte."""

from __future__ import annotations

from .comum import _CINZA_ROTULO, _LARGURA

__all__ = ["rotulo_dir", "bloco_demonstrativo", "corte"]


def rotulo_dir(tela, txt, *, italico=False) -> None:
    """Linha de rótulo alinhada à direita (ex.: "Autenticação mecânica")."""
    tela.texto(
        0,
        tela.y_() - 2.6 * tela.mm,
        txt,
        fonte="Helvetica-Oblique" if italico else "Helvetica",
        tam=6.5,
        cor=tela.rotulo,
        dir_x=tela.x_(_LARGURA),
    )
    tela.avanca(4.0)


def bloco_demonstrativo(tela, info) -> None:
    """Bloco livre de demonstrativo (monoespaçado), abaixo do recibo."""
    canvas, mm, x_, texto = tela.canvas, tela.mm, tela.x_, tela.texto
    linhas = info.demonstrativo.splitlines() or [info.demonstrativo]
    h_dem = max(10.0, 5.0 + 3.6 * len(linhas))
    y_topo = tela.y_()
    canvas.setLineWidth(0.5)
    canvas.setStrokeColor(tela.borda)
    canvas.rect(x_(0), y_topo - h_dem * mm, _LARGURA * mm, h_dem * mm, stroke=1, fill=0)
    texto(x_(1.2), y_topo - 3.0 * mm, tela.rot_fmt("Demonstrativo"), tam=5.8, cor=tela.rotulo)
    for i, ln in enumerate(linhas):
        texto(x_(1.2), y_topo - (6.5 + 3.6 * i) * mm, ln, fonte="Courier", tam=8)
    tela.avanca(h_dem)


def corte(tela) -> None:
    """Linha tracejada de corte entre o recibo e a ficha de compensação."""
    canvas, mm, x_ = tela.canvas, tela.mm, tela.x_
    tela.avanca(3.5)
    canvas.setStrokeColor(tela.HexColor(_CINZA_ROTULO))
    canvas.setLineWidth(0.4)
    canvas.setDash(2, 2)
    canvas.line(x_(0), tela.y_(), x_(_LARGURA), tela.y_())
    canvas.setDash()
    if tela.moderno:
        tela.texto(
            0, tela.y_() - 2.4 * mm, "Corte aqui", tam=5.5, cor=tela.rotulo, dir_x=x_(_LARGURA)
        )
    tela.avanca(4.0)
