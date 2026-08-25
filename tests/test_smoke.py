"""Testes de fumaça da fundação do projeto.

Garantem que o pacote importa, expõe versão e que o registro inicial de bancos
está coerente. À medida que o roadmap avança, novos módulos de teste cobrem
núcleo, boleto, CNAB, PIX e integração.
"""

from __future__ import annotations

import pytest

import pycobranca
from pycobranca.bancos import REGISTRO


def test_versao_exposta() -> None:
    assert isinstance(pycobranca.__version__, str)
    assert pycobranca.__version__.count(".") == 2


def test_bancos_deriva_do_registro_e_cobre_todos() -> None:
    """``BANCOS`` é derivado do ``REGISTRO`` (fonte única) e cobre todos os bancos."""
    assert pycobranca.BANCOS == {codigo: cls.nome for codigo, cls in REGISTRO.items()}
    assert len(pycobranca.BANCOS) == 19
    # os prioritários continuam presentes
    assert {"001", "033", "104", "237", "341"} <= pycobranca.BANCOS.keys()


@pytest.mark.parametrize("codigo", sorted(REGISTRO))
def test_banco_info_para_todo_banco_registrado(codigo: str) -> None:
    assert pycobranca.banco_info(codigo) == REGISTRO[codigo].nome


def test_banco_info_normaliza_codigo() -> None:
    assert pycobranca.banco_info("341") == "Itaú"
    # aceita código sem zero à esquerda
    assert pycobranca.banco_info("1") == "Banco do Brasil"
    assert pycobranca.banco_info(1) == "Banco do Brasil"  # aceita int


def test_banco_info_desconhecido_levanta() -> None:
    with pytest.raises(KeyError):
        pycobranca.banco_info("999")
