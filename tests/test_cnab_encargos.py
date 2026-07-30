"""Encargos (juros/mora, multa, desconto 1º/2º/3º, IOF, abatimento) na remessa.

Diferente de ``test_cnab_remessa.py`` (que confere o arquivo inteiro byte a byte
com **todos os encargos zerados**), aqui montamos pagamentos com encargos reais
e conferimos **posição a posição** (fatias exatas do registro) que cada campo cai
no lugar certo, com o valor formatado esperado. Cobre as correções da Fase C:

- juros de mora percentual quando ``tipo_mora == "2"`` (Taxa Mensal, FEBRABAN);
- datas de multa/mora efetivas no CNAB 240 (usam o campo, não só o vencimento);
- 2º e 3º desconto efetivos no segmento R do CNAB 240;
- Sicoob 400: valor de mora ao dia + percentual de multa.
"""

from __future__ import annotations

from datetime import date

from pycobranca.cnab import Pagamento, RemessaBancoBrasil240, RemessaSicoob400
from pycobranca.contracts import pagamento_para_api, valida_contrato

_COMUM = dict(empresa_mae="Empresa Exemplo LTDA", documento_cedente="11222333000181")
_COMUM_240 = dict(
    **_COMUM,
    sequencial_remessa="1",
    data_geracao_fixa="23072026",
    hora_geracao_fixa="120000",
)
_COMUM_400 = dict(**_COMUM, data_geracao=date(2026, 7, 23))


def _pag_base(**extra) -> Pagamento:
    dados = dict(
        valor=199.90,
        data_vencimento=date(2026, 8, 15),
        data_emissao=date(2026, 7, 23),
        nosso_numero="12345678",
        numero="DOC0001",
        documento_sacado="52998224725",
        nome_sacado="Cliente Final da Silva",
        endereco_sacado="Rua das Flores, 100",
        bairro_sacado="Centro",
        cep_sacado="30110000",
        cidade_sacado="Belo Horizonte",
        uf_sacado="MG",
    )
    dados.update(extra)
    return Pagamento(**dados)


def _registros(arquivo: str) -> list[str]:
    return [linha for linha in arquivo.split("\r\n") if linha]


def _segmento(arquivo: str, letra: str) -> str:
    return next(ln for ln in _registros(arquivo) if len(ln) >= 14 and ln[13] == letra)


def _bb240(pag: Pagamento) -> str:
    remessa = RemessaBancoBrasil240(
        pagamentos=[pag],
        agencia="1234",
        conta_corrente="123456789012",
        convenio="1234567",
        variacao="019",
        carteira="17",
        **_COMUM_240,
    )
    return remessa.gera_arquivo()


def _mora_seg_p(seg_p: str, pag: Pagamento) -> dict[str, str]:
    """Extrai o bloco de juros de mora do segmento P ancorando na data de emissão
    (``DDMMYYYY``); logo após vêm ``tipo_mora`` (1) + data (8) + valor/percentual (15)."""
    i = seg_p.index(pag.data_emissao.strftime("%d%m%Y")) + 8
    return {"tipo": seg_p[i], "data": seg_p[i + 1 : i + 9], "valor": seg_p[i + 9 : i + 24]}


# Offsets fixos do segmento R (layout base, usado pelo BB): ocorrência(15-16),
# 2º desconto cod/data/valor (17..40), 3º desconto (41..64), multa cod/data/perc (65..88).
_R = {
    "d2_cod": (17, 18),
    "d2_data": (18, 26),
    "d2_valor": (26, 41),
    "d3_cod": (41, 42),
    "d3_data": (42, 50),
    "d3_valor": (50, 65),
    "multa_cod": (65, 66),
    "multa_data": (66, 74),
    "multa_perc": (74, 89),
}


def _r(seg_r: str, campo: str) -> str:
    a, b = _R[campo]
    return seg_r[a:b]


# --------------------------------------------------------------------------- #
# CNAB 240 — Segmento P: juros de mora
# --------------------------------------------------------------------------- #
def test_240_mora_valor_ao_dia() -> None:
    """tipo_mora=1 → valor ao dia (15 pos.); data de mora = campo informado."""
    pag = _pag_base(tipo_mora="1", valor_mora=1.53, data_mora=date(2026, 8, 20))
    mora = _mora_seg_p(_segmento(_bb240(pag), "P"), pag)
    assert mora["tipo"] == "1"
    assert mora["data"] == "20082026"  # data de mora efetiva (campo, não vencimento)
    assert mora["valor"] == "000000000000153"  # 1,53


def test_240_mora_percentual_taxa_mensal() -> None:
    """tipo_mora=2 → o campo de valor carrega o percentual_mora, NÃO o valor_mora."""
    pag = _pag_base(
        tipo_mora="2", valor_mora=9.99, percentual_mora=3.17, data_mora=date(2026, 8, 20)
    )
    mora = _mora_seg_p(_segmento(_bb240(pag), "P"), pag)
    assert mora["tipo"] == "2"
    assert mora["valor"] == "000000000000317"  # 3,17% (percentual)
    assert mora["valor"] != "000000000000999"  # valor_mora (9,99) não entra quando tipo=2


# --------------------------------------------------------------------------- #
# CNAB 240 — Segmento R: multa (data efetiva) + 2º/3º desconto
# --------------------------------------------------------------------------- #
def test_240_multa_data_efetiva() -> None:
    seg_r = _segmento(
        _bb240(_pag_base(codigo_multa="2", percentual_multa=2.71, data_multa=date(2026, 8, 16))),
        "R",
    )
    assert _r(seg_r, "multa_cod") == "2"
    assert _r(seg_r, "multa_data") == "16082026"  # data da multa efetiva (campo)
    assert _r(seg_r, "multa_perc") == "000000000000271"  # 2,71%


def test_240_segundo_e_terceiro_desconto() -> None:
    """Antes zerados fixos; agora vêm do Pagamento, em suas posições exatas."""
    seg_r = _segmento(
        _bb240(
            _pag_base(
                cod_segundo_desconto="1",
                valor_segundo_desconto=5.55,
                data_segundo_desconto=date(2026, 8, 10),
                cod_terceiro_desconto="2",
                valor_terceiro_desconto=3.33,
                data_terceiro_desconto=date(2026, 8, 12),
            )
        ),
        "R",
    )
    assert (_r(seg_r, "d2_cod"), _r(seg_r, "d2_data"), _r(seg_r, "d2_valor")) == (
        "1",
        "10082026",
        "000000000000555",
    )
    assert (_r(seg_r, "d3_cod"), _r(seg_r, "d3_data"), _r(seg_r, "d3_valor")) == (
        "2",
        "12082026",
        "000000000000333",
    )


def test_240_sem_encargos_zera_segmento_r() -> None:
    """Regressão: sem encargos, os slots de 2º/3º desconto e multa ficam zerados."""
    seg_r = _segmento(_bb240(_pag_base()), "R")
    assert seg_r[17:65] == "0" * 48  # 2º + 3º desconto (código+data+valor cada)
    assert _r(seg_r, "multa_cod") == "0"
    assert _r(seg_r, "multa_data") == "0" * 8
    assert _r(seg_r, "multa_perc") == "0" * 15


# --------------------------------------------------------------------------- #
# CNAB 400 — Sicoob: valor de mora ao dia + percentual de multa
# --------------------------------------------------------------------------- #
def test_400_sicoob_mora_valor_e_multa_percentual() -> None:
    pag = _pag_base(tipo_mora="1", valor_mora=1.53, codigo_multa="2", percentual_multa=2.47)
    remessa = RemessaSicoob400(
        pagamentos=[pag],
        agencia="1234",
        conta_corrente="12345678",
        convenio="123456789",
        digito_conta="5",
        carteira="01",
        sequencial_remessa="0000001",
        **_COMUM_400,
    )
    detalhe = next(ln for ln in _registros(remessa.gera_arquivo()) if ln.startswith("1"))
    # Âncora na emissão (DDMMYY) + "00" + "00" → mora(6) + multa(6).
    i = detalhe.index(pag.data_emissao.strftime("%d%m%y")) + 6
    assert detalhe[i : i + 4] == "0000"
    assert detalhe[i + 4 : i + 10] == "000153"  # valor de mora ao dia (1,53)
    assert detalhe[i + 10 : i + 16] == "000247"  # percentual de multa (2,47)


# --------------------------------------------------------------------------- #
# API / contrato — encargos serializados
# --------------------------------------------------------------------------- #
def test_api_encargos_serializados_e_validos() -> None:
    pag = _pag_base(
        tipo_mora="2",
        percentual_mora=3.17,
        data_mora=date(2026, 8, 20),
        codigo_multa="2",
        percentual_multa=2.71,
        data_multa=date(2026, 8, 16),
        cod_desconto="1",
        valor_desconto=10.0,
        data_desconto=date(2026, 8, 1),
        cod_segundo_desconto="1",
        valor_segundo_desconto=5.55,
        data_segundo_desconto=date(2026, 8, 10),
        valor_iof=1.25,
        valor_abatimento=2.5,
    )
    dados = pagamento_para_api(pag)
    valida_contrato(dados, "Pagamento")
    enc = dados["encargos"]
    assert enc["mora"] == {"tipo": "2", "percentual": 3.17, "data": "2026-08-20"}
    assert enc["multa"] == {"codigo": "2", "percentual": 2.71, "data": "2026-08-16"}
    assert enc["descontos"][0] == {"codigo": "1", "valor": 10.0, "data": "2026-08-01"}
    assert enc["descontos"][1] == {"codigo": "1", "valor": 5.55, "data": "2026-08-10"}
    assert enc["iof"] == 1.25
    assert enc["abatimento"] == 2.5
    valida_contrato(enc, "Encargos")


def test_api_sem_encargos_omite_campo() -> None:
    """Pagamento sem encargos → nenhuma chave ``encargos`` (payload inalterado)."""
    dados = pagamento_para_api(_pag_base())
    assert "encargos" not in dados
