"""Renderização de boletos — backend único: **ReportLab** (Python puro).

Decisão de projeto (ver ``docs/11-renderizacao.md``): o ReportLab é o único
backend de renderização — rápido, adequado a alto volume e sem dependências de
sistema.

- :func:`render_boleto_pdf` — boleto (modelos ``classico`` e
  ``moderno``, com Bolepix e TEMA).
- :func:`desenha_boleto` — desenha o boleto num canvas já existente (para compor
  o boleto dentro de outro documento).
- :func:`render_carne_pdf` — carnê (3 parcelas por A4).
- :func:`render_fatura_pdf` — fatura (demonstrativo de itens + boleto).
- :func:`interleaved_2of5_svg` / :func:`sequencia_i2of5` — código de barras
  Interleaved 2 of 5 em Python puro (SVG para pré-visualizações; sequência
  para desenho vetorial no PDF).

Organização interna do pacote:

- :mod:`~pycobranca.render.comum` — constantes, paleta e primitivas de desenho.
- :mod:`~pycobranca.render.tela` — a :class:`~pycobranca.render.tela.Tela`
  (canvas + cursor + coordenadas do boleto).
- :mod:`~pycobranca.render.dados` — extração dos dados do contexto.
- :mod:`~pycobranca.render.blocos` — blocos comuns aos modelos.
- :mod:`~pycobranca.render.modelos` — catálogo dos documentos renderizáveis.

O ``reportlab`` é importado sob demanda (só ao gerar o PDF), mantendo o import
do pacote leve; ele é dependência padrão, então já vem instalado.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from .barcode import InvalidBarcodeError, interleaved_2of5_svg, sequencia_i2of5
from .comum import _canvas_e_libs
from .dados import extrai_dados
from .marcas import bancos_com_logo, logo_do_banco
from .modelos import MODELO_FATURA, modelo_boleto, render_carne_pdf
from .tela import Tela

__all__ = [
    "render_boleto_pdf",
    "render_carne_pdf",
    "render_fatura_pdf",
    "desenha_boleto",
    "interleaved_2of5_svg",
    "sequencia_i2of5",
    "InvalidBarcodeError",
    "logo_do_banco",
    "bancos_com_logo",
]


def desenha_boleto(canvas, contexto: dict[str, Any], modelo: str = "moderno") -> None:
    """Desenha o boleto (recibo + ficha) num canvas ReportLab **já existente**.

    Não chama ``showPage()`` nem ``save()`` — é o ponto de extensão para compor o
    boleto dentro de outro documento. O layout assume página A4 com margens de
    10mm (as mesmas coordenadas de :func:`render_boleto_pdf`).

    Args:
        canvas: ``reportlab.pdfgen.canvas.Canvas`` de destino (página A4) ou uma
            :class:`~pycobranca.render.tela.Tela` já montada.
        contexto: dicionário de contexto do boleto (ver :func:`render_boleto_pdf`).
        modelo: ``"moderno"`` (padrão) ou ``"classico"``.
    """
    mod = modelo_boleto(modelo)
    info = extrai_dados(contexto)
    tela = (
        canvas
        if isinstance(canvas, Tela)
        else Tela(canvas, moderno=mod.MODERNO, cor_marca=info.banco_cor, logo=info.banco_logo)
    )
    mod.desenha(tela, info, contexto)


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
    modelo_boleto(modelo)  # valida antes de abrir o canvas
    _colors, A4, _mm, Canvas = _canvas_e_libs()

    buf = BytesIO()
    canvas = Canvas(buf, pagesize=A4)
    desenha_boleto(canvas, contexto, modelo)
    canvas.showPage()
    canvas.save()
    return buf.getvalue()


def render_fatura_pdf(contexto: dict[str, Any], modelo: str = "moderno") -> bytes:
    """Gera o PDF da **fatura**: demonstrativo de itens + boleto na mesma página.

    Args:
        contexto: o mesmo contexto do boleto, acrescido de ``itens`` — lista de
            dicionários com ``descricao`` e ``valor`` (ou ``valor_unitario`` com
            ``quantidade``). Sem ``itens``, a saída é o boleto puro.
        modelo: ``"moderno"`` (padrão) ou ``"classico"`` — define a paleta e o
            layout do boleto ao pé da fatura.

    Returns:
        Bytes do PDF (uma página A4).
    """
    mod_boleto = modelo_boleto(modelo)  # valida antes de abrir o canvas
    _colors, A4, _mm, Canvas = _canvas_e_libs()

    info = extrai_dados(contexto)
    buf = BytesIO()
    canvas = Canvas(buf, pagesize=A4)
    tela = Tela(canvas, moderno=mod_boleto.MODERNO, cor_marca=info.banco_cor, logo=info.banco_logo)
    MODELO_FATURA.desenha(tela, info, contexto)
    canvas.showPage()
    canvas.save()
    return buf.getvalue()
