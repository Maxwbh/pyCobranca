"""Testes de fumaça da fundação do projeto.

Garantem que o pacote importa, expõe versão e que o registro inicial de bancos
está coerente. À medida que o roadmap avança, novos módulos de teste cobrem
núcleo, boleto, CNAB, PIX e integração.
"""

from __future__ import annotations

import pytest

import pycobranca


def test_versao_exposta() -> None:
    assert isinstance(pycobranca.__version__, str)
    assert pycobranca.__version__.count(".") == 2


def test_registro_de_bancos_prioritarios() -> None:
    prioritarios = {"001", "033", "104", "237", "341"}
    assert prioritarios.issubset(pycobranca.BANCOS.keys())


def test_banco_info_normaliza_codigo() -> None:
    assert pycobranca.banco_info("341") == "Itaú"
    # aceita código sem zero à esquerda
    assert pycobranca.banco_info("1") == "Banco do Brasil"


def test_banco_info_desconhecido_levanta() -> None:
    with pytest.raises(KeyError):
        pycobranca.banco_info("999")
