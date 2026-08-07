"""Validação de entrada do OFX e do retorno CNAB (contrato de erros).

Um consumidor precisa distinguir **arquivo inválido** de **resultado vazio** — por isso
`Extrato`/`Retorno` levantam exceções claras em vez de devolver estrutura vazia silenciosa.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycobranca.cnab.retorno import Retorno
from pycobranca.exceptions import OFXInvalido, RetornoInvalido
from pycobranca.ofx import Extrato

FIXTURES_OFX = Path(__file__).parent / "fixtures" / "ofx"
FIXTURES_RET = Path(__file__).parent / "fixtures" / "retorno"


# ---- OFX ----


def test_ofx_conteudo_invalido_levanta() -> None:
    with pytest.raises(OFXInvalido):
        Extrato.parse("isto não é um OFX, apenas texto solto")


def test_ofx_bytes_invalidos_levantam() -> None:
    with pytest.raises(OFXInvalido):
        Extrato.ler(b"\x00\x01 lixo binario sem ofx")


def test_ofx_valido_nao_levanta() -> None:
    extrato = Extrato.ler(FIXTURES_OFX / "extrato_itau.ofx")
    assert extrato.transacoes  # tem transações


def test_ofx_valido_sem_transacoes_nao_levanta() -> None:
    # tem marcador <OFX> mas nenhuma STMTTRN → extrato válido e vazio (não é erro)
    minimo = "OFXHEADER:100\n<OFX><BANKMSGSRSV1></BANKMSGSRSV1></OFX>"
    extrato = Extrato.parse(minimo)
    assert extrato.transacoes == []


# ---- Retorno CNAB ----


def test_retorno_vazio_levanta() -> None:
    with pytest.raises(RetornoInvalido, match="vazio"):
        Retorno.ler_linhas(["", "   ", ""])


def test_retorno_sem_banco_levanta() -> None:
    # linha curta sem header de banco reconhecível
    with pytest.raises(RetornoInvalido, match="identificar o banco"):
        Retorno.ler_linhas(["linha qualquer sem header cnab valido"])


def test_retorno_valido_nao_levanta() -> None:
    retorno = Retorno.ler(FIXTURES_RET / "CNAB400ITAU.RET")
    assert retorno.codigo_banco
    assert len(retorno.registros) >= 1
