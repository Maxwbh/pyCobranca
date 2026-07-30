"""Retorno CNAB (400 e 240) — parsing validado contra vetores de referência.

As fixtures ``.RET`` em ``tests/fixtures/retorno/`` são as mesmas usadas pela
de referência; os valores esperados abaixo foram extraídos de uma implementação de
referência (Ruby)
carregando cada arquivo e serializando os registros. O parser da PyCobrança
deve reproduzir os mesmos campos.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pycobranca.cnab.retorno import Retorno, descreve_ocorrencia

FIXTURES = Path(__file__).parent / "fixtures" / "retorno"

# (arquivo, layout, banco, nº de registros de detalhe — header e trailer excluídos)
CASOS = [
    ("CNAB400ITAU.RET", "400", "341", 52),
    ("CNAB400BRADESCO.RET", "400", "237", 6),
    ("CNAB400SANTANDER.RET", "400", "033", 53),
    ("CNAB400BANRISUL.RET", "400", "041", 1),
    ("CNAB400BANCONORDESTE.RET", "400", "004", 1),
    ("CNAB400CREDISIS.RET", "400", "097", 1),
    # o header deste arquivo traz o código 001 — o layout é escolhido pelo header,
    # (também processado como Banco do Brasil)
    ("CNAB400UNICRED.RET", "400", "001", 1),
    ("CNAB400BANCOBRASILIA.RET", "400", "070", 1),
    ("CNAB240SANTANDER.RET", "240", "033", 2),
    ("CNAB240AILOS.RET", "240", "085", 3),
    ("CNAB240SICOOB.RET", "240", "756", 3),
]


@pytest.mark.parametrize(("arquivo", "layout", "banco", "n"), CASOS)
def test_retorno_detecta_layout_e_banco(arquivo, layout, banco, n) -> None:
    retorno = Retorno.ler(FIXTURES / arquivo)
    assert retorno.layout == layout
    assert retorno.codigo_banco == banco
    assert len(retorno.registros) == n


def test_retorno_itau_primeiro_registro() -> None:
    retorno = Retorno.ler(FIXTURES / "CNAB400ITAU.RET")
    r = retorno.registros[0]
    assert r.codigo_registro == "1"
    assert r.nosso_numero == "00000011"
    assert r.carteira == "I"
    assert r.codigo_ocorrencia == "06"
    assert r.valor_titulo == "0000000004000"
    assert r.valor_recebido == "0000000003790"
    assert r.data_ocorrencia == "200513"
    assert r.data_credito == "210513"
    assert r.banco_recebedor == "104"
    assert r.motivo_ocorrencia == []


def test_retorno_bradesco_agencia_com_dv_calculada() -> None:
    retorno = Retorno.ler(FIXTURES / "CNAB400BRADESCO.RET")
    # agencia_com_dv é derivada de agencia_sem_dv por módulo 11 (regra Bradesco)
    assert retorno.registros[0].agencia_sem_dv == "01467"
    assert retorno.registros[0].agencia_com_dv == "01467-2"


def test_retorno_sicoob_240_segmentos_t_u() -> None:
    retorno = Retorno.ler(FIXTURES / "CNAB240SICOOB.RET")
    r = retorno.registros[0]
    # campo do segmento T
    assert r.nosso_numero == "0000000083"
    assert r.codigo_ocorrencia == "06"
    assert r.motivo_ocorrencia == ["03"]
    # campo do segmento U
    assert r.valor_recebido == "000000000000200"
    assert r.data_credito == "10082015"


def test_to_dict_compacto_remove_nulos() -> None:
    retorno = Retorno.ler(FIXTURES / "CNAB400BANRISUL.RET")
    dados = retorno.to_dict()
    assert isinstance(dados, list)
    assert all(v is not None for d in dados for v in d.values())


def test_descricao_ocorrencia() -> None:
    assert descreve_ocorrencia("06", "400") == "Liquidação normal"
    assert descreve_ocorrencia("09", "400") == "Baixa"
    assert descreve_ocorrencia("06", "240") == "Liquidação"
    assert descreve_ocorrencia("99", "400") is None
    assert descreve_ocorrencia(None) is None

    retorno = Retorno.ler(FIXTURES / "CNAB400ITAU.RET")
    assert retorno.descricao_ocorrencia(retorno.registros[0]) == "Liquidação normal"


def test_arquivo_generico_400_usa_layout_itau() -> None:
    # code path de fallback: banco não mapeado cai no layout base (Itaú)
    retorno = Retorno.ler(FIXTURES / "CNAB400ITAU.RET", layout="400")
    assert retorno.registros[0].sequencial == "000002"
