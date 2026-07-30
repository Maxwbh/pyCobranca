"""Validação cruzada com a BrCobrança (Ruby).

Os valores esperados foram **gerados pela BrCobrança** (fork Maxwbh, Ruby 3.3)
com exatamente os mesmos dados de entrada e conferidos campo a campo contra a
PyCobrança. Servem como fixtures permanentes de paridade: qualquer regressão
que altere código de barras ou linha digitável quebra estes testes.

Os exemplos vivem em :mod:`exemplos_boletos` (fonte única, compartilhada com o
validador FEBRABAN independente de ``test_validacao_externa.py``).
"""

from __future__ import annotations

import pytest
from exemplos_boletos import EXEMPLOS


@pytest.mark.parametrize("nome", sorted(EXEMPLOS))
def test_paridade_cruzada(nome: str) -> None:
    caso = EXEMPLOS[nome]
    boleto = caso["boleto"]()
    assert boleto.codigo_barras == caso["codigo_barras"], f"{nome}: código de barras diverge"
    assert boleto.linha_digitavel == caso["linha_digitavel"], f"{nome}: linha digitável diverge"
    assert boleto.nosso_numero_formatado() == caso["nosso_numero"], f"{nome}: nosso número diverge"
