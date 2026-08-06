"""Encargos validados por um **sistema independente do gerador**.

Sem reusar o código de geração da PyCobrança, um **decodificador FEBRABAN**
lê a remessa por **posições absolutas do padrão** e reconstrói juros/mora,
multa e descontos (valores e datas). O teste confere o *round-trip*
``encode → arquivo → decode`` — os números que saem são exatamente os que
entraram, lidos como faria o intake de um banco.

Complementa `test_cnab_encargos.py` (que confere a saída do próprio gerador):
aqui a leitura é feita por outro caminho de código, sobre posições do manual,
e cruzada em **três bancos 240** (BB, Caixa, Santander) mais o **Sicoob 400**.
Reaproveita ainda o validador estrutural independente (`test_cnab_estrutura`)
para confirmar que o arquivo **com encargos** continua ACEITO por "outro sistema".
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

# Validador estrutural independente (mesmo diretório de testes, no sys.path).
from test_cnab_estrutura import _valida_240, _valida_400

from pycobranca.cnab import (
    Pagamento,
    RemessaBancoBrasil240,
    RemessaCaixa240,
    RemessaSantander240,
    RemessaSicoob400,
)


# --------------------------------------------------------------------------- #
# Decodificador FEBRABAN independente (posições ABSOLUTAS, base 0)
# --------------------------------------------------------------------------- #
def _val(campo: str) -> Decimal:
    """Valor CNAB (``9(n)V99``, sem ponto) → Decimal em reais/percentual."""
    return Decimal(int(campo)) / 100


def _dat(campo: str) -> date | None:
    """Data ``DDMMYYYY`` → ``date`` (ou ``None`` quando zerada)."""
    return None if set(campo) <= {"0"} else datetime.strptime(campo, "%d%m%Y").date()


def _decode_p(p: str) -> dict:
    """Segmento P (240): juros de mora + 1º desconto + IOF + abatimento."""
    return {
        "cod_mora": p[117],
        "data_mora": _dat(p[118:126]),
        "mora": _val(p[126:141]),
        "cod_desc1": p[141],
        "data_desc1": _dat(p[142:150]),
        "desc1": _val(p[150:165]),
        "iof": _val(p[165:180]),
        "abatimento": _val(p[180:195]),
    }


def _decode_r(r: str) -> dict:
    """Segmento R (240): 2º e 3º desconto + multa."""
    return {
        "cod_desc2": r[17],
        "data_desc2": _dat(r[18:26]),
        "desc2": _val(r[26:41]),
        "cod_desc3": r[41],
        "data_desc3": _dat(r[42:50]),
        "desc3": _val(r[50:65]),
        "cod_multa": r[65],
        "data_multa": _dat(r[66:74]),
        "multa": _val(r[74:89]),
    }


def _dec(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"))


# --------------------------------------------------------------------------- #
# Fixture de encargos e construtores por banco
# --------------------------------------------------------------------------- #
def _pag_encargos() -> Pagamento:
    return Pagamento(
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
        tipo_mora="1",
        valor_mora=1.53,
        data_mora=date(2026, 8, 20),
        cod_desconto="1",
        valor_desconto=10.00,
        data_desconto=date(2026, 8, 1),
        valor_iof=1.25,
        valor_abatimento=2.50,
        codigo_multa="2",
        percentual_multa=2.71,
        data_multa=date(2026, 8, 16),
        cod_segundo_desconto="1",
        valor_segundo_desconto=5.55,
        data_segundo_desconto=date(2026, 8, 10),
        cod_terceiro_desconto="2",
        valor_terceiro_desconto=3.33,
        data_terceiro_desconto=date(2026, 8, 12),
    )


_COMUM_240 = dict(
    empresa_mae="Empresa Exemplo LTDA",
    documento_cedente="11222333000181",
    sequencial_remessa="1",
    data_geracao_fixa="23072026",
    hora_geracao_fixa="120000",
)


def _remessa_240(banco: str, pag: Pagamento):
    if banco == "banco_brasil":
        return RemessaBancoBrasil240(
            pagamentos=[pag],
            agencia="1234",
            conta_corrente="123456789012",
            convenio="1234567",
            variacao="019",
            carteira="17",
            **_COMUM_240,
        )
    if banco == "caixa":
        return RemessaCaixa240(
            pagamentos=[pag],
            agencia="1234",
            digito_agencia="5",
            convenio="123456",
            versao_aplicativo="1234",
            conta_corrente="1234567",
            **_COMUM_240,
        )
    return RemessaSantander240(
        pagamentos=[pag],
        codigo_transmissao="123456789012345",
        agencia="1234",
        conta_corrente="123456789",
        digito_conta="5",
        **_COMUM_240,
    )


def _registros(arquivo: str) -> list[str]:
    return [linha for linha in arquivo.split("\r\n") if linha]


# --------------------------------------------------------------------------- #
# CNAB 240 — round-trip por decodificador independente (3 bancos)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("banco", ["banco_brasil", "caixa", "santander"])
def test_240_encargos_roundtrip_decodificador_independente(banco: str) -> None:
    pag = _pag_encargos()
    linhas = _registros(_remessa_240(banco, pag).gera_arquivo())

    # 1) "Outro sistema" aceita o arquivo com encargos (estrutura FEBRABAN).
    _valida_240(linhas)

    # 2) Round-trip dos valores lidos por posição absoluta.
    seg_p = next(ln for ln in linhas if ln[13] == "P")
    seg_r = next(ln for ln in linhas if ln[13] == "R")
    p, r = _decode_p(seg_p), _decode_r(seg_r)

    # Caixa emite a data de mora/multa como vencimento+1 quando o campo é dado;
    # aqui o campo foi informado, então a data lida deve ser exatamente o campo.
    assert p["cod_mora"] == "1"
    assert p["data_mora"] == pag.data_mora
    assert p["mora"] == _dec(pag.valor_mora)
    assert (p["cod_desc1"], p["data_desc1"], p["desc1"]) == (
        "1",
        pag.data_desconto,
        _dec(pag.valor_desconto),
    )
    assert p["iof"] == _dec(pag.valor_iof)
    assert p["abatimento"] == _dec(pag.valor_abatimento)

    assert (r["cod_desc2"], r["data_desc2"], r["desc2"]) == (
        "1",
        pag.data_segundo_desconto,
        _dec(pag.valor_segundo_desconto),
    )
    assert (r["cod_desc3"], r["data_desc3"], r["desc3"]) == (
        "2",
        pag.data_terceiro_desconto,
        _dec(pag.valor_terceiro_desconto),
    )
    assert (r["cod_multa"], r["data_multa"], r["multa"]) == (
        "2",
        pag.data_multa,
        _dec(pag.percentual_multa),
    )


def test_240_mora_percentual_roundtrip() -> None:
    """tipo_mora=2 → o decodificador lê o percentual no campo de mora."""
    pag = _pag_encargos()
    pag.tipo_mora = "2"
    pag.percentual_mora = 3.17
    linhas = _registros(_remessa_240("banco_brasil", pag).gera_arquivo())
    p = _decode_p(next(ln for ln in linhas if ln[13] == "P"))
    assert p["cod_mora"] == "2"
    assert p["mora"] == _dec(pag.percentual_mora)  # 3,17% (não o valor_mora)


# --------------------------------------------------------------------------- #
# CNAB 400 — Sicoob: round-trip por posições absolutas
# --------------------------------------------------------------------------- #
def test_400_sicoob_encargos_roundtrip() -> None:
    pag = _pag_encargos()
    remessa = RemessaSicoob400(
        pagamentos=[pag],
        agencia="1234",
        conta_corrente="12345678",
        convenio="123456789",
        digito_conta="5",
        carteira="01",
        sequencial_remessa="0000001",
        empresa_mae="Empresa Exemplo LTDA",
        documento_cedente="11222333000181",
        data_geracao=date(2026, 7, 23),
    )
    linhas = _registros(remessa.gera_arquivo())

    _valida_400(linhas)  # "outro sistema" aceita o arquivo com encargos

    detalhe = next(ln for ln in linhas if ln.startswith("1"))
    # Sicoob 400: mora ao dia em 161-166, multa (%) em 167-172 (1-based).
    assert _val(detalhe[160:166]) == _dec(pag.valor_mora)
    assert _val(detalhe[166:172]) == _dec(pag.percentual_multa)
