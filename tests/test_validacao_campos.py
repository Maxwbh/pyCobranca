"""Validação de tamanho/conjunto de campos (boleto) e coerência de encargos (CNAB).

Cobre o contrato de erros: :class:`BoletoInvalido` carrega ``.erros`` (lista
estruturada) e ``str(exc)`` traz as mensagens unidas — o que um consumidor REST
usa para tratar cada violação.
"""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.bancos import BRB, Bradesco, Itau
from pycobranca.cnab import Pagamento
from pycobranca.exceptions import BoletoInvalido


def _itau(**kwargs) -> Itau:
    base = dict(
        valor="100.00",
        cedente="Empresa LTDA",
        agencia="1234",
        conta="56789",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
    )
    base.update(kwargs)
    return Itau(**base)


# ---- contrato de erros estruturado ----


def test_boleto_invalido_carrega_lista_de_erros() -> None:
    with pytest.raises(BoletoInvalido) as exc:
        _ = _itau(agencia="12345", conta="123456").codigo_barras
    erros = exc.value.erros
    assert isinstance(erros, list)
    assert any("agência" in e for e in erros)
    assert any("conta" in e for e in erros)
    # str(exc) une os itens
    assert "; " in str(exc.value)


def test_boleto_invalido_aceita_string_unica() -> None:
    exc = BoletoInvalido("erro único")
    assert exc.erros == ["erro único"]
    assert str(exc) == "erro único"


# ---- boleto: tamanho máximo (trava o formato) ----


def test_itau_agencia_acima_do_maximo() -> None:
    with pytest.raises(BoletoInvalido, match="agência deve ter no máximo 4"):
        _ = _itau(agencia="12345").codigo_barras


def test_itau_nosso_numero_acima_do_maximo() -> None:
    with pytest.raises(BoletoInvalido, match="nosso número deve ter no máximo 8"):
        _ = _itau(nosso_numero="123456789").codigo_barras


def test_bradesco_nosso_numero_acima_do_maximo() -> None:
    with pytest.raises(BoletoInvalido, match="nosso número deve ter no máximo 11"):
        _ = Bradesco(
            valor="100.00",
            cedente="X",
            agencia="1234",
            conta="1234567",
            carteira="09",
            nosso_numero="123456789012",
            data_vencimento=date(2026, 8, 15),
        ).codigo_barras


# ---- boleto: tamanho mínimo (campo vazio) ----


def test_itau_nosso_numero_vazio() -> None:
    with pytest.raises(BoletoInvalido, match="nosso número deve ter no mínimo 1"):
        _ = _itau(nosso_numero="").codigo_barras


# ---- boleto: agência do BRB é 3 dígitos (não 4) ----


def test_brb_agencia_maximo_3() -> None:
    with pytest.raises(BoletoInvalido, match="agência deve ter no máximo 3"):
        _ = BRB(
            valor="100.00",
            cedente="X",
            agencia="1234",
            conta="1234567",
            carteira="1",
            nosso_numero="123456",
            incremento="123",
            data_vencimento=date(2026, 8, 15),
        ).codigo_barras


# ---- boleto: conjunto válido de carteira ----


def test_itau_carteira_fora_do_conjunto() -> None:
    with pytest.raises(BoletoInvalido, match="carteira .* não suportada"):
        _ = _itau(carteira="999").codigo_barras


def test_itau_boleto_valido_nao_levanta() -> None:
    # não deve levantar
    assert len(_itau().codigo_barras) == 44


# ---- CNAB: coerência de encargos ----


def _pagamento(**kwargs) -> Pagamento:
    base = dict(
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        valor=199.90,
        documento_sacado="12345678909",
        nome_sacado="Cliente",
        endereco_sacado="Rua X, 1",
        cep_sacado="01001000",
    )
    base.update(kwargs)
    return Pagamento(**base)


def test_pagamento_valor_deve_ser_positivo() -> None:
    with pytest.raises(BoletoInvalido, match="valor deve ser positivo"):
        _pagamento(valor=0.0).validar()


def test_pagamento_mora_taxa_mensal_exige_percentual() -> None:
    with pytest.raises(BoletoInvalido, match="percentual_mora"):
        _pagamento(tipo_mora="2", percentual_mora=0.0).validar()


def test_pagamento_mora_valor_dia_exige_valor() -> None:
    with pytest.raises(BoletoInvalido, match="valor_mora"):
        _pagamento(tipo_mora="1", valor_mora=0.0).validar()


def test_pagamento_multa_exige_percentual() -> None:
    with pytest.raises(BoletoInvalido, match="percentual_multa"):
        _pagamento(codigo_multa="2", percentual_multa=0.0).validar()


def test_pagamento_desconto_exige_valor_e_data() -> None:
    with pytest.raises(BoletoInvalido) as exc:
        _pagamento(cod_desconto="1", valor_desconto=0.0, data_desconto=None).validar()
    assert any("1º desconto" in e and "valor" in e for e in exc.value.erros)
    assert any("1º desconto" in e and "data" in e for e in exc.value.erros)


def test_pagamento_valores_negativos() -> None:
    with pytest.raises(BoletoInvalido, match="valor_iof não pode ser negativo"):
        _pagamento(valor_iof=-1.0).validar()


def test_pagamento_uf_invalida() -> None:
    with pytest.raises(BoletoInvalido, match="uf_sacado deve ter 2 letras"):
        _pagamento(uf_sacado="SPO").validar()


def test_pagamento_coerente_nao_levanta() -> None:
    # encargos coerentes: não deve levantar
    _pagamento(
        tipo_mora="2",
        percentual_mora=3.17,
        codigo_multa="2",
        percentual_multa=2.0,
        cod_desconto="1",
        valor_desconto=10.0,
        data_desconto=date(2026, 8, 1),
    ).validar()
