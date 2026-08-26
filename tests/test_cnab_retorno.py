"""Retorno CNAB (400 e 240) — parsing validado contra vetores de referência.

As fixtures ``.RET`` em ``tests/fixtures/retorno/`` são as mesmas usadas pela
de referência; os valores esperados abaixo foram extraídos de uma implementação de
referência (Ruby)
carregando cada arquivo e serializando os registros. O parser da PyCobrança
deve reproduzir os mesmos campos.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from pycobranca.cnab.retorno import Retorno, descreve_ocorrencia
from pycobranca.cnab.retorno.cnab240 import parse_cnab240
from pycobranca.cnab.retorno.cnab400 import LAYOUTS_400, parse_cnab400
from pycobranca.exceptions import LayoutGenerico

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
    with pytest.warns(LayoutGenerico):  # o fallback avisa; ler calado era o defeito
        fallback = parse_cnab400(linhas, "999")[0]

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


# --- Safra (422): as posições coincidem com o comum, menos onde importa -------
#
# Datas e valores do Safra caem onde a maioria dos bancos põe, mas o **nosso
# número ocupa 63-71 (nove posições)**, contra as oito do Itaú. No fallback o
# último dígito — que é o DV — é cortado sem erro nenhum, e a conciliação passa a
# comparar um número que não é o do título.
#
# A fixture foi montada pelas posições do manual (*Leiaute de Arquivos — Cobrança
# CNAB 400*, seção 6.2) — não há arquivo real do banco. Ela prova o mapeamento,
# não a realidade do arquivo que o Safra emite.

RETORNO_SAFRA = Path(__file__).parent / "fixtures" / "retorno_safra_cnab400.ret"


def _linhas_safra() -> list[str]:
    return RETORNO_SAFRA.read_text(encoding="ascii").replace("\r\n", "\n").rstrip("\n").split("\n")


def test_retorno_safra_le_os_campos_nas_posicoes_do_manual() -> None:
    retorno = Retorno.ler(str(RETORNO_SAFRA))
    assert retorno.codigo_banco == "422"
    assert len(retorno.registros) == 2  # header e trailer não viram registro

    liquidado, protestado = retorno.registros
    assert liquidado.nosso_numero == "945502001"  # 063-071, sequencial(8) + DV
    assert liquidado.codigo_ocorrencia == "06"  # 109-110
    assert liquidado.data_ocorrencia == "110926"  # 111-116
    assert liquidado.documento_numero == "2026-0007"  # 117-126 "seu número"
    assert liquidado.data_vencimento == "100926"  # 147-152
    assert liquidado.valor_titulo == "0000000123456"  # 153-165
    assert liquidado.valor_recebido == "0000000123456"  # 254-266
    assert liquidado.data_credito == "120926"  # 296-301
    assert liquidado.carteira == "1"  # 108
    assert protestado.codigo_ocorrencia == "40"


def test_ocorrencia_40_do_safra_e_protesto_nao_liquidacao() -> None:
    """O código que colide de frente com a FEBRABAN.

    No padrão, ``40`` é *Baixa por ter sido liquidado* — título **pago**. No Safra
    é baixa de título **protestado**. Descrever um protesto como liquidação
    inverte o sentido numa conciliação, e é o que aconteceria sem a sobreposição.
    """
    retorno = Retorno.ler(str(RETORNO_SAFRA))
    _, protestado = retorno.registros
    assert retorno.descricao_ocorrencia(protestado) == "Baixa de título protestado"
    assert descreve_ocorrencia("40", "400") == "Baixa por ter sido liquidado"
    assert descreve_ocorrencia("40", "400", "422") == "Baixa de título protestado"


def test_sem_o_layout_proprio_o_safra_perderia_o_dv_do_nosso_numero() -> None:
    """Mede o valor da entrada ``422`` em vez de só afirmar que ela existe.

    O fallback do Itaú lê oito posições onde o Safra grava nove: o número sai sem
    o dígito verificador, sem erro e sem aviso. É a forma de falha que este
    projeto trata como bug — saída plausível e errada.
    """
    linhas = _linhas_safra()
    correto = parse_cnab400(linhas, "422")[0]
    with pytest.warns(LayoutGenerico):  # o fallback avisa; ler calado era o defeito
        fallback = parse_cnab400(linhas, "999")[0]

    assert correto.nosso_numero == "945502001"
    assert fallback.nosso_numero == "94550200"  # o DV foi cortado
    assert correto.nosso_numero.startswith(fallback.nosso_numero)


def test_o_layout_do_safra_cabe_nas_400_posicoes() -> None:
    """Nenhuma faixa pode escapar do registro nem inverter as pontas."""
    for atributo, faixa in LAYOUTS_400["422"].items():
        inicio, fim = faixa[0], faixa[1]
        assert 0 <= inicio <= fim <= 399, f"{atributo}: faixa {faixa} fora do registro"


# --- O fallback deixou de ser silencioso -------------------------------------
#
# Sem mapa próprio, ``parse_cnab400`` e ``parse_cnab240`` leem o arquivo inteiro
# com um layout genérico e **não levantam nada**. O resultado é plausível e
# errado — a forma de falha que este projeto trata como bug. O aviso não muda o
# comportamento: é o sinal que faltava para quem recebe o arquivo.


def test_o_fallback_do_400_avisa_em_vez_de_ler_calado() -> None:
    linhas = _linhas_safra()
    with pytest.warns(LayoutGenerico, match="999"):
        parse_cnab400(linhas, "999")


def test_o_fallback_do_240_avisa_em_vez_de_ler_calado() -> None:
    linhas = (FIXTURES / "CNAB240SICOOB.RET").read_text(encoding="latin-1").splitlines()
    with pytest.warns(LayoutGenerico, match="999"):
        parse_cnab240(linhas, "999")


@pytest.mark.parametrize("banco", ["341", "077", "422"])
def test_banco_com_layout_proprio_nao_avisa(banco: str) -> None:
    """O aviso tem de ser específico: se disparasse sempre, viraria ruído."""
    linhas = _linhas_safra()
    with warnings.catch_warnings():
        warnings.simplefilter("error", LayoutGenerico)
        parse_cnab400(linhas, banco)


def test_o_aviso_pode_virar_erro() -> None:
    """Quem processa retorno em lote costuma preferir falhar a seguir adiante."""
    linhas = _linhas_safra()
    with warnings.catch_warnings():
        warnings.simplefilter("error", LayoutGenerico)
        with pytest.raises(LayoutGenerico):
            parse_cnab400(linhas, "999")


# --- Sicredi (748): retorno 400 sobre arquivo real do banco -------------------
#
# Evidência mais forte do projeto: **manual oficial** (CNAB 400 v2.4, seção 9.2)
# mais um **arquivo de retorno real**, de terceiros, em ``externos/``.

RETORNO_SICREDI = (
    Path(__file__).parent / "fixtures" / "retorno" / "externos" / "sicredi_cnab400.ret"
)


def _linhas_sicredi() -> list[str]:
    bruto = RETORNO_SICREDI.read_bytes().decode("latin-1")
    sep = "\r\n" if "\r\n" in bruto else "\n"
    return [linha for linha in bruto.split(sep) if linha.strip()]


def test_retorno_sicredi_le_o_nosso_numero_das_quinze_posicoes() -> None:
    """Seção 9.2: nosso número em **048-062**, quinze posições.

    O layout de reserva lê 63-70, que no Sicredi cai no meio do *filler* de
    063-108. O número real deste arquivo é ``00000162000015``.
    """
    retorno = Retorno.ler(RETORNO_SICREDI)
    assert retorno.codigo_banco == "748"
    registro = retorno.registros[0]
    assert registro.nosso_numero == "00000162000015"
    assert registro.codigo_ocorrencia == "02"  # 109-110
    assert registro.data_vencimento == "111116"  # 147-152
    assert registro.valor_titulo == "0000000010000"  # 153-165
    assert registro.valor_recebido == "0000000010000"  # 254-266


def test_sem_o_layout_proprio_o_sicredi_devolvia_zeros_de_filler() -> None:
    """Mede o valor da entrada ``748`` num arquivo **real** do banco.

    O fallback não devolvia lixo evidente: devolvia ``00000000`` — zeros lidos de
    espaço em branco, com toda a aparência de um nosso número válido. Uma
    conciliação compararia isso contra os títulos emitidos e não casaria nenhum,
    sem nunca dizer por quê.
    """
    linhas = _linhas_sicredi()
    correto = parse_cnab400(linhas, "748")[0]
    with pytest.warns(LayoutGenerico):
        fallback = parse_cnab400(linhas, "999")[0]

    assert correto.nosso_numero == "00000162000015"
    assert fallback.nosso_numero == "00000000"
    assert not fallback.nosso_numero.strip("0")  # só zeros: plausível e vazio


def test_a_data_de_credito_do_sicredi_tem_oito_posicoes() -> None:
    """329-336 em ``AAAAMMDD`` — o resto do layout usa ``DDMMAA`` em seis.

    Fica crua, como vem: converter aqui esconderia a diferença de quem lê.
    """
    registro = Retorno.ler(RETORNO_SICREDI).registros[0]
    assert len(registro.data_credito) == 8


def test_o_layout_do_sicredi_cabe_nas_400_posicoes() -> None:
    for atributo, faixa in LAYOUTS_400["748"].items():
        inicio, fim = faixa[0], faixa[1]
        assert 0 <= inicio <= fim <= 399, f"{atributo}: faixa {faixa} fora do registro"


# --- Sicoob (756): retorno 400 pelo layout oficial do portal -----------------
#
# Eu havia concluído que o Sicoob não tinha CNAB 400 de cobrança, porque o
# validador do banco só oferece CNAB240. **Estava errado**: o portal publica
# ``Layout_Cobranca_CNAB400.xls`` (19/05/2025), com as abas de remessa e retorno.
# A conclusão vinha de inferência sobre a ausência no validador, não de fonte —
# e a fonte existia.

RETORNO_SICOOB = Path(__file__).parent / "fixtures" / "retorno_sicoob_cnab400.ret"


def _linhas_sicoob() -> list[str]:
    return RETORNO_SICOOB.read_text(encoding="ascii").replace("\r\n", "\n").rstrip("\n").split("\n")


def test_retorno_sicoob_400_le_o_nosso_numero_com_o_dv() -> None:
    """Aba 04 do XLS: nosso número em **63-73** e o DV em **74**, doze posições."""
    retorno = Retorno.ler(RETORNO_SICOOB)
    assert retorno.codigo_banco == "756"
    liquidado, rejeitado = retorno.registros

    assert liquidado.nosso_numero == "000000002461"  # 063-074, número + DV
    assert liquidado.codigo_ocorrencia == "06"  # 109-110 comando/movimento
    assert liquidado.data_ocorrencia == "160826"  # 111-116
    assert liquidado.documento_numero == "2026-0009"  # 117-126
    assert liquidado.data_vencimento == "150826"  # 147-152
    assert liquidado.valor_titulo == "0000000012750"  # 153-165
    assert liquidado.data_credito == "170826"  # 176-181, não 296-301
    assert liquidado.carteira == "01"  # 107-108, duas posições
    assert rejeitado.codigo_ocorrencia == "03"
    assert rejeitado.motivo_ocorrencia == "05"  # 081-082 código de baixa/recusa


def test_sem_o_layout_proprio_o_sicoob_perdia_o_dv_e_a_data_de_credito() -> None:
    """Mede as duas diferenças que mais doem numa conciliação.

    O layout de reserva lê oito posições de nosso número onde o Sicoob grava
    doze: somem três dígitos **e** o DV. E lê a data de crédito em 296-301,
    enquanto o Sicoob a grava em 176-181 — devolvia zeros, indistinguível de
    "ainda não creditado".
    """
    linhas = _linhas_sicoob()
    correto = parse_cnab400(linhas, "756")[0]
    with pytest.warns(LayoutGenerico):
        fallback = parse_cnab400(linhas, "999")[0]

    assert correto.nosso_numero == "000000002461"
    assert fallback.nosso_numero == "00000000"
    assert correto.data_credito == "170826"
    assert fallback.data_credito == "000000"


def test_o_layout_do_sicoob_400_cabe_nas_400_posicoes() -> None:
    for atributo, faixa in LAYOUTS_400["756"].items():
        inicio, fim = faixa[0], faixa[1]
        assert 0 <= inicio <= fim <= 399, f"{atributo}: faixa {faixa} fora do registro"
