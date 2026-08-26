"""Banco Safra (422) — boleto conferido contra o manual oficial.

Até aqui o Safra era sustentado por **um vetor de referência**: a saída da
implementação em Ruby com as mesmas entradas, em ``exemplos_boletos.py``. Dois
sistemas concordarem prova que a saída não é invenção de um só, mas não prova que
ambos estejam certos — os dois podem repetir o mesmo engano.

Este módulo acrescenta a evidência que faltava, vinda da **fonte primária**:

1. **O DV do nosso número contra os três exemplos resolvidos da seção 7.1**, entre
   eles o de resto zero. O número esperado vem do banco, não daqui.
2. **As posições do campo livre uma a uma**, contra a tabela da seção 7.2.2.

As duas verificações eram possíveis desde sempre; só faltava o manual. Elas
confirmaram a implementação existente sem exigir mudança nela.

Manual: *Leiaute de Arquivos — Cobrança CNAB 400*, Banco Safra.
"""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.bancos import Bancos, Safra
from pycobranca.exceptions import BoletoInvalido


def boleto_exemplo(**kwargs) -> Safra:
    dados = dict(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="0811",
        digito_agencia="1",
        conta="00053678",
        digito_conta="8",
        carteira="2",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    dados.update(kwargs)
    return Bancos.find("422")(**dados)


# --- 1. DV do nosso número: exemplos resolvidos do manual ---------------------


@pytest.mark.parametrize(
    ("sequencial", "dv"),
    [
        ("94550200", 1),  # soma 186, resto 10
        ("93199999", 5),  # soma 292, resto 6
        ("26173001", 1),  # soma 132, resto 0 — a borda
    ],
)
def test_dv_do_nosso_numero_contra_os_exemplos_do_manual(sequencial: str, dv: int) -> None:
    """Seção 7.1: módulo 11 com pesos 9→2, aplicados da esquerda para a direita.

    O manual fecha as bordas em duas linhas — *"Se na divisão o resto for 0, o
    dígito será 1"* e *"se for 1, o dígito será 0"* — e traz um exemplo que cai
    justamente no resto zero. Sem cobrir isso, o DV sairia errado em um a cada
    onze títulos, e o boleto ainda pareceria válido.
    """
    assert boleto_exemplo(nosso_numero=sequencial).dv_nosso_numero == dv


def test_nosso_numero_formatado_traz_o_dv_separado() -> None:
    assert boleto_exemplo().nosso_numero_formatado() == "12345678-9"


# --- 2. Campo livre: posições da seção 7.2.2 ---------------------------------


def test_campo_livre_posicao_a_posicao_do_manual() -> None:
    """Tabela *"Formatação do código de barras — cobrança registrada"*.

    O campo livre ocupa as posições 20 a 44 do código de barras, e o manual
    detalha cada faixa. Conferir o bloco inteiro de uma vez esconderia qual
    pedaço estaria errado.
    """
    codigo = boleto_exemplo().codigo_barras
    assert len(codigo) == 44

    def campo(de: int, ate: int) -> str:
        """Fatia pela numeração do manual (1-based, inclusiva nas duas pontas)."""
        return codigo[de - 1 : ate]

    assert campo(1, 3) == "422"  # banco beneficiário
    assert campo(4, 4) == "9"  # moeda: real
    assert campo(20, 20) == "7"  # dígito do Banco Safra
    assert campo(21, 25) == "08111"  # agência(4) + dígito
    assert campo(26, 34) == "000536788"  # conta(8) + dígito
    assert campo(35, 43) == "123456789"  # nosso número(8) + DV
    assert campo(44, 44) == "2"  # tipo de cobrança: registrada


def test_linha_digitavel_posicao_a_posicao_do_manual() -> None:
    """A seção 7.2.3 documenta a linha digitável **em tabela própria**.

    Não é o campo livre reordenado por regra geral: o manual descreve o corte
    campo a campo, e ali a agência aparece **partida** — os quatro primeiros
    dígitos na posição 6–9 e o último lá na 11, com o DV do primeiro campo no
    meio. Conferir contra essa tabela pega um erro que o round-trip com o código
    de barras não pegaria, porque os dois estariam errados juntos.
    """
    digitos = "".join(c for c in boleto_exemplo().linha_digitavel if c.isdigit())
    assert len(digitos) == 47

    def campo(de: int, ate: int) -> str:
        return digitos[de - 1 : ate]

    assert campo(1, 3) == "422"  # banco beneficiário
    assert campo(4, 4) == "9"  # moeda
    assert campo(5, 5) == "7"  # dígito do Banco Safra
    assert campo(6, 9) == "0811"  # 4 primeiros dígitos da agência
    assert campo(11, 11) == "1"  # último dígito da agência
    assert campo(12, 20) == "000536788"  # código do cliente
    assert campo(22, 30) == "123456789"  # nosso número + DV
    assert campo(31, 31) == "2"  # tipo de cobrança
    assert campo(34, 37) == "1539"  # fator de vencimento
    assert campo(38, 47) == "0000012750"  # valor


def test_tipo_de_cobranca_e_fixo_nas_duas_carteiras() -> None:
    """A posição 44 é *"Fixo o número 2 = Cobrança Registrada"* (seção 7.2.7).

    ``carteira`` distingue cobrança simples (1) de vinculada (2) **no arquivo
    CNAB**, não no código de barras. As duas produzem o mesmo campo livre, e é o
    que o manual manda — não é a carteira que vai ali.
    """
    simples = boleto_exemplo(carteira="1").campo_livre()
    vinculada = boleto_exemplo(carteira="2").campo_livre()
    assert simples == vinculada
    assert simples.endswith("2")


# --- Exigências de campo -----------------------------------------------------


@pytest.mark.parametrize("faltante", ["digito_agencia", "digito_conta"])
def test_boleto_exige_os_digitos_de_agencia_e_conta(faltante: str) -> None:
    """As duas posições entram no campo livre; sem elas o título aponta para outra conta.

    O manual reserva 5 posições para a agência e 9 para a conta, e a última de
    cada uma é o dígito. Assumir zero gravaria uma identidade que não é a do
    beneficiário — arquivo estruturalmente válido, destino errado.
    """
    boleto = boleto_exemplo(**{faltante: ""})
    with pytest.raises(BoletoInvalido):
        boleto.campo_livre()
