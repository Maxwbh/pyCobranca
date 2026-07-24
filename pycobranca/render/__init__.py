"""Renderização de boletos — backend único: **ReportLab** (Python puro).

Decisão de projeto (ver ``docs/11-renderizacao.md``): o ReportLab é o único
backend de renderização — rápido, adequado a alto volume e sem dependências de
sistema.

- :func:`render_boleto_pdf` — boleto (modelos ``classico`` e
  ``moderno``, com Bolepix e TEMA).
- :func:`render_carne_pdf` — carnê (3 parcelas por A4).
- :func:`interleaved_2of5_svg` / :func:`sequencia_i2of5` — código de barras
  Interleaved 2 of 5 em Python puro (SVG para pré-visualizações; sequência
  para desenho vetorial no PDF).
"""

from __future__ import annotations

from .barcode import InvalidBarcodeError, interleaved_2of5_svg, sequencia_i2of5
from .marcas import bancos_com_logo, logo_do_banco
from .reportlab import render_boleto_pdf, render_carne_pdf

__all__ = [
    "render_boleto_pdf",
    "render_carne_pdf",
    "interleaved_2of5_svg",
    "sequencia_i2of5",
    "InvalidBarcodeError",
    "logo_do_banco",
    "bancos_com_logo",
]
