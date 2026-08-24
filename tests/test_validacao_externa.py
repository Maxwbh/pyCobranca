"""Validação externa: cada boleto conferido por um verificador FEBRABAN independente.

Estes testes **não usam o código do núcleo** (``pycobranca.core.dv``,
``pycobranca.boleto`` etc.). Eles reimplementam, do zero, exatamente o que um
sistema externo faz ao **receber** um boleto — um app de banco lendo a linha
digitável, um PSP conferindo o código de barras, um leitor de arquivo de
pagamento. Se a PyCobrança e este verificador independente concordam, o título
seria aceito por qualquer sistema conforme à FEBRABAN.

Para cada um dos 18 bancos, a partir do que a PyCobrança emitiu, verificamos:

1. o código de barras tem 44 dígitos e o **DV geral (módulo 11)** confere;
2. a linha digitável tem 47 dígitos e os **três DVs de campo (módulo 10)** conferem;
3. a linha digitável **reconstrói exatamente** o código de barras (round-trip);
4. o **fator de vencimento** decodifica de volta à data de vencimento do título;
5. o **valor** embutido bate com o valor do título;
6. **banco** e **moeda** (Real = 9) batem.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from exemplos_boletos import EXEMPLOS

from pycobranca.bancos.base import BancoBase

# --- Verificador independente (reimplementação limpa das regras FEBRABAN) -----

BASE_FATOR = date(1997, 10, 7)
ROLLOVER_FATOR = date(2025, 2, 22)


def _so_digitos(texto: str) -> str:
    return "".join(c for c in texto if c.isdigit())


def _dv_modulo10(campo: str) -> int:
    """DV módulo 10 de um campo da linha digitável (pesos 2,1,2,1… da direita)."""
    total = 0
    for posicao, digito in enumerate(reversed(campo)):
        parcela = int(digito) * (2 if posicao % 2 == 0 else 1)
        total += parcela if parcela < 10 else parcela - 9  # soma dos algarismos
    return (10 - total % 10) % 10


def _dv_geral_modulo11(codigo_sem_dv: str) -> int:
    """DV geral (posição 5) do código de barras: módulo 11, pesos 2..9 cíclicos."""
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for posicao, digito in enumerate(reversed(codigo_sem_dv)):
        total += int(digito) * pesos[posicao % len(pesos)]
    dv = 11 - total % 11
    return 1 if dv in (0, 10, 11) else dv


def _fator_esperado(vencimento: date) -> int:
    """Fator de vencimento FEBRABAN (com reinício em 1000 a partir de 22/02/2025)."""
    if vencimento < ROLLOVER_FATOR:
        return (vencimento - BASE_FATOR).days
    return 1000 + (vencimento - ROLLOVER_FATOR).days


def _data_do_fator(fator: int) -> date:
    """Decodifica o fator de volta para a data (janela moderna, pós-reinício)."""
    return ROLLOVER_FATOR + timedelta(days=fator - 1000)


def _reconstroi_codigo_barras(linha_47: str) -> str:
    """Remonta as 44 posições do código de barras a partir da linha digitável (47)."""
    banco = linha_47[0:3]
    moeda = linha_47[3]
    livre1 = linha_47[4:9]
    livre2 = linha_47[10:20]
    livre3 = linha_47[21:31]
    dv_geral = linha_47[32]
    fator_valor = linha_47[33:47]
    return f"{banco}{moeda}{dv_geral}{fator_valor}{livre1}{livre2}{livre3}"


def _confere(nome: str, boleto: BancoBase) -> None:
    """Roda o verificador independente sobre um título já emitido."""
    cb = boleto.codigo_barras
    linha = _so_digitos(boleto.linha_digitavel)

    # 1) estrutura + DV geral do código de barras
    assert len(cb) == 44 and cb.isdigit(), f"{nome}: código de barras não tem 44 dígitos"
    sem_dv = cb[0:4] + cb[5:44]  # 43 posições (remove o DV da posição 5)
    assert _dv_geral_modulo11(sem_dv) == int(cb[4]), f"{nome}: DV geral (módulo 11) inválido"

    # 2) estrutura + DVs de campo (módulo 10) da linha digitável
    assert len(linha) == 47, f"{nome}: linha digitável não tem 47 dígitos"
    assert _dv_modulo10(linha[0:9]) == int(linha[9]), f"{nome}: DV do campo 1 inválido"
    assert _dv_modulo10(linha[10:20]) == int(linha[20]), f"{nome}: DV do campo 2 inválido"
    assert _dv_modulo10(linha[21:31]) == int(linha[31]), f"{nome}: DV do campo 3 inválido"

    # 3) a linha digitável reconstrói exatamente o código de barras
    assert _reconstroi_codigo_barras(linha) == cb, f"{nome}: linha digitável não reconstrói o CB"
    assert linha[32] == cb[4], f"{nome}: DV geral da linha diverge do código de barras"

    # 4) fator de vencimento ↔ data
    fator = int(cb[5:9])
    assert fator == _fator_esperado(boleto.data_vencimento), f"{nome}: fator de vencimento diverge"
    assert _data_do_fator(fator) == boleto.data_vencimento, f"{nome}: data decodificada diverge"

    # 5) valor embutido (10 dígitos, centavos)
    assert int(cb[9:19]) == boleto.valor_centavos, f"{nome}: valor no código de barras diverge"

    # 6) banco e moeda
    assert cb[0:3] == str(boleto.codigo).zfill(3), f"{nome}: código do banco diverge"
    assert cb[3] == "9", f"{nome}: moeda deveria ser 9 (Real)"


@pytest.mark.parametrize("nome", sorted(EXEMPLOS))
def test_boleto_validado_por_sistema_externo(nome: str) -> None:
    _confere(nome, EXEMPLOS[nome]["boleto"]())


# --- Itaú: uma carteira por composição de DAC --------------------------------
#
# ``EXEMPLOS`` traz o Itaú só na carteira 109. A 112 usa outra composição do DAC
# do nosso número (issue #40) e nunca passava por aqui: era conferida só contra
# vetor externo, e vetor prova que duas implementações concordam, não que ambas
# estejam certas. Este verificador não usa nada do núcleo.


@pytest.mark.parametrize("carteira", ("104", "109", "112", "115", "175", "177", "188"))
def test_carteiras_do_itau_validadas_por_sistema_externo(carteira: str) -> None:
    from pycobranca.bancos import Bancos

    boleto = Bancos.find("341")(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="0057",
        conta="12345",
        carteira=carteira,
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    _confere(f"itau/{carteira}", boleto)
