"""Validação externa: cada boleto conferido por um verificador FEBRABAN independente.

Estes testes **não usam o código do núcleo** (``pycobranca.core.dv``,
``pycobranca.boleto`` etc.). Eles reimplementam, do zero, exatamente o que um
sistema externo faz ao **receber** um boleto — um app de banco lendo a linha
digitável, um PSP conferindo o código de barras, um leitor de arquivo de
pagamento. Se a PyCobrança e este verificador independente concordam, o título
seria aceito por qualquer sistema conforme à FEBRABAN.

Para cada um dos 19 bancos, a partir do que a PyCobrança emitiu, verificamos:

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
from pycobranca.exceptions import PyCobrancaError

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


# --- Inter: sem vetor cruzado, esta é a única verificação externa da saída -----
#
# Os demais bancos têm a saída conferida contra uma implementação de produção
# independente. O Inter não existe em nenhuma implementação aberta conhecida,
# então esse cruzamento não existe para ele — e este verificador, que não usa
# nada do núcleo, deixa de ser camada extra para ser a única. Ver o docstring de
# ``test_bancos_inter.py`` para a hierarquia completa da evidência.


def test_inter_validado_por_sistema_externo() -> None:
    from pycobranca.bancos import Bancos

    boleto = Bancos.find("077")(
        valor="1234.56",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="0001",
        conta="123456",
        carteira="110",
        convenio="1234567",
        nosso_numero="0004309540",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    _confere("inter/110", boleto)


# --- Toda carteira declarada, em todo banco ----------------------------------
#
# ``carteiras`` é promessa pública: quem lê a matriz acredita que aquelas
# carteiras funcionam. Os exemplos exercitavam **uma** por banco — as demais
# nunca tinham sido geradas, e uma delas nunca funcionou.

#: Carteiras declaradas que **não produzem boleto válido**. Não é lista de
#: tolerância: é defeito registrado, com o teste abaixo garantindo que ninguém
#: some com a evidência nem acrescente outra sem perceber.
#:
#: - **399/CSB**: ``campo_livre`` monta nosso número(13) + agência(4) +
#:   conta(7) + ``"001"`` = **27 posições**, onde a FEBRABAN exige 25. É
#:   aritmético: a carteira nunca gerou boleto. A composição correta precisa do
#:   manual do HSBC, que o banco não publica mais — encerrou no Brasil em 2016.
CARTEIRAS_QUEBRADAS = {("399", "CSB")}


def _um_boleto_por_banco():
    """Um construtor válido por código de banco, tirado dos exemplos."""
    return {ex["boleto"]().codigo: ex["boleto"] for ex in EXEMPLOS.values()}


def _todas_as_carteiras():
    from pycobranca.bancos import Bancos

    construtores = _um_boleto_por_banco()
    return [
        (banco.codigo, carteira)
        for banco in sorted(Bancos.todos(), key=lambda b: b.codigo)
        if banco.codigo in construtores
        for carteira in banco.carteiras
    ]


@pytest.mark.parametrize(("codigo", "carteira"), _todas_as_carteiras())
def test_toda_carteira_declarada_gera_boleto_valido(codigo: str, carteira: str) -> None:
    """Troca só a carteira sobre dados válidos do banco e roda o verificador.

    O verificador é o mesmo dos outros testes deste módulo: não usa nada do
    núcleo, reimplementa as regras FEBRABAN do zero.
    """
    boleto = _um_boleto_por_banco()[codigo]()
    boleto.carteira = carteira
    if (codigo, carteira) in CARTEIRAS_QUEBRADAS:
        with pytest.raises((PyCobrancaError, AssertionError)):
            _confere(f"{codigo}/{carteira}", boleto)
        return
    _confere(f"{codigo}/{carteira}", boleto)


def test_a_lista_de_carteiras_quebradas_nao_cresceu() -> None:
    """Prende o número: uma carteira nova que não funcione tem de aparecer aqui."""
    assert CARTEIRAS_QUEBRADAS == {("399", "CSB")}


def test_o_campo_livre_do_csb_tem_27_posicoes_onde_cabem_25() -> None:
    """Nomeia a causa, para a correção não virar tentativa e erro.

    Não é ajuste de dígito: sobram **duas** posições na composição. Sem o manual
    do HSBC não dá para saber qual campo encolhe, então o defeito fica descrito
    em vez de adivinhado.
    """
    boleto = _um_boleto_por_banco()["399"]()
    boleto.carteira = "CSB"
    assert len(boleto.campo_livre()) == 27


def test_a_mesma_carteira_escrita_de_dois_jeitos_da_o_mesmo_boleto() -> None:
    """``"9"`` e ``"09"`` são a mesma carteira — têm de gerar o mesmo título.

    O Sicoob declara as duas grafias e o Ailos declara ``"1"`` e ``"01"``. O
    Ailos acertava (``zfill(2)``); o Sicoob montava a posição 1 do campo livre
    com ``so_digitos(carteira)[:1]``, que pega o **primeiro** caractere — e
    ``"09"`` virava ``"0"``, uma carteira que o banco não tem.

    Nenhuma camada existente pegava isso. O verificador FEBRABAN aprova: são 44
    posições com o DV recalculado sobre o valor errado. O vetor cruzado usa uma
    grafia só. É o mesmo modo de falha do ``portfolio`` do Citibank — o boleto
    sai plausível, válido e cobrando pela conta errada.
    """
    from collections import defaultdict

    from pycobranca.bancos import Bancos

    construtores = _um_boleto_por_banco()
    divergem = []
    for banco in sorted(Bancos.todos(), key=lambda b: b.codigo):
        if banco.codigo not in construtores:
            continue
        grupos = defaultdict(list)
        for carteira in banco.carteiras:
            if carteira.isdigit():
                grupos[int(carteira)].append(carteira)
        for numero, grafias in grupos.items():
            if len(grafias) < 2:
                continue
            saidas = {}
            for grafia in grafias:
                boleto = construtores[banco.codigo]()
                boleto.carteira = grafia
                saidas[grafia] = boleto.codigo_barras
            if len(set(saidas.values())) > 1:
                divergem.append(f"{banco.codigo} carteira {numero}: {saidas}")
    assert divergem == [], "\n".join(divergem)


@pytest.mark.parametrize("carteira", ["9", "09"])
def test_a_carteira_9_do_sicoob_grava_o_9_no_campo_livre(carteira: str) -> None:
    """Prende o dígito, não só a igualdade entre as duas grafias.

    Sem isto, uma correção que fizesse as duas gravarem ``"0"`` também passaria
    no teste acima — as duas iguais, as duas erradas.
    """
    boleto = _um_boleto_por_banco()["756"]()
    boleto.carteira = carteira
    assert boleto.campo_livre()[0] == "9"


def test_carteira_que_nao_cabe_na_posicao_do_campo_livre_e_recusada() -> None:
    """Dois dígitos significativos num campo de um: erro, não truncamento.

    Truncar produziria um boleto de outra carteira, que é exatamente o defeito
    que se está consertando.
    """
    boleto = _um_boleto_por_banco()["756"]()
    boleto.carteira = "19"
    with pytest.raises(PyCobrancaError, match="posição 1 do campo livre"):
        boleto.campo_livre()
