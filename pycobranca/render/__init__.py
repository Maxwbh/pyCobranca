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

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from ..exceptions import ModeloInvalido
from .barcode import InvalidBarcodeError, interleaved_2of5_svg, sequencia_i2of5
from .comum import _canvas_e_libs
from .dados import extrai_dados
from .marcas import bancos_com_logo, logo_do_banco
from .modelos import MODELO_FATURA, modelo_boleto, render_carne_pdf
from .tela import Tela

__all__ = [
    "emite_boleto",
    "BoletoEmitido",
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


@dataclass(frozen=True)
class BoletoEmitido:
    """O boleto pronto: o PDF e os dados que acompanham a resposta.

    Existe para que o PDF e os números venham da **mesma** montagem. Buscando-os
    em separado — PDF do render, linha digitável do objeto — abre-se espaço para
    o papel dizer uma coisa e o JSON outra, sem nada avisar; e o contexto de
    render, de onde os dados saem, é formato interno que não serve de contrato.
    """

    pdf: bytes
    linha_digitavel: str
    codigo_barras: str
    nosso_numero: str
    vencimento: str
    valor_documento: str
    #: Copia-e-cola do PIX, ou ``None`` quando o boleto não tem PIX.
    pix_copia_cola: str | None = None
    #: ``True`` quando o payload veio do banco e o QR **liquida o título**;
    #: ``False`` quando foi montado da chave e é um PIX avulso, que credita mas
    #: deixa o título em aberto. ``None`` sem PIX.
    pix_vinculado: bool | None = None
    #: Os cinco campos da faixa FEBRABAN, já formatados; vazios quando não informados.
    totalizadores: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Tudo menos o PDF — pronto para virar o corpo de uma resposta JSON."""
        return {
            "linha_digitavel": self.linha_digitavel,
            "codigo_barras": self.codigo_barras,
            "nosso_numero": self.nosso_numero,
            "vencimento": self.vencimento,
            "valor_documento": self.valor_documento,
            "pix_copia_cola": self.pix_copia_cola,
            "pix_vinculado": self.pix_vinculado,
            "totalizadores": dict(self.totalizadores),
        }


def emite_boleto(
    boleto, modelo: str = "moderno", *, tema: dict[str, Any] | None = None
) -> BoletoEmitido:
    """PDF **e** dados do boleto numa chamada só.

    Monta o contexto uma vez e lê dele tanto o desenho quanto os números, de
    modo que `validar()` e a montagem do código de barras rodam uma vez — contra
    quatro quando o chamador busca os derivados de volta no objeto.

    Args:
        boleto: instância de :class:`~pycobranca.bancos.base.BancoBase`.
        modelo: ``"moderno"`` (padrão) ou ``"classico"``.
        tema: bloco opcional da faixa de marca; ver
            :func:`pycobranca.contracts.tema_de_api` para montá-lo a partir de
            um ``BoletoData``.

    Returns:
        :class:`BoletoEmitido`.
    """
    contexto = boleto.contexto_render()
    if tema:
        if not isinstance(tema, dict):
            raise ModeloInvalido(
                f"tema deve ser um dicionário, recebido {type(tema).__name__} — "
                "monte-o com pycobranca.contracts.tema_de_api()"
            )
        contexto["tema"] = tema
    pix = contexto.get("pix") or {}
    return BoletoEmitido(
        pdf=render_boleto_pdf(contexto, modelo=modelo),
        linha_digitavel=contexto["linha_digitavel"],
        codigo_barras=contexto["codigo_barras"],
        nosso_numero=contexto["nosso_numero"],
        vencimento=contexto["vencimento"],
        valor_documento=contexto["valor_documento"],
        pix_copia_cola=pix.get("copia_cola") if pix.get("habilitado") else None,
        pix_vinculado=pix.get("vinculado") if pix.get("habilitado") else None,
        totalizadores=contexto.get("totalizadores") or {},
    )


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
