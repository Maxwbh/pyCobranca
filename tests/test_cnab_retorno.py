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
from pycobranca.cnab.retorno.cnab400 import LAYOUTS_400, parse_cnab400

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


# --- Inter (077): layout de retorno bem distante do comum --------------------
#
# O retorno do Inter põe a ocorrência em 90-91 e o vencimento em 119-124, onde a
# maioria dos bancos usa 109-110 e 147-152. Sem layout próprio, ``parse_cnab400``
# cai no fallback do Itaú e lê "seu número" como código de ocorrência: o arquivo
# inteiro parece válido e os campos saem trocados, sem exceção nenhuma.
#
# A fixture foi montada pelas posições do manual (v2.2, seção 5.2) — não há
# arquivo real do banco. Ela prova o mapeamento, não a realidade do arquivo que o
# Inter emite.

RETORNO_INTER = Path(__file__).parent / "fixtures" / "retorno_inter_cnab400.ret"


def _linhas_inter() -> list[str]:
    return RETORNO_INTER.read_text(encoding="ascii").replace("\r\n", "\n").rstrip("\n").split("\n")


def test_retorno_inter_le_os_campos_nas_posicoes_do_manual() -> None:
    retorno = Retorno.ler(str(RETORNO_INTER))
    assert retorno.codigo_banco == "077"
    assert len(retorno) == 2  # header e trailer não viram registro

    pago, cancelado = retorno.registros
    assert pago.codigo_ocorrencia == "06"  # 090-091
    assert pago.nosso_numero == "00043095401"  # 071-081, com DV
    assert pago.documento_numero == "2026-0003"  # 098-107 "seu número"
    assert pago.data_vencimento == "150826"  # 119-124
    assert pago.valor_titulo == "0000000012750"  # 125-137
    assert pago.valor_recebido == "0000000012750"  # 160-172 valor pago
    assert pago.data_credito == "170826"  # 173-178
    assert pago.carteira == "110"  # 021-023
    assert cancelado.codigo_ocorrencia == "07"


def test_ocorrencia_07_do_inter_e_cancelado_nao_liquidacao_parcial() -> None:
    """O código que colide de frente com a FEBRABAN.

    No padrão, ``07`` é *Liquidação por conta/parcial*; no Inter é **Cancelado**.
    Descrever um título cancelado como parcialmente liquidado inverte o sentido
    numa conciliação — e é exatamente o que aconteceria sem a sobreposição.
    """
    retorno = Retorno.ler(str(RETORNO_INTER))
    _, cancelado = retorno.registros
    assert retorno.descricao_ocorrencia(cancelado) == "Cancelado"
    assert descreve_ocorrencia("07", "400") == "Liquidação por conta/parcial"
    assert descreve_ocorrencia("07", "400", "077") == "Cancelado"


def test_sem_o_layout_proprio_o_inter_seria_lido_errado() -> None:
    """Mede o valor da entrada ``077`` em vez de só afirmar que ela existe.

    Lido com o layout de fallback, o mesmo arquivo devolve outro código de
    ocorrência — sem erro, sem aviso. É a forma de falha que este projeto trata
    como bug: saída plausível e errada.
    """
    linhas = _linhas_inter()
    correto = parse_cnab400(linhas, "077")[0]
    fallback = parse_cnab400(linhas, "999")[0]  # banco sem layout -> cai no do Itaú

    assert correto.codigo_ocorrencia == "06"
    assert fallback.codigo_ocorrencia != correto.codigo_ocorrencia
    assert fallback.data_vencimento != correto.data_vencimento


def test_o_layout_do_inter_cobre_as_25_posicoes_uteis() -> None:
    """Nenhuma faixa pode escapar das 400 posições nem se sobrepor ao sequencial."""
    layout = LAYOUTS_400["077"]
    for atributo, faixa in layout.items():
        inicio, fim = faixa[0], faixa[1]
        assert 0 <= inicio <= fim <= 399, f"{atributo}: faixa {faixa} fora do registro"
    assert layout["sequencial"] == (394, 399)
