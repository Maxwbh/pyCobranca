"""A faixa de encargos do boleto sai **em branco** — quem preenche é o caixa.

Desconto/abatimento, outras deduções, mora/multa, outros acréscimos e valor
cobrado são campos da ficha FEBRABAN preenchidos **no ato do pagamento**, pela
instituição que recebe. A regra do título vive no bloco de **instruções**
("após o vencimento, multa de 2% e juros de 1% ao mês"), que é o que o caixa lê
para calcular.

A biblioteca já sabia disso pela metade: deixava a faixa vazia quando nada era
informado, mas imprimia o que o emissor preenchesse **e ainda somava o total** —
fazendo, no papel, a conta que é do caixa. Um total impresso antes do pagamento
induz o pagador a pagar o valor errado, e nada no PDF denuncia o erro.

As molduras continuam desenhadas: elas fazem parte do formulário. O que não sai
é o conteúdo, aconteça o que acontecer com os campos do título.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

import pytest

from pycobranca.bancos import Bancos
from pycobranca.render import desenha_boleto
from pycobranca.render.comum import _LARGURA, _MARGEM, _canvas_e_libs
from pycobranca.render.tela import Tela

CHAVES = (
    "desconto_abatimento",
    "outras_deducoes",
    "mora_multa",
    "outros_acrescimos",
    "valor_cobrado",
)

#: Preenchidos com valores que, se vazassem para o papel, seriam inconfundíveis.
ENCARGOS = {
    "desconto_abatimento": "1150375.42",
    "outras_deducoes": "212345.30",
    "mora_multa": "98765.00",
    "outros_acrescimos": "43210.20",
    "valor_cobrado": "999888.77",
}

#: Como cada um sairia formatado, se a faixa fosse impressa.
FORMATADOS = (
    "1.150.375,42",
    "212.345,30",
    "98.765,00",
    "43.210,20",
    "999.888,77",
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


# ---- o contexto de render não carrega valor ----


def test_sem_encargos_a_faixa_sai_em_branco() -> None:
    assert totais() == dict.fromkeys(CHAVES, "")


def test_com_encargos_a_faixa_continua_em_branco() -> None:
    """O campo preenchido no título não vira número no papel."""
    assert totais(**ENCARGOS) == dict.fromkeys(CHAVES, "")


def test_valor_cobrado_nao_e_calculado() -> None:
    """A soma é do caixa. Antes a biblioteca fazia 1.279,50 − 150,00 e imprimia."""
    assert totais(desconto_abatimento="150.00")["valor_cobrado"] == ""


def test_valor_cobrado_informado_tambem_nao_sai() -> None:
    """Nem mesmo o total explícito — o campo é do caixa, não do emissor."""
    assert totais(valor_cobrado="1000.00")["valor_cobrado"] == ""


@pytest.mark.parametrize("bruto", ["150.00", 150.0, 150, Decimal("150.00")])
def test_o_campo_continua_aceito_no_titulo(bruto) -> None:
    """Aceitar não é imprimir: o valor segue no objeto e no contrato REST.

    Quem informa o encargo continua conseguindo trafegá-lo — o que mudou é que
    ele não chega ao papel.
    """
    assert boleto(desconto_abatimento=bruto).desconto_abatimento == Decimal("150")


# ---- e o papel também não ----


class _Espia:
    """Canvas ReportLab que anota cada texto desenhado: alinhamento, x e corpo."""

    def __init__(self):
        _, _, _, Canvas = _canvas_e_libs()
        self.canvas = Canvas(io.BytesIO())
        self.desenhos: list[tuple[str, float, float, str]] = []
        self._tam = 0.0
        self._fonte = "Helvetica"

    def __getattr__(self, nome):
        return getattr(self.canvas, nome)

    def setFont(self, fonte, tam, *a, **k):  # noqa: N802 (API do ReportLab)
        self._fonte, self._tam = fonte, tam
        return self.canvas.setFont(fonte, tam, *a, **k)

    def _anota(self, modo, x, s):
        if s and s.strip():
            self.desenhos.append((modo, x, self._tam, s))

    def drawString(self, x, y, s):  # noqa: N802
        self._anota("esq", x, s)
        return self.canvas.drawString(x, y, s)

    def drawRightString(self, x, y, s):  # noqa: N802
        self._anota("dir", x, s)
        return self.canvas.drawRightString(x, y, s)

    def drawCentredString(self, x, y, s):  # noqa: N802
        self._anota("cen", x, s)
        return self.canvas.drawCentredString(x, y, s)


def _desenhos(modelo, **extra):
    espia = _Espia()
    contexto = boleto(**extra).contexto_render()
    desenha_boleto(Tela(espia, moderno=modelo == "moderno"), contexto, modelo=modelo)
    return espia.desenhos


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_nenhum_encargo_chega_ao_papel(modelo) -> None:
    """Ponta a ponta: com os cinco campos preenchidos, nenhum número sai."""
    escritos = {s for *_, s in _desenhos(modelo, **ENCARGOS)}
    vazaram = [v for v in FORMATADOS if v in escritos]
    assert not vazaram, f"encargo impresso no modelo {modelo}: {vazaram}"


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_os_rotulos_da_faixa_continuam_impressos(modelo) -> None:
    """A moldura é do formulário: sai sempre, para o caixa preencher à mão."""
    escritos = {s.upper() for *_, s in _desenhos(modelo)}
    for rotulo in ("DESCONTO", "MORA", "ACRÉSCIMOS", "VALOR COBRADO"):
        assert any(rotulo in s for s in escritos), (
            f"rótulo {rotulo!r} não foi impresso no modelo {modelo}"
        )


@pytest.mark.parametrize("modelo", ["moderno", "classico"])
def test_o_valor_do_documento_continua_saindo_e_alinhado(modelo) -> None:
    """O que o emissor cobra é dele: esse número não pode sumir junto."""
    desenhos = _desenhos(modelo, **ENCARGOS)
    _, _, mm, _ = _canvas_e_libs()
    borda = round((_MARGEM + _LARGURA - 1.5) * mm, 2)
    bordas = [round(x, 2) for modo, x, _t, s in desenhos if modo == "dir" and s == "1.279,50"]
    assert bordas, f"valor do documento não foi impresso no modelo {modelo}"
    assert borda in bordas, f"valor do documento não termina em {borda:.2f}: {bordas}"
