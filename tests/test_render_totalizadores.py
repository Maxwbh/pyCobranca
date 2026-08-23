"""A faixa de totalizadores do boleto: valores reais e casas decimais alinhadas.

Os cinco campos da faixa FEBRABAN — desconto/abatimento, outras deduções,
mora/multa, outros acréscimos e valor cobrado — eram desenhados com string
vazia: a moldura saía no papel, o número nunca. Quem emitia um boleto com
desconto por pontualidade não tinha onde imprimi-lo.

Em branco continua sendo o padrão, e de propósito: no boleto comum quem
preenche essa faixa é o caixa, no ato do pagamento. Imprimir ``0,00`` num campo
que o emissor não informou seria pior do que deixá-lo vazio — induz o pagador a
achar que o total já está fechado.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

import pytest

from pycobranca.bancos import Bancos
from pycobranca.render import desenha_boleto
from pycobranca.render.comum import _LARGURA, _MARGEM, _canvas_e_libs

#: Os três chips do recibo moderno (vencimento, valor, nosso número) são cartões
#: de leitura, não coluna de soma: ali o valor acompanha o rótulo à esquerda, e é
#: o único lugar do boleto em que isso é intencional. O corpo vem do próprio
#: modelo para o teste não descolar dele.
from pycobranca.render.modelos.boleto_moderno import _CHIP_TAM as _CORPO_CHIP
from pycobranca.render.tela import _RETICENCIAS, Tela

#: Altura de caixa alta como fração do corpo, nas Helvetica: é ela que decide
#: se dois textos em linhas de base vizinhas encostam. O corpo inteiro inclui a
#: descida e exageraria a colisão.
_CAIXA_ALTA = 0.72

CHAVES = (
    "desconto_abatimento",
    "outras_deducoes",
    "mora_multa",
    "outros_acrescimos",
    "valor_cobrado",
)


def boleto(valor="1279.50", **extra):
    Banco = Bancos.find("341")
    return Banco(
        valor=valor,
        cedente="EMPRESA EXEMPLO COMERCIO LTDA",
        cedente_documento="11.222.333/0001-81",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 9, 10),
        sacado="CLIENTE FINAL LTDA",
        sacado_documento="529.982.247-25",
        **extra,
    )


def totais(**extra):
    return boleto(**extra).contexto_render()["totalizadores"]


# ---- valores ----


def test_sem_encargos_a_faixa_sai_em_branco() -> None:
    """Padrão: nenhum campo informado, nenhum número impresso — nem ``0,00``."""
    assert totais() == dict.fromkeys(CHAVES, "")


def test_encargo_informado_aparece_formatado() -> None:
    assert totais(desconto_abatimento="150.00")["desconto_abatimento"] == "150,00"


def test_valor_cobrado_e_somado_quando_ha_encargo() -> None:
    """1.279,50 − 150,00 = 1.129,50."""
    assert totais(desconto_abatimento="150.00")["valor_cobrado"] == "1.129,50"


def test_valor_cobrado_com_os_quatro_campos() -> None:
    """1.279,50 − 150,00 − 12,30 + 8,00 + 3,20 = 1.128,40."""
    t = totais(
        desconto_abatimento="150.00",
        outras_deducoes="12.30",
        mora_multa="8.00",
        outros_acrescimos="3.20",
    )
    assert t["valor_cobrado"] == "1.128,40"


def test_valor_cobrado_explicito_sobrepoe_a_soma() -> None:
    """Quando o banco já apurou o total, é ele que vale — não a nossa conta."""
    t = totais(desconto_abatimento="150.00", valor_cobrado="1000.00")
    assert t["valor_cobrado"] == "1.000,00"


def test_valor_cobrado_sozinho_dispensa_as_parcelas() -> None:
    t = totais(valor_cobrado="1279.50")
    assert t["valor_cobrado"] == "1.279,50"
    assert t["desconto_abatimento"] == ""


@pytest.mark.parametrize("bruto", ["150.00", 150.0, 150, Decimal("150.00")])
def test_aceita_str_float_int_e_decimal(bruto) -> None:
    """Mesma tolerância de ``valor``: o chamador não deveria precisar saber."""
    b = boleto(desconto_abatimento=bruto)
    assert b.desconto_abatimento == Decimal("150")
    assert b.contexto_render()["totalizadores"]["desconto_abatimento"] == "150,00"


def test_milhar_usa_o_separador_brasileiro() -> None:
    assert totais(mora_multa="1234.56")["mora_multa"] == "1.234,56"


# ---- alinhamento ----


class _Espia:
    """Canvas ReportLab que anota cada texto desenhado: alinhamento, x e corpo."""

    def __init__(self):
        _, _, _, Canvas = _canvas_e_libs()
        self.canvas = Canvas(io.BytesIO())
        self.desenhos: list[tuple[str, float, float, str]] = []
        #: ``(y, corpo, x0, x1, texto)`` de cada texto, para checar sobreposição
        self.caixas: list[tuple[float, float, float, float, str]] = []
        self._tam = 0.0
        self._fonte = "Helvetica"

    def __getattr__(self, nome):
        return getattr(self.canvas, nome)

    def setFont(self, fonte, tam, *args, **kwargs):  # noqa: N802 (API do ReportLab)
        self._fonte, self._tam = fonte, tam
        return self.canvas.setFont(fonte, tam, *args, **kwargs)

    def _anota(self, modo, x, y, s):
        largura = self.canvas.stringWidth(s, self._fonte, self._tam)
        x0 = {"esq": x, "dir": x - largura, "centro": x - largura / 2}[modo]
        self.desenhos.append((modo, x, self._tam, s))
        self.caixas.append((y, self._tam, x0, x0 + largura, s))

    def drawString(self, x, y, s):
        self._anota("esq", x, y, s)
        return self.canvas.drawString(x, y, s)

    def drawRightString(self, x, y, s):
        self._anota("dir", x, y, s)
        return self.canvas.drawRightString(x, y, s)

    def drawCentredString(self, x, y, s):
        self._anota("centro", x, y, s)
        return self.canvas.drawCentredString(x, y, s)


ENCARGOS = {
    "desconto_abatimento": "150.00",
    "outras_deducoes": "12.30",
    "mora_multa": "8.00",
    "outros_acrescimos": "3.20",
}


def _desenhos(modelo):
    espia = _Espia()
    contexto = boleto(**ENCARGOS).contexto_render()
    desenha_boleto(Tela(espia, moderno=modelo == "moderno"), contexto, modelo=modelo)
    return espia.desenhos, contexto["totalizadores"]


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_totalizadores_saem_no_papel(modelo) -> None:
    desenhos, totalizadores = _desenhos(modelo)
    escritos = {d[-1] for d in desenhos}
    for valor in totalizadores.values():
        assert valor in escritos, f"{valor!r} não foi desenhado no modelo {modelo}"


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_todo_valor_monetario_vai_alinhado_a_direita(modelo) -> None:
    """Numa coluna de totais, é a vírgula alinhada que deixa a soma legível."""
    desenhos, totalizadores = _desenhos(modelo)
    alvos = set(totalizadores.values()) | {"1.279,50"}
    esquerda = [
        (round(x, 1), s)
        for modo, x, tam, s in desenhos
        if modo == "esq" and s in alvos and tam != _CORPO_CHIP
    ]
    assert not esquerda, f"valores à esquerda no modelo {modelo}: {esquerda}"


GRANDES = {
    "desconto_abatimento": "1150375.42",
    "outras_deducoes": "212345.30",
    "mora_multa": "98765.00",
    "outros_acrescimos": "43210.20",
}


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_valor_de_sete_digitos_nao_passa_por_cima_do_rotulo(modelo) -> None:
    """A faixa é estreita: o valor vem da direita e cresce em direção ao rótulo.

    A 6,5 mm no moderno e 6,0 mm no clássico, rótulo e valor caíam na mesma
    linha de base — ``(-) DESCONTO / ABATIMENTOS`` deixava 46 pt e
    ``1.150.375,42`` pede 49,6. Não pode terminar em número truncado nem em
    dois textos sobrepostos: ambos tornam o campo ilegível.
    """
    espia = _Espia()
    contexto = boleto(valor="1279500.00", **GRANDES).contexto_render()
    desenha_boleto(Tela(espia, moderno=modelo == "moderno"), contexto, modelo=modelo)

    # Nenhum valor abreviado: "1.150.…" não é dinheiro. Buscar a reticência em
    # vez do valor íntegro é o que pega o caso em que a faixa do recibo corta e
    # a coluna da ficha, mais larga, imprime o mesmo número inteiro.
    cortados = [s for *_, s in espia.caixas if _RETICENCIAS in s]
    assert not cortados, f"valor abreviado no modelo {modelo}: {cortados}"
    for valor in contexto["totalizadores"].values():
        assert valor in {d[-1] for d in espia.desenhos}, f"{valor!r} não foi desenhado"

    # Colisão não é "mesma linha de base": o rótulo sai a 5,8 pt e o valor a
    # 8,5 pt, em bases diferentes. O que conta é a faixa de tinta — da linha de
    # base até a altura de caixa alta (``_CAIXA_ALTA``).
    for i, (y_a, tam_a, a0, a1, s_a) in enumerate(espia.caixas):
        for y_b, tam_b, b0, b1, s_b in espia.caixas[i + 1 :]:
            vertical = min(y_a + _CAIXA_ALTA * tam_a, y_b + _CAIXA_ALTA * tam_b) - max(y_a, y_b)
            if vertical <= 0:
                continue
            assert min(a1, b1) - max(a0, b0) <= 0.6, (
                f"{s_a!r} e {s_b!r} se sobrepõem no modelo {modelo}"
            )


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_coluna_da_ficha_compartilha_a_mesma_borda_direita(modelo) -> None:
    """Os cinco da ficha e o valor do documento terminam na mesma coordenada."""
    _, _, mm, _ = _canvas_e_libs()
    borda = round((_MARGEM + _LARGURA - 1.5) * mm, 2)
    desenhos, totalizadores = _desenhos(modelo)
    for valor in list(totalizadores.values()) + ["1.279,50"]:
        bordas = [round(x, 2) for modo, x, _tam, s in desenhos if modo == "dir" and s == valor]
        assert borda in bordas, f"{valor!r} não termina em {borda:.2f}: {bordas}"
