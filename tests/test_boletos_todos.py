"""Cobertura de **todos** os bancos: exemplos ↔ registro e geração de PDF.

Os testes parametrizados de paridade (``test_validacao_cruzada``) e do validador
FEBRABAN independente (``test_validacao_externa``) iteram sobre ``EXEMPLOS``.
Este módulo fecha o que eles pressupõem:

1. ``EXEMPLOS`` cobre **exatamente** o ``REGISTRO`` — se um banco novo entrar no
   registro sem exemplo, ele escaparia silenciosamente daquelas validações;
   aqui isso vira uma falha explícita.
2. Cada um dos 18 bancos gera um título estruturalmente válido (código de barras
   de 44, linha digitável de 47) e **renderiza** em PDF nos dois modelos.
"""

from __future__ import annotations

import pytest
from exemplos_boletos import EXEMPLOS

from pycobranca.bancos import REGISTRO


def _codigo_do_exemplo(nome: str) -> str:
    return str(EXEMPLOS[nome]["boleto"]().codigo).zfill(3)


def test_exemplos_cobrem_todo_o_registro() -> None:
    """Todo banco registrado tem exemplo (e vice-versa) — sem cobertura silenciosa."""
    do_registro = set(REGISTRO)
    dos_exemplos = {_codigo_do_exemplo(nome) for nome in EXEMPLOS}
    assert dos_exemplos == do_registro, (
        f"faltam exemplos para {sorted(do_registro - dos_exemplos)}; "
        f"exemplos sem banco no registro: {sorted(dos_exemplos - do_registro)}"
    )
    assert len(EXEMPLOS) == len(REGISTRO) == 18


@pytest.mark.parametrize("nome", sorted(EXEMPLOS))
def test_cada_banco_gera_titulo_valido_e_pdf(nome: str) -> None:
    """Para cada banco: título válido (44/47) e PDF válido (clássico e moderno)."""
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    boleto = EXEMPLOS[nome]["boleto"]()
    boleto.validar()  # não deve levantar

    cb = boleto.codigo_barras
    linha = "".join(c for c in boleto.linha_digitavel if c.isdigit())
    assert len(cb) == 44 and cb.isdigit(), f"{nome}: código de barras inválido"
    assert len(linha) == 47, f"{nome}: linha digitável não tem 47 dígitos"

    ctx = boleto.contexto_render()
    for modelo in ("classico", "moderno"):
        pdf = render_boleto_pdf(ctx, modelo=modelo)
        assert pdf.startswith(b"%PDF") and len(pdf) > 2000, f"{nome}/{modelo}: PDF inválido"
