"""Duas promessas que a documentação faz ao integrador, presas por teste.

1. **Um `except` cobre a biblioteca inteira.** ``docs/19-integracao.md`` diz isso,
   e a doc estava errada: ``InvalidBarcodeError`` e ``ErroDeContrato`` herdavam
   só de ``ValueError``. Quem seguisse a orientação deixava a exceção escapar do
   handler — e o efeito aparece em produção, não em teste.

2. **O contrato REST acompanha o domínio.** Campo novo em ``BancoBase`` que não
   chegue ao ``BoletoData`` deixa o consumidor sem acesso ao recurso, sem nada
   quebrar. Aconteceu com a faixa de totalizadores.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
from datetime import date
from pathlib import Path

import pytest

import pycobranca
from pycobranca.bancos import Bancos
from pycobranca.contracts import TOTALIZADORES, boleto_para_api, valida_contrato
from pycobranca.contracts.contrato_rest import CONTRATO
from pycobranca.exceptions import PyCobrancaError


def _linha_digitavel(codigo: str):
    from pycobranca.boleto.linha_digitavel import linha_digitavel

    return linha_digitavel(codigo)


def _modulo10(sequencia: str):
    from pycobranca.core.dv import modulo10

    return modulo10(sequencia)


def _campo_livre_curto():
    from pycobranca.boleto.codigo_barras import montar_codigo_barras

    return montar_codigo_barras("341", 1000, 12750, "0" * 24)


def _render_modelo(modelo: str):
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    return render_boleto_pdf(_boleto().contexto_render(), modelo=modelo)


def _fatura_bloco(tipo: str):
    pytest.importorskip("reportlab")
    from pycobranca.render import render_fatura_pdf

    contexto = _boleto().contexto_render()
    contexto["fatura"] = {"blocos": [{"tipo": tipo}]}
    return render_fatura_pdf(contexto)


def _todas_as_excecoes():
    """Toda classe de exceção definida dentro do pacote, em qualquer módulo."""
    achadas: dict[str, type] = {}
    for info in pkgutil.walk_packages(pycobranca.__path__, "pycobranca."):
        try:
            mod = importlib.import_module(info.name)
        except Exception:  # noqa: BLE001 — módulo opcional não instalado
            continue
        for nome, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, BaseException) and obj.__module__.startswith("pycobranca"):
                achadas[f"{obj.__module__}.{nome}"] = obj
    return achadas


def test_toda_excecao_do_pacote_herda_de_pycobranca_error() -> None:
    foras = [
        caminho
        for caminho, cls in _todas_as_excecoes().items()
        if not issubclass(cls, PyCobrancaError)
    ]
    assert not foras, f"não herdam de PyCobrancaError: {foras}"


def test_o_pacote_nao_levanta_builtin_direto() -> None:
    """Classe na hierarquia não basta: o que conta é o que escapa da chamada.

    O teste acima confere as **classes** — e passava enquanto 14 pontos do
    pacote levantavam ``ValueError``/``KeyError``/``RuntimeError`` crus, de modo
    que a promessa de ``docs/19`` continuava falsa. Aqui a busca é no código.
    """
    padrao = re.compile(r"^\s*raise (ValueError|KeyError|TypeError|RuntimeError|Exception)\b")
    raiz = Path(pycobranca.__file__).parent
    achados = [
        f"{arquivo.relative_to(raiz)}:{i}: {linha.strip()}"
        for arquivo in sorted(raiz.rglob("*.py"))
        for i, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1)
        if padrao.match(linha)
    ]
    assert not achados, (
        "erro embutido levantado direto (use uma exceção da hierarquia):\n" + "\n".join(achados)
    )


@pytest.mark.parametrize(
    ("rotulo", "chamada"),
    [
        ("banco_info com código fora do registro", lambda: pycobranca.banco_info("999")),
        (
            "vencimento anterior à base do fator",
            lambda: _boleto(data_vencimento=date(1990, 1, 1)).codigo_barras,
        ),
        (
            "vencimento além do rollover",
            lambda: _boleto(data_vencimento=date(2099, 1, 1)).codigo_barras,
        ),
        ("linha digitável de código curto", lambda: _linha_digitavel("123")),
        ("módulo 10 sem dígitos", lambda: _modulo10("abc")),
        ("campo livre com 24 posições", lambda: _campo_livre_curto()),
        ("modelo de boleto inexistente", lambda: _render_modelo("art-deco")),
        ("bloco de fatura inexistente", lambda: _fatura_bloco("inexistente")),
    ],
)
def test_entrada_publica_so_levanta_erro_da_hierarquia(rotulo, chamada) -> None:
    """Cada um destes já escapou de um ``except PyCobrancaError`` em produção."""
    with pytest.raises(PyCobrancaError):
        chamada()


@pytest.mark.parametrize(
    ("caminho", "embutida"),
    [
        ("pycobranca.exceptions.BoletoInvalido", ValueError),
        ("pycobranca.exceptions.BancoNaoRegistrado", KeyError),
        ("pycobranca.exceptions.OFXInvalido", ValueError),
        ("pycobranca.exceptions.RetornoInvalido", ValueError),
        ("pycobranca.render.barcode.InvalidBarcodeError", ValueError),
        ("pycobranca.contracts.contrato_rest.ErroDeContrato", ValueError),
    ],
)
def test_excecao_tambem_e_o_erro_embutido_correspondente(caminho, embutida) -> None:
    """Quem já tratava por ``ValueError``/``KeyError`` não pode ser quebrado."""
    cls = _todas_as_excecoes()[caminho]
    assert issubclass(cls, embutida)
    # PyCobrancaError vem antes na MRO: é a captura mais específica das duas.
    mro = cls.__mro__
    assert mro.index(PyCobrancaError) < mro.index(embutida)


# ---- contrato x domínio ----


def _boleto(data_vencimento: date = date(2026, 9, 10), **extra):
    Banco = Bancos.find("341")
    return Banco(
        valor="1279.50",
        cedente="EMPRESA EXEMPLO LTDA",
        cedente_documento="11.222.333/0001-81",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=data_vencimento,
        sacado="CLIENTE FINAL LTDA",
        sacado_documento="529.982.247-25",
        **extra,
    )


def test_os_totalizadores_estao_declarados_no_boleto_data() -> None:
    props = CONTRATO["schemas"]["BoletoData"]["properties"]
    ausentes = [c for c in TOTALIZADORES if c not in props]
    assert not ausentes, f"campos do domínio fora do contrato: {ausentes}"


def test_totalizadores_informados_saem_no_payload() -> None:
    data = boleto_para_api(_boleto(desconto_abatimento="150.00", mora_multa="8.00"))["data"]
    assert data["desconto_abatimento"] == 150.0
    assert data["mora_multa"] == 8.0
    valida_contrato(data, "BoletoData")


def test_boleto_sem_encargos_nao_ganha_campo_no_payload() -> None:
    """Compatibilidade: o payload de quem não usa a faixa fica como era antes."""
    data = boleto_para_api(_boleto())["data"]
    assert not [c for c in TOTALIZADORES if c in data]
    valida_contrato(data, "BoletoData")


def test_zero_informado_de_proposito_sobrevive() -> None:
    """``0`` é informação — só ``None`` (não informado) some do payload."""
    data = boleto_para_api(_boleto(desconto_abatimento="0"))["data"]
    assert data["desconto_abatimento"] == 0.0


def test_valor_cobrado_serializa_o_informado_e_nao_o_calculado() -> None:
    """``boleto_para_api`` é projeção do que o chamador montou, não do que sai impresso.

    O total calculado é decisão de renderização e vive em ``contexto_render()``;
    emiti-lo aqui viraria override explícito num eventual caminho de volta.
    """
    b = _boleto(desconto_abatimento="150.00")
    assert b.contexto_render()["totalizadores"]["valor_cobrado"] == "1.129,50"
    assert "valor_cobrado" not in boleto_para_api(b)["data"]
