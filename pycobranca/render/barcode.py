"""Gerador de código de barras Interleaved 2 of 5 (ITF) em SVG.

O padrão de boleto brasileiro usa Interleaved 2 of 5 para as 44 posições do código
de barras. A geração é em **Python puro**, sem dependências, e produz um `<svg>`
pronto para ser embutido em qualquer HTML.
"""

from __future__ import annotations

__all__ = ["interleaved_2of5_svg", "sequencia_i2of5", "InvalidBarcodeError"]

# Padrões de barras/espaços por dígito: N = estreito, W = largo (2 largos por dígito).
_PADROES = {
    "0": "NNWWN",
    "1": "WNNNW",
    "2": "NWNNW",
    "3": "WWNNN",
    "4": "NNWNW",
    "5": "WNWNN",
    "6": "NWWNN",
    "7": "NNNWW",
    "8": "WNNWN",
    "9": "NWNWN",
}


class InvalidBarcodeError(ValueError):
    """Código informado não é válido para Interleaved 2 of 5."""


def sequencia_i2of5(codigo: str) -> list[tuple[bool, int]]:
    """Retorna a sequência de (é_barra, unidades) para o código.

    Interleaved 2 of 5 codifica dígitos aos pares: o dígito ímpar vira barras e o
    par vira espaços. Cada elemento tem largura 1 (estreito) ou 3 (largo) unidades.
    Reusada pelos backends SVG/HTML e ReportLab.
    """
    if not codigo.isdigit():
        raise InvalidBarcodeError(f"código deve conter apenas dígitos: {codigo!r}")
    if len(codigo) % 2:
        codigo = "0" + codigo  # dígitos são codificados aos pares

    seq: list[tuple[bool, int]] = []
    # Guarda inicial: barra-estreita, espaço-estreito, barra-estreita, espaço-estreito.
    seq += [(True, 1), (False, 1), (True, 1), (False, 1)]
    for i in range(0, len(codigo), 2):
        barras = _PADROES[codigo[i]]
        espacos = _PADROES[codigo[i + 1]]
        for j in range(5):
            seq.append((True, 3 if barras[j] == "W" else 1))
            seq.append((False, 3 if espacos[j] == "W" else 1))
    # Guarda final: barra-larga, espaço-estreito, barra-estreita.
    seq += [(True, 3), (False, 1), (True, 1)]
    return seq


def interleaved_2of5_svg(
    codigo: str, *, altura: float = 50.0, unidade: float = 1.5, cor: str = "#101418"
) -> str:
    """Gera o SVG do código de barras ITF para ``codigo``.

    Args:
        codigo: Dígitos do código (ex.: as 44 posições do boleto).
        altura: Altura das barras, em unidades do viewBox.
        unidade: Largura da barra estreita; a larga é 3x.
        cor: Cor das barras.

    Returns:
        String SVG (``<svg …>…</svg>``) com ``viewBox`` proporcional ao conteúdo.
    """
    x = 0.0
    rects: list[str] = []
    for e_barra, unidades in sequencia_i2of5(codigo):
        largura = unidades * unidade
        if e_barra:
            rects.append(f'<rect x="{x:.2f}" y="0" width="{largura:.2f}" height="{altura:.2f}"/>')
        x += largura
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x:.2f} {altura:.2f}" '
        f'preserveAspectRatio="none" role="img" aria-label="Código de barras">'
        f'<g fill="{cor}">{"".join(rects)}</g></svg>'
    )
