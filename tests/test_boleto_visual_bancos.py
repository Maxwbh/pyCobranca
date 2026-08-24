"""O boleto impresso, banco a banco: o que está no papel e onde está.

``test_boletos_todos`` já garante que cada um dos 18 bancos **gera** um PDF; o
que ele não vê é o papel. Os defeitos desta camada não levantam exceção e não
mudam um byte do que o banco lê — aparecem só na impressão:

- razão social longa atravessando a borda da célula e saindo da página;
- rótulo e valor caindo um por cima do outro quando o encargo tem sete dígitos;
- valor monetário alinhado à esquerda, ilegível em coluna de números;
- campo que simplesmente não foi impresso.

A conferência não rasteriza: um canvas espião registra cada ``drawString`` /
``drawRightString`` / ``drawCentredString`` e cada ``rect`` com posição, fonte e
corpo — que é exatamente o que o ReportLab escreve no PDF. Dali sai a caixa de
tinta de cada texto (altura de caixa alta e descida da fonte) e a moldura de
cada célula.

A tolerância é **zero**: a caixa nominal já é maior que a tinta real (medido a
2400 dpi, o rabo do "p" de "Espécie" passava a 0,03 pt do "M" de "DM" com as
caixas nominais se sobrepondo em 0,5 pt), então exigir sobreposição nula das
caixas mantém uma folga real no papel sem depender de constante arbitrária.
"""

from __future__ import annotations

import io
from decimal import Decimal
from functools import cache

import pytest
from exemplos_boletos import EXEMPLOS

pytest.importorskip("reportlab")

from pycobranca.render import desenha_boleto  # noqa: E402
from pycobranca.render.comum import _LARGURA, _MARGEM, _canvas_e_libs  # noqa: E402
from pycobranca.render.tela import Tela  # noqa: E402

MODELOS = ("moderno", "classico")
BANCOS = sorted(EXEMPLOS)
CASOS = [(nome, modelo) for nome in BANCOS for modelo in MODELOS]


def _com_pix() -> list[str]:
    """Os bancos que têm Bolepix — o layout abre uma coluna a mais para o QR."""
    return [n for n in BANCOS if EXEMPLOS[n]["boleto"]().suporta_pix]


CASOS_PIX = [(nome, modelo) for nome in _com_pix() for modelo in MODELOS]

#: caracteres que descem abaixo da linha de base nas fontes base do PDF
_DESCENDENTES = set("gjpqyçÇ,;_()[]{}/")
#: proporções da Helvetica: altura de caixa alta e descida, em frações do corpo
_CAPA, _DESCIDA = 0.72, 0.21

#: encargos largos — sete dígitos é o que cabe num boleto e o que colidia
_ENCARGOS = dict.fromkeys(
    ("desconto_abatimento", "outras_deducoes", "mora_multa", "outros_acrescimos"),
    Decimal("1234567.89"),
)

_LONGO = (
    "COMPANHIA BRASILEIRA DE DISTRIBUICAO E LOGISTICA INTEGRADA DE MATERIAIS "
    "DE CONSTRUCAO LTDA ME EPP SOCIEDADE ANONIMA DE CAPITAL FECHADO"
)


class _Espia:
    """Canvas que registra o que foi desenhado, sem atrapalhar o desenho."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.escritas: list[dict] = []
        self.molduras: list[tuple[float, float, float, float]] = []
        self._fonte, self._tam = "Helvetica", 0.0

    def __getattr__(self, nome):
        return getattr(self.canvas, nome)

    def setFont(self, fonte, tam, *args, **kwargs):  # noqa: N802 (API do ReportLab)
        self._fonte, self._tam = fonte, tam
        return self.canvas.setFont(fonte, tam, *args, **kwargs)

    def rect(self, x, y, w, h, *args, **kwargs):
        self.molduras.append((x, y, x + w, y + h))
        return self.canvas.rect(x, y, w, h, *args, **kwargs)

    def _registra(self, x, y, s, ancora):
        if not s or not s.strip():
            return
        largura = self.canvas.stringWidth(s, self._fonte, self._tam)
        x0 = x if ancora == "esq" else (x - largura if ancora == "dir" else x - largura / 2)
        descida = _DESCIDA * self._tam if set(s) & _DESCENDENTES else 0.0
        self.escritas.append(
            {
                "s": s,
                "fonte": self._fonte,
                "tam": self._tam,
                "ancora": ancora,
                "base": y,
                "x0": x0,
                "x1": x0 + largura,
                "y0": y - descida,
                "y1": y + _CAPA * self._tam,
            }
        )

    def drawString(self, x, y, s):  # noqa: N802
        self._registra(x, y, s, "esq")
        return self.canvas.drawString(x, y, s)

    def drawRightString(self, x, y, s):  # noqa: N802
        self._registra(x, y, s, "dir")
        return self.canvas.drawRightString(x, y, s)

    def drawCentredString(self, x, y, s):  # noqa: N802
        self._registra(x, y, s, "cen")
        return self.canvas.drawCentredString(x, y, s)


def _boleto(nome: str, variante: str):
    boleto = EXEMPLOS[nome]["boleto"]()
    if variante == "encargos":
        for campo, valor in _ENCARGOS.items():
            setattr(boleto, campo, valor)
    elif variante == "longos":
        boleto.cedente = _LONGO
        boleto.sacado = _LONGO
        boleto.cedente_endereco = _LONGO
        boleto.sacado_endereco = _LONGO
        # Dez linhas: a moldura não comporta todas, e o excedente não pode
        # simplesmente ser desenhado por baixo dela.
        boleto.instrucoes = [_LONGO] * 10
    elif variante == "pix":
        boleto.pix_chave = "cobranca@empresaexemplo.com.br"
        boleto.pix_txid = "PEDIDO2026000123456789012"  # 25 posições: o máximo do EMV
    return boleto


@cache
def _desenho(nome: str, modelo: str, variante: str = "simples"):
    """``(escritas, molduras, mm, contexto)`` do boleto desenhado de fato."""
    _, _, mm, Canvas = _canvas_e_libs()
    espia = _Espia(Canvas(io.BytesIO()))
    contexto = _boleto(nome, variante).contexto_render()
    desenha_boleto(Tela(espia, moderno=modelo == "moderno"), contexto, modelo)
    return espia.escritas, espia.molduras, mm, contexto


def _sobrepoem(a: dict, b: dict) -> bool:
    return (
        min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]) > 0
        and min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]) > 0
    )


def _impressos(escritas) -> list[str]:
    return [e["s"] for e in escritas]


# ---- 1. os campos estão no papel ----


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
def test_os_campos_do_titulo_estao_impressos(nome: str, modelo: str) -> None:
    """Cada campo que identifica o título aparece na página, com o valor do título."""
    escritas, _, _, ctx = _desenho(nome, modelo)
    impressos = _impressos(escritas)
    obrigatorios = {
        "linha digitável": ctx["linha_digitavel"],
        "vencimento": ctx["vencimento"],
        "valor do documento": ctx["valor_documento"],
        "nosso número": ctx["nosso_numero"],
        "agência/código": ctx["beneficiario"]["agencia_codigo"],
        "carteira": ctx["carteira"],
        "espécie da moeda": ctx["especie_moeda"],
    }
    ausentes = [f"{rot} ({val!r})" for rot, val in obrigatorios.items() if val not in impressos]
    assert not ausentes, f"{nome}/{modelo}: campos não impressos: {ausentes}"


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
def test_beneficiario_e_pagador_aparecem_pelo_nome(nome: str, modelo: str) -> None:
    """O nome pode ser cortado pela largura da célula; o começo tem de estar lá."""
    escritas, _, _, ctx = _desenho(nome, modelo)
    impressos = _impressos(escritas)
    for papel, nome_pessoa in (
        ("beneficiário", ctx["beneficiario"]["nome"]),
        ("pagador", ctx["pagador"]["nome"]),
    ):
        prefixo = nome_pessoa[:12]
        assert any(s.startswith(prefixo) for s in impressos), (
            f"{nome}/{modelo}: {papel} {nome_pessoa!r} não foi impresso"
        )


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
def test_a_linha_digitavel_impressa_e_a_do_codigo_de_barras(nome: str, modelo: str) -> None:
    """O que a pessoa digita para pagar tem de ser o número que o banco leria.

    Um separador a mais, um dígito a menos ou o campo de outro título e o
    pagamento vai para o lugar errado — e o PDF continua válido.
    """
    from pycobranca.boleto.linha_digitavel import linha_digitavel

    escritas, _, _, ctx = _desenho(nome, modelo)
    impressa = next(s for s in _impressos(escritas) if s == ctx["linha_digitavel"])
    assert impressa == linha_digitavel(ctx["codigo_barras"])
    assert len([c for c in impressa if c.isdigit()]) == 47


# ---- 2. nada sai do lugar ----


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
@pytest.mark.parametrize("variante", ["simples", "encargos", "longos"])
def test_nenhum_texto_ultrapassa_a_moldura_da_pagina(nome, modelo, variante) -> None:
    """Texto fora da área útil é texto que o papel corta — sem erro nenhum."""
    escritas, _, mm, _ = _desenho(nome, modelo, variante)
    esquerda, direita = _MARGEM * mm, (_MARGEM + _LARGURA) * mm
    fora = [
        f"{e['s'][:40]!r} em x=[{e['x0']:.1f}, {e['x1']:.1f}]"
        for e in escritas
        if e["x0"] < esquerda - 0.5 or e["x1"] > direita + 0.5
    ]
    assert not fora, (
        f"{nome}/{modelo}/{variante}: fora da área útil ({esquerda:.1f}–{direita:.1f}): {fora}"
    )


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
@pytest.mark.parametrize("variante", ["simples", "encargos", "longos"])
def test_nenhum_texto_escreve_por_cima_de_outro(nome, modelo, variante) -> None:
    """Duas caixas de tinta não podem se sobrepor: no papel viram um borrão.

    É o defeito que a faixa de totalizadores tinha — o encargo de sete dígitos
    crescia para a esquerda até entrar embaixo do próprio rótulo.
    """
    escritas, _, _, _ = _desenho(nome, modelo, variante)
    colisoes = [
        f"{a['s'][:30]!r} × {b['s'][:30]!r}"
        for i, a in enumerate(escritas)
        for b in escritas[i + 1 :]
        if _sobrepoem(a, b)
    ]
    assert not colisoes, f"{nome}/{modelo}/{variante}: tinta sobre tinta: {colisoes[:6]}"


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
def test_texto_longo_fica_dentro_da_celula(nome: str, modelo: str) -> None:
    """A célula é a moldura do campo; o texto que começa dentro dela termina dentro.

    Com razão social e endereço extensos, o motor desenhava o texto inteiro a
    partir da coordenada inicial e ele atravessava a borda.
    """
    escritas, molduras, _, _ = _desenho(nome, modelo, "longos")
    vazamentos = []
    for e in escritas:
        donas = [
            m
            for m in molduras
            if m[0] - 0.6 <= e["x0"] < m[2] and m[1] <= e["base"] <= m[3] and m[2] - m[0] > 1
        ]
        if donas and e["x1"] > max(m[2] for m in donas) + 0.6:
            largura = max(m[2] for m in donas) - e["x0"]
            vazamentos.append(
                f"{e['s'][:40]!r} passa {e['x1'] - max(m[2] for m in donas):.1f}pt "
                f"da célula de {largura:.1f}pt"
            )
    assert not vazamentos, f"{nome}/{modelo}: texto fora da célula: {vazamentos[:5]}"


# ---- 3. os números leem-se como números ----


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
def test_valores_e_datas_alinham_a_direita(nome: str, modelo: str) -> None:
    """Coluna de números só se confere alinhada à direita — vírgula sob vírgula."""
    escritas, _, _, ctx = _desenho(nome, modelo)
    à_direita = {e["s"] for e in escritas if e["ancora"] == "dir"}
    devem = {
        "valor do documento": ctx["valor_documento"],
        "vencimento": ctx["vencimento"],
        "nosso número": ctx["nosso_numero"],
        "agência/código": ctx["beneficiario"]["agencia_codigo"],
    }
    erradas = [f"{rot} ({val!r})" for rot, val in devem.items() if val not in à_direita]
    assert not erradas, f"{nome}/{modelo}: não alinhados à direita: {erradas}"


# ---- 4. o Bolepix abre uma coluna a mais ----


@pytest.mark.parametrize(("nome", "modelo"), CASOS_PIX)
def test_com_pix_o_layout_continua_intacto(nome: str, modelo: str) -> None:
    """A coluna do QR é recortada do bloco de instruções: nada pode transbordar."""
    escritas, _, mm, _ = _desenho(nome, modelo, "pix")
    esquerda, direita = _MARGEM * mm, (_MARGEM + _LARGURA) * mm
    fora = [e["s"][:40] for e in escritas if e["x0"] < esquerda - 0.5 or e["x1"] > direita + 0.5]
    colisoes = [
        f"{a['s'][:24]!r} × {b['s'][:24]!r}"
        for i, a in enumerate(escritas)
        for b in escritas[i + 1 :]
        if _sobrepoem(a, b)
    ]
    assert not fora, f"{nome}/{modelo}/pix: fora da área útil: {fora}"
    assert not colisoes, f"{nome}/{modelo}/pix: tinta sobre tinta: {colisoes[:6]}"


@pytest.mark.parametrize(("nome", "modelo"), CASOS_PIX)
def test_com_pix_os_campos_do_titulo_continuam_impressos(nome: str, modelo: str) -> None:
    """Abrir espaço para o QR não pode custar um campo do boleto."""
    escritas, _, _, ctx = _desenho(nome, modelo, "pix")
    impressos = _impressos(escritas)
    faltando = [
        val
        for val in (
            ctx["linha_digitavel"],
            ctx["vencimento"],
            ctx["valor_documento"],
            ctx["nosso_numero"],
        )
        if val not in impressos
    ]
    assert not faltando, f"{nome}/{modelo}/pix: campos não impressos: {faltando}"


@pytest.mark.parametrize(("nome", "modelo"), CASOS)
def test_encargo_informado_nao_chega_ao_papel(nome: str, modelo: str) -> None:
    """A faixa de desconto/mora/total é preenchida pelo caixa, no ato do pagamento.

    O título aqui vai com os quatro encargos em ``1.234.567,89``; se algum
    aparecer impresso, o pagador lê um encargo que o banco ainda não apurou.
    """
    escritas, _, _, ctx = _desenho(nome, modelo, "encargos")
    impressos = _impressos(escritas)
    assert set(ctx["totalizadores"].values()) == {""}, (
        f"{nome}/{modelo}: contexto de render trouxe encargo: {ctx['totalizadores']}"
    )
    assert "1.234.567,89" not in impressos, f"{nome}/{modelo}: encargo impresso no boleto"
    truncados = [s for s in impressos if s.endswith("…") and any(c.isdigit() for c in s[:-1])]
    assert not truncados, f"{nome}/{modelo}: número cortado: {truncados}"
