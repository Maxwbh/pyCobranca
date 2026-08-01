"""Leitura de extrato bancário **OFX** (v1 SGML e v2 XML) e conciliação.

Complementa o retorno CNAB: lê o extrato do banco, extrai o nosso número do
memo de cada transação e concilia contra os boletos emitidos.

    from pycobranca.ofx import Extrato, concilia

    extrato = Extrato.ler("extrato.ofx")
    resultado = concilia(extrato, ["12345678", "87654321"])
"""

from __future__ import annotations

from .conciliacao import Conciliacao, concilia
from .nosso_numero import extrair_nosso_numero
from .parser import Extrato, Transacao

__all__ = [
    "Extrato",
    "Transacao",
    "extrair_nosso_numero",
    "Conciliacao",
    "concilia",
]
