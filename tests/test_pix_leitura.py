"""O QR do boleto é **lido de volta** — não basta a matriz estar certa.

Os demais testes de PIX conferem o payload e a matriz de módulos. Nada disso
prova que o QR **impresso** é legível: entre a matriz e o papel há a
rasterização, onde módulos caem em fração de pixel, e há o que estiver desenhado
em volta.

O que este arquivo mede, e nenhum outro media: que o QR **impresso** decodifica
de volta no payload exato. A leitura degrada com a resolução — a 150 dpi dois
dos sete payloads já não são lidos, e a partir de 200 dpi todos são. É por isso
que a referência aqui é 300 dpi, o padrão de impressão de boleto.

Requer ``opencv`` (só para decodificar; não é dependência do pacote).
"""

from __future__ import annotations

import pytest

pytest.importorskip("cv2")
pytest.importorskip("pymupdf")
pytest.importorskip("reportlab")

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pymupdf  # noqa: E402
from exemplos_boletos import EXEMPLOS  # noqa: E402

from pycobranca.render import render_boleto_pdf  # noqa: E402

#: Resolução de referência. 300 dpi é o padrão de impressão de boleto; abaixo de
#: 200 a rasterização começa a comer os módulos, e aí a leitura depende do
#: payload — ver ``test_leitura_degrada_abaixo_de_200_dpi``.
DPI = 300

BANCOS_COM_PIX = sorted(n for n in EXEMPLOS if EXEMPLOS[n]["boleto"]().suporta_pix)
MODELOS = ("moderno", "classico")


def _boleto_com_pix(nome: str):
    boleto = EXEMPLOS[nome]["boleto"]()
    boleto.pix_chave = "cobranca@empresaexemplo.com.br"
    boleto.cedente_cidade = "SAO PAULO"
    return boleto


def _le_qr(pdf: bytes, dpi: int = DPI) -> str:
    """Rasteriza a primeira página e devolve o conteúdo do QR (``""`` se ilegível)."""
    documento = pymupdf.open(stream=pdf, filetype="pdf")
    pixmap = documento[0].get_pixmap(dpi=dpi)
    imagem = np.frombuffer(pixmap.samples, np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
    cinza = cv2.cvtColor(imagem, cv2.COLOR_RGB2GRAY if pixmap.n == 3 else cv2.COLOR_RGBA2GRAY)
    texto, *_ = cv2.QRCodeDetector().detectAndDecode(cinza)
    return texto or ""


@pytest.mark.parametrize("modelo", MODELOS)
@pytest.mark.parametrize("nome", BANCOS_COM_PIX)
def test_qr_do_pdf_le_de_volta_o_payload(nome: str, modelo: str) -> None:
    """Fecha o ciclo: payload -> matriz -> PDF -> raster -> leitura -> payload.

    Comparar com o payload, e não só verificar que "algo" foi lido, é o que pega
    um QR que decodifica para outra coisa.
    """
    contexto = _boleto_com_pix(nome).contexto_render()
    lido = _le_qr(render_boleto_pdf(contexto, modelo=modelo))
    assert lido == contexto["pix"]["copia_cola"], f"{nome}/{modelo}: QR ilegível ou divergente"


@pytest.mark.parametrize("dpi", [200, 300, 600])
def test_leitura_se_mantem_em_toda_resolucao_de_impressao(dpi: int) -> None:
    """De 200 dpi para cima, os sete bancos leem nos dois modelos.

    Prende o piso: se uma mudança de layout encolher o QR ou aproximá-lo demais
    de uma moldura, isto acusa antes de virar boleto impresso ilegível.
    """
    for nome in BANCOS_COM_PIX:
        contexto = _boleto_com_pix(nome).contexto_render()
        for modelo in MODELOS:
            lido = _le_qr(render_boleto_pdf(contexto, modelo=modelo), dpi=dpi)
            assert lido == contexto["pix"]["copia_cola"], f"{nome}/{modelo} a {dpi} dpi"
