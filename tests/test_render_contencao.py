"""Texto que não cabe na célula não pode vazar para fora do boleto.

Razão social longa é comum no Brasil, e o motor desenhava o texto inteiro a
partir da coordenada inicial: o nome atravessava a borda da célula e saía da
página. O PDF continuava válido em bytes — nada levantava exceção —, e o erro
só aparecia no papel.

O corte acompanha o que o CNAB já faz: os registros gravam o nome do sacado
truncado no tamanho do campo (30 posições no Itaú 400, por exemplo).
"""

from __future__ import annotations

import pytest

from pycobranca.render.comum import _canvas_e_libs
from pycobranca.render.tela import Tela

LONGO = (
    "COMPANHIA BRASILEIRA DE DISTRIBUICAO E LOGISTICA INTEGRADA DE MATERIAIS "
    "DE CONSTRUCAO LTDA ME EPP SOCIEDADE ANONIMA DE CAPITAL FECHADO"
)


@pytest.fixture
def tela():
    _, _, _, Canvas = _canvas_e_libs()
    import io

    return Tela(Canvas(io.BytesIO()), moderno=True)


def _largura(tela, s, fonte="Helvetica", tam=8.5):
    return tela.canvas.stringWidth(s, fonte, tam)


def test_texto_que_cabe_sai_intacto(tela) -> None:
    curto = "EMPRESA EXEMPLO LTDA"
    assert tela.cabe(curto, _largura(tela, curto) + 10) == curto


def test_texto_longo_e_cortado_dentro_da_largura(tela) -> None:
    largura = 120.0
    saida = tela.cabe(LONGO, largura)
    assert saida != LONGO
    assert _largura(tela, saida) <= largura


def test_corte_e_sinalizado_com_reticencias(tela) -> None:
    assert tela.cabe(LONGO, 120.0).endswith("…")


def test_largura_menor_que_as_reticencias_devolve_vazio(tela) -> None:
    """Célula estreita demais: melhor nada do que um caractere solto."""
    assert tela.cabe(LONGO, 0.5) == ""


@pytest.mark.parametrize("valor", ["", None])
def test_vazio_passa_sem_alteracao(tela, valor) -> None:
    assert tela.cabe(valor, 100.0) == valor


@pytest.mark.parametrize("largura", [20.0, 60.0, 150.0, 400.0])
def test_nunca_ultrapassa_a_largura_pedida(tela, largura) -> None:
    assert _largura(tela, tela.cabe(LONGO, largura)) <= largura


def test_linha_digitavel_nao_encosta_na_regua_do_cabecalho() -> None:
    """A régua vertical do cabeçalho clássico não pode cortar o primeiro dígito.

    A linha digitável é alinhada à direita, então a ponta esquerda cai onde a
    largura do texto levar. Em ``Courier-Bold 9.5`` ela media 307,8 pt para um
    vão de 306,1 — a régua de ``x_(82)`` passava por cima do "3", que era lido
    como "B". Num número que a pessoa digita para pagar, isso é erro de
    pagamento, não detalhe estético.
    """
    import io

    from pycobranca.render.comum import _MARGEM, _canvas_e_libs
    from pycobranca.render.modelos.boleto_classico import _LARGURA

    _, _, mm, Canvas = _canvas_e_libs()
    canvas = Canvas(io.BytesIO())

    # 47 posições com os separadores — o formato mais largo que o campo recebe.
    linha = "34191.09123 34567.800056 71234.570001 4 15700000127950"
    regua = (_MARGEM + 82) * mm
    direita = (_MARGEM + _LARGURA) * mm
    inicio = direita - canvas.stringWidth(linha, "Courier-Bold", 9.0)

    assert inicio > regua, f"linha digitável invade a régua ({inicio:.1f} <= {regua:.1f})"


def test_nome_longo_encolhe_em_vez_de_ser_cortado(tela) -> None:
    """Título curto e conhecido: reduzir o corpo preserva a leitura; cortar, não."""
    nome = "Caixa Econômica Federal"
    largura = _largura(tela, nome, "Helvetica-Bold", 12) * 0.8
    saida, corpo = tela.cabe_corpo(nome, largura, tam=12)
    assert saida == nome
    assert corpo < 12
    assert _largura(tela, saida, "Helvetica-Bold", corpo) <= largura


def test_nome_absurdo_cai_no_piso_e_ai_sim_e_cortado(tela) -> None:
    saida, corpo = tela.cabe_corpo(LONGO, 60.0, tam=12, minimo=8)
    assert corpo == 8
    assert saida.endswith("…")
    assert _largura(tela, saida, "Helvetica-Bold", 8) <= 60.0


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_nenhum_nome_de_banco_atravessa_a_regua_do_cabecalho(modelo) -> None:
    """ "Caixa Econômica Federal" media 145 pt para um vão de 115 e batia no DV.

    O nome é desenhado da margem para a direita, então quem tem nome comprido
    invade a régua vertical e escreve por cima do código-DV — os dois ficam
    ilegíveis. Percorre os 18 bancos: o teste é sobre o registro, não sobre um
    nome escolhido a dedo.
    """
    import io

    from pycobranca.bancos import REGISTRO
    from pycobranca.render.comum import _canvas_e_libs
    from pycobranca.render.tela import Tela

    _, _, mm, Canvas = _canvas_e_libs()
    espia = _EspiaTexto(Canvas(io.BytesIO()))
    vao, tam = ((42 - 1.5) * mm, 12) if modelo == "moderno" else ((62 - 10 - 1.5) * mm, 10)
    tela = Tela(espia, moderno=modelo == "moderno")

    for Banco in REGISTRO.values():
        saida, corpo = tela.cabe_corpo(Banco.nome, vao, tam=tam)
        largura = espia.stringWidth(saida, "Helvetica-Bold", corpo)
        assert largura <= vao, f"{Banco.nome!r} mede {largura:.1f} pt num vão de {vao:.1f}"


class _EspiaTexto:
    """Canvas que registra ``(texto, fonte, corpo)`` de cada escrita no papel."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.escritos: list[tuple[str, str, float]] = []
        self._fonte, self._tam = "Helvetica", 0.0

    def __getattr__(self, nome):
        return getattr(self.canvas, nome)

    def setFont(self, fonte, tam, *args, **kwargs):  # noqa: N802 (API do ReportLab)
        self._fonte, self._tam = fonte, tam
        return self.canvas.setFont(fonte, tam, *args, **kwargs)

    def drawString(self, x, y, s):
        self.escritos.append((s, self._fonte, self._tam))
        return self.canvas.drawString(x, y, s)

    def drawRightString(self, x, y, s):
        self.escritos.append((s, self._fonte, self._tam))
        return self.canvas.drawRightString(x, y, s)

    def drawCentredString(self, x, y, s):
        self.escritos.append((s, self._fonte, self._tam))
        return self.canvas.drawCentredString(x, y, s)


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_o_cabecalho_desenhado_de_fato_usa_o_nome_contido(modelo) -> None:
    """Ponta a ponta: o modelo tem de chamar a contenção, não só tê-la disponível.

    Sem isto, ``cabe_corpo`` poderia estar correta e ninguém usá-la — foi
    exatamente o estado anterior do cabeçalho moderno.
    """
    import io
    from datetime import date

    from pycobranca.bancos import Bancos
    from pycobranca.render import desenha_boleto
    from pycobranca.render.comum import _canvas_e_libs
    from pycobranca.render.tela import Tela

    _, _, mm, Canvas = _canvas_e_libs()
    Banco = Bancos.find("104")  # Caixa Econômica Federal: o nome mais comprido
    boleto = Banco(
        valor="127.50",
        cedente="EMPRESA EXEMPLO LTDA",
        cedente_documento="11.222.333/0001-81",
        agencia="1234",
        conta="12345",
        carteira="14",
        nosso_numero="123456789012345",
        convenio="123456",
        data_vencimento=date(2026, 8, 15),
        sacado="CLIENTE FINAL",
        sacado_documento="529.982.247-25",
    )
    espia = _EspiaTexto(Canvas(io.BytesIO()))
    desenha_boleto(Tela(espia, moderno=modelo == "moderno"), boleto.contexto_render(), modelo)

    vao = (42 - 1.5) * mm if modelo == "moderno" else (62 - 10 - 1.5) * mm
    nomes = [(s, f, t) for s, f, t in espia.escritos if s.startswith("Caixa")]
    assert nomes, "o nome do banco não foi desenhado"
    for s, fonte, tam in nomes:
        largura = espia.stringWidth(s, fonte, tam)
        assert largura <= vao, f"{s!r} a {tam} pt mede {largura:.1f} num vão de {vao:.1f}"


def test_boleto_com_nome_extremo_nao_estoura_a_pagina() -> None:
    """Ponta a ponta: o texto desenhado tem de caber na moldura da célula."""
    from datetime import date

    from pycobranca.bancos import Bancos
    from pycobranca.render import render_boleto_pdf

    Banco = Bancos.find("341")
    boleto = Banco(
        valor="127.50",
        cedente=LONGO,
        cedente_documento="11.222.333/0001-81",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado=LONGO,
        sacado_documento="529.982.247-25",
    )
    for modelo in ("moderno", "classico"):
        pdf = render_boleto_pdf(boleto.contexto_render(), modelo=modelo)
        assert pdf.startswith(b"%PDF")
