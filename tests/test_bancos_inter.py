"""Banco Inter (077) — campo livre da carteira 110, contra o manual oficial.

**A natureza da evidência aqui é diferente da dos outros bancos.** Os 18 bancos de
``exemplos_boletos.py`` têm vetor de uma implementação de produção independente: dois
sistemas concordarem não prova que ambos estejam certos, mas prova que a saída não é
invenção de um só. O Inter não está em nenhuma implementação aberta conhecida, então
esse cruzamento não existe.

O que sustenta esta implementação, em ordem de força:

1. **O DV do nosso número é conferido contra o exemplo resolvido do manual**
   (seção 8.3: ``00011100004309540`` → soma 29, resto 9, DV 1). Isso é verificação
   externa de verdade — o número esperado vem do banco, não daqui.
2. **As posições do campo livre são conferidas uma a uma** contra a tabela da seção
   7.1.3. Estrutural, mas ancorada na fonte primária.
3. **A montagem do código de barras e da linha digitável** é padrão FEBRABAN, a mesma
   já exercida pelos 18 bancos e pelo verificador independente de
   ``test_validacao_externa.py``.

O que **não** existe: um boleto real do Inter na carteira 110. Por isso o código de
barras congelado abaixo é **guarda de regressão, não paridade externa** — ele prende a
saída de hoje, e prenderia igual se estivesse errada. Um boleto real fecharia essa
lacuna; até lá, a distinção fica dita.

Manual: *CNAB 400 — Emissão boletos de cobrança*, Inter, V9, 06/07/2026.
"""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.bancos import Bancos, Inter
from pycobranca.exceptions import BoletoInvalido


def boleto_exemplo(**kwargs) -> Inter:
    dados = dict(
        valor="1234.56",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11.222.333/0001-81",
        agencia="0001",
        conta="123456",
        carteira="110",
        convenio="1234567",  # número da operação
        nosso_numero="0004309540",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="529.982.247-25",
    )
    dados.update(kwargs)
    return Inter(**dados)


# --- registro ----------------------------------------------------------------


def test_registro_de_bancos() -> None:
    assert Bancos.find("077") is Inter
    assert Bancos.find(77) is Inter  # aceita sem zeros à esquerda
    assert Inter in Bancos.todos()
    assert Inter not in Bancos.com_pix()


# --- o único ponto com número esperado vindo do banco ------------------------


def test_dv_do_nosso_numero_bate_com_o_exemplo_do_manual() -> None:
    """Seção 7.3: agência 0001, carteira 110, nosso número 0004309540 → DV 1.

    Módulo 10 sobre os 17 dígitos ``0001`` + ``110`` + nosso número sem DV. O manual
    mostra a conta inteira: soma 29, resto 9, DV = 10 − 9 = 1.
    """
    assert boleto_exemplo(nosso_numero="0004309540").dac_nosso_numero == 1


def test_o_dv_entra_no_nosso_numero_com_11_posicoes() -> None:
    """O manual (seção 8) exige os 11 dígitos: nosso número + DV."""
    b = boleto_exemplo(nosso_numero="0004309540")
    assert b.nosso_numero_formatado() == "0004309540-1"
    assert b.campo_livre()[14:25] == "00043095401"


# --- campo livre, posição a posição (seção 8.1.3) ----------------------------


def test_campo_livre_posicao_a_posicao() -> None:
    """Agência(4) + carteira(3) + operação(7) + nosso número com DV(11) = 25."""
    cl = boleto_exemplo().campo_livre()
    assert len(cl) == 25 and cl.isdigit()
    assert cl[0:4] == "0001"  # 001–004 agência sem DV
    assert cl[4:7] == "110"  # 005–007 carteira
    assert cl[7:14] == "1234567"  # 008–014 número da operação
    assert cl[14:25] == "00043095401"  # 015–025 nosso número + DV


def test_campo_livre_ocupa_as_25_ultimas_posicoes_do_codigo_de_barras() -> None:
    b = boleto_exemplo()
    assert b.codigo_barras[19:] == b.campo_livre()


@pytest.mark.parametrize(
    ("campo", "valor", "fatia", "esperado"),
    [
        ("convenio", "42", slice(7, 14), "0000042"),
        ("nosso_numero", "7", slice(14, 24), "0000000007"),
        ("agencia", "1", slice(0, 4), "0001"),
    ],
)
def test_zeros_a_esquerda_sao_regra_e_nao_formatacao(campo, valor, fatia, esperado) -> None:
    """O preenchimento entra no campo livre e no DV — simplificá-lo muda o título."""
    assert boleto_exemplo(**{campo: valor}).campo_livre()[fatia] == esperado


def test_agencia_omitida_usa_a_agencia_unica_do_inter() -> None:
    """Banco digital, agência única: exigir ``0001`` de todo chamador seria ruído."""
    omitida = boleto_exemplo(agencia="")
    explicita = boleto_exemplo(agencia="0001")
    assert omitida._agencia4 == "0001"
    assert omitida.codigo_barras == explicita.codigo_barras


# --- a 112 não pode entrar ---------------------------------------------------


def test_apenas_a_carteira_110_e_aceita() -> None:
    """A 112 é numerada pelo banco: o nosso número só existe no arquivo retorno.

    Aceitá-la produziria um título que imprime, passa em conferência estrutural e
    carrega um nosso número que o Inter nunca emitiu. O corte é na entrada.
    """
    assert Inter.carteiras == ("110",)
    with pytest.raises(BoletoInvalido) as erro:
        boleto_exemplo(carteira="112").validar()
    assert any("carteira" in m for m in erro.value.erros)


def test_a_carteira_entra_no_dac_do_nosso_numero() -> None:
    """A carteira compõe o DV, então não é rótulo: trocá-la muda o dígito.

    Prende a diferença contra a 112 pelo comportamento, e não pela constante — se um
    dia a 112 for aceita, este número tem de ser reavaliado, não herdado.
    """
    from pycobranca.core.dv import modulo10

    assert modulo10("0001" + "110" + "0004309540") == 1
    assert modulo10("0001" + "112" + "0004309540") == 7


# --- guarda de regressão (não é paridade externa) ----------------------------

#: Saída atual para os dados de ``boleto_exemplo``. Congelada para que uma mudança
#: acidental apareça — **não** é vetor de implementação independente; ver o docstring
#: do módulo.
CODIGO_BARRAS = "07794153900001234560001110123456700043095401"
LINHA_DIGITAVEL = "07790.00116 10123.456708 00430.954016 4 15390000123456"


def test_saida_congelada() -> None:
    b = boleto_exemplo()
    assert b.codigo_barras == CODIGO_BARRAS
    assert b.linha_digitavel == LINHA_DIGITAVEL


def test_estrutura_do_codigo_de_barras() -> None:
    cb = boleto_exemplo().codigo_barras
    assert len(cb) == 44 and cb.isdigit()
    assert cb.startswith("0779")  # banco + moeda
    fator = 1000 + (date(2026, 8, 15) - date(2025, 2, 22)).days
    assert cb[5:9] == f"{fator:04d}"
    assert cb[9:19] == "0000123456"  # R$ 1.234,56


def test_digito_do_banco() -> None:
    """``077-9`` — módulo 11 sobre o código do banco, como impresso no boleto."""
    assert Inter.digito_banco == "9"


# --- render ------------------------------------------------------------------


def test_boleto_para_pdf_reportlab() -> None:
    pytest.importorskip("reportlab")
    from pycobranca.render import render_boleto_pdf

    ctx = boleto_exemplo().contexto_render()
    assert ctx["codigo_barras"] == CODIGO_BARRAS
    assert render_boleto_pdf(ctx, modelo="moderno").startswith(b"%PDF")
