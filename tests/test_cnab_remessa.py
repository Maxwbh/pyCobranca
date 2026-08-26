"""Remessa CNAB (400 e 240) — validada byte a byte contra vetores de referência.

As fixtures em ``tests/fixtures/*.rem`` foram geradas por uma implementação de referência (Ruby)
com os mesmos dados de entrada; os testes garantem que a PyCobrança produz
arquivos **byte a byte idênticos** (incluindo CRLF, maiúsculas e remoção de
acentos).

**Exceção de procedência — Inter (077) e Safra (422).** Não há implementação de referência
que gere remessa desses dois, então ``remessa_inter_cnab400.rem`` e
``remessa_safra_cnab400.rem`` foram geradas pela própria PyCobrança a partir do layout do
manual de cada banco. Ali a fixture é **guarda de regressão, não paridade**: prende a saída
de hoje, e prenderia igual se estivesse errada. O que confere a saída contra a fonte
primária são ``test_remessa_inter_posicoes_do_manual`` e
``test_remessa_safra_posicoes_do_manual``, que afirmam cada campo na posição documentada.

**Exceção de procedência — Banco do Nordeste (004), CrediSIS (097), BRB (070) e Santander
240 (033).** As quatro produziam registros **fora do comprimento do formato** — 401 e 402
posições num CNAB 400, 241 num 240 —, porque ``rjust`` preenche e não corta. As fixtures não
pegavam: vêm da referência, que estoura igual. Corrigido em ``campo_numerico``, as fixtures
foram regeradas e **deixaram de ser vetor de paridade**; quem confere agora é
``test_toda_remessa_400_produz_registros_de_400_posicoes``, contra o invariante do formato.
Nos três do 400 os dados de teste também mudaram: o nosso número passou a caber no campo que
cada banco declara (7, 6 e 6 posições), como ``regras_campos`` já dizia no boleto.

**Exceção de procedência — Sicoob (756).** A fixture era vetor de paridade e **deixou de
ser**: o layout oficial do banco declara as posições 111–120 como ``X(10)``, alfanumérico, e
a referência preenchia com zeros à esquerda. Onde manual e referência discordam, vale o
manual — então ``remessa_sicoob_cnab400.rem`` foi regerada, e a diferença é **só naquelas dez
posições** (20 bytes, nos dois registros de detalhe; nada mais se moveu). Quem confere agora
é ``test_remessa_sicoob_posicoes_do_layout_oficial``, campo a campo contra a planilha.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pycobranca.cnab import (
    Pagamento,
    RemessaAilos240,
    RemessaBancoBrasil240,
    RemessaBancoBrasil400,
    RemessaBancoBrasilia400,
    RemessaBancoC6_400,
    RemessaBancoNordeste400,
    RemessaBanrisul400,
    RemessaBradesco400,
    RemessaCaixa240,
    RemessaCitibank400,
    RemessaCredisis400,
    RemessaInter400,
    RemessaItau400,
    RemessaSafra400,
    RemessaSantander240,
    RemessaSantander400,
    RemessaSicoob240,
    RemessaSicoob400,
    RemessaSicredi240,
    RemessaUnicred240,
    RemessaUnicred400,
)
from pycobranca.cnab.cnab400.safra import dv_nosso_numero
from pycobranca.exceptions import BoletoInvalido

FIXTURES = Path(__file__).parent / "fixtures"


def _pagamentos() -> list[Pagamento]:
    return [
        Pagamento(
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
        ),
        Pagamento(
            valor=1350.75,
            data_vencimento=date(2026, 9, 1),
            data_emissao=date(2026, 7, 23),
            nosso_numero="87654321",
            numero="DOC0002",
            documento_sacado="11222333000181",
            nome_sacado="Empresa Compradora Ltda & Çia",
            endereco_sacado="Av. Paulista, 1578, conj. 405",
            bairro_sacado="Bela Vista",
            cep_sacado="01310200",
            cidade_sacado="São Paulo",
            uf_sacado="SP",
        ),
    ]


_COMUM = dict(empresa_mae="Empresa Exemplo LTDA", documento_cedente="11222333000181")
_COMUM_400 = dict(**_COMUM, data_geracao=date(2026, 7, 23))
_COMUM_240 = dict(
    **_COMUM,
    sequencial_remessa="1",
    data_geracao_fixa="23072026",
    hora_geracao_fixa="120000",
)


def _pagamentos_com_nosso_numero(digitos: int) -> list[Pagamento]:
    """Como ``_pagamentos()``, com nosso número dentro do campo daquele banco.

    O conjunto comum usa oito dígitos, e três bancos têm campo menor: Banco do
    Nordeste (7), CrediSIS (6) e BRB (6) — os mesmos limites que ``regras_campos``
    já declarava no boleto. Passar oito ali **estourava o registro** para 401 ou
    402 posições, porque ``rjust`` preenche e não corta; hoje é recusado.
    """
    pagamentos = _pagamentos()
    for i, pagamento in enumerate(pagamentos):
        pagamento.nosso_numero = str(1234567 + i)[-digitos:].rjust(digitos, "0")
    return pagamentos


def _pagamentos_inter() -> list[Pagamento]:
    """Como ``_pagamentos()``, com nosso número na faixa de 10 dígitos do Inter."""
    pagamentos = _pagamentos()
    for i, pagamento in enumerate(pagamentos):
        pagamento.nosso_numero = f"{4309540 + i:010d}"
    return pagamentos


def _remessas_400():
    return {
        "itau": RemessaItau400(
            pagamentos=_pagamentos(),
            agencia="0057",
            conta_corrente="12345",
            digito_conta="7",
            carteira="109",
            **_COMUM_400,
        ),
        "bradesco": RemessaBradesco400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="56789",
            digito_conta="0",
            carteira="06",
            codigo_empresa="4587",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banco_brasil": RemessaBancoBrasil400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            convenio="1234567",
            variacao_carteira="019",
            carteira="18",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "santander": RemessaSantander400(
            pagamentos=_pagamentos(),
            codigo_transmissao="9876543210",
            **_COMUM_400,
        ),
        "sicoob": RemessaSicoob400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345678",
            convenio="123456789",
            digito_conta="5",
            carteira="01",
            sequencial_remessa="0000001",
            **_COMUM_400,
        ),
        "unicred": RemessaUnicred400(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            digito_conta="5",
            codigo_beneficiario="12345",
            carteira="21",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banrisul": RemessaBanrisul400(
            pagamentos=_pagamentos(),
            agencia="1234",
            convenio="1234567890123",
            carteira="1",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banco_nordeste": RemessaBancoNordeste400(
            # campo de 7 posições — o conjunto comum usa 8 e é recusado
            pagamentos=_pagamentos_com_nosso_numero(7),
            agencia="1234",
            conta_corrente="1234567",
            digito_conta="5",
            carteira="21",
            **_COMUM_400,
        ),
        "banco_brasilia": RemessaBancoBrasilia400(
            # campo de 6 posições
            pagamentos=_pagamentos_com_nosso_numero(6),
            agencia="123",
            conta_corrente="1234567",
            digito_conta="5",
            carteira="1",
            data_formacao="20260723120000",
            **_COMUM_400,
        ),
        "citibank": RemessaCitibank400(
            pagamentos=_pagamentos(),
            portfolio="12345678901234567890",
            carteira="1",
            **_COMUM_400,
        ),
        "credisis": RemessaCredisis400(
            # campo de 6 posições
            pagamentos=_pagamentos_com_nosso_numero(6),
            agencia="1234",
            conta_corrente="12345678",
            codigo_cedente="1234",
            digito_conta="5",
            carteira="18",
            convenio="1234567",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "inter": RemessaInter400(
            # O Inter usa nosso número de 10 posições (a faixa que ele reserva),
            # não as 8 do conjunto comum — e agora recusa qualquer outro tamanho.
            pagamentos=_pagamentos_inter(),
            agencia="0001",
            conta_corrente="123456",
            digito_conta="7",
            carteira="110",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "banco_c6": RemessaBancoC6_400(
            pagamentos=_pagamentos(),
            codigo_beneficiario="123456789012",
            carteira="20",
            sequencial_remessa="1",
            **_COMUM_400,
        ),
        "safra": RemessaSafra400(
            pagamentos=_pagamentos(),
            agencia="0811",
            conta_corrente="00053678",
            digito_conta="8",
            carteira="1",  # cobrança simples
            sequencial_remessa="1",
            **_COMUM_400,
        ),
    }


def _remessas_240():
    return {
        "ailos": RemessaAilos240(
            pagamentos=_pagamentos(),
            agencia="0134",
            digito_agencia="5",
            conta_corrente="1234567",
            convenio="123456",
            **_COMUM_240,
        ),
        "banco_brasil": RemessaBancoBrasil240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="123456789012",
            convenio="1234567",
            variacao="019",
            carteira="17",
            **_COMUM_240,
        ),
        "caixa": RemessaCaixa240(
            pagamentos=_pagamentos(),
            agencia="1234",
            digito_agencia="5",
            convenio="123456",
            versao_aplicativo="1234",
            conta_corrente="1234567",
            **_COMUM_240,
        ),
        "santander": RemessaSantander240(
            pagamentos=_pagamentos(),
            codigo_transmissao="123456789012345",
            agencia="1234",
            conta_corrente="123456789",
            digito_conta="5",
            **_COMUM_240,
        ),
        "sicoob": RemessaSicoob240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345678",
            convenio="123456",
            modalidade_carteira="01",
            parcela="01",
            digito_conta="5",
            **_COMUM_240,
        ),
        "sicredi": RemessaSicredi240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            digito_conta="5",
            **_COMUM_240,
        ),
        "unicred": RemessaUnicred240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            digito_conta="5",
            **_COMUM_240,
        ),
    }


@pytest.mark.parametrize("banco", sorted(_remessas_400()))
def test_remessa_cnab400_byte_a_byte(banco: str) -> None:
    remessa = _remessas_400()[banco]
    esperado = (FIXTURES / f"remessa_{banco}_cnab400.rem").read_bytes()
    assert remessa.gera_arquivo().encode("ascii") == esperado


@pytest.mark.parametrize("banco", sorted(_remessas_240()))
def test_remessa_cnab240_byte_a_byte(banco: str) -> None:
    remessa = _remessas_240()[banco]
    esperado = (FIXTURES / f"remessa_{banco}_cnab240.rem").read_bytes()
    assert remessa.gera_arquivo().encode("ascii") == esperado


def test_estrutura_dos_registros_400() -> None:
    remessa = _remessas_400()["itau"]
    linhas = remessa.gera_arquivo().splitlines()
    assert len(linhas) == 4  # header + 2 detalhes + trailer
    assert all(len(linha) == 400 for linha in linhas)
    assert linhas[0].startswith("01REMESSA01COBRANCA")
    assert linhas[-1].startswith("9")
    assert linhas[-1].endswith("000004")


def test_estrutura_dos_registros_240() -> None:
    remessa = _remessas_240()["caixa"]
    linhas = remessa.gera_arquivo().splitlines()
    # header arq + header lote + (P+Q+R)*2 + trailer lote + trailer arq
    assert len(linhas) == 10
    assert all(len(linha) == 240 for linha in linhas)
    assert linhas[0][:3] == "104"
    assert linhas[-1][:8] == "10499999"


def test_remessa_sem_pagamentos_levanta() -> None:
    with pytest.raises(BoletoInvalido):
        RemessaItau400(empresa_mae="X").gera_arquivo()


def test_pagamento_incompleto_levanta() -> None:
    with pytest.raises(BoletoInvalido):
        Pagamento(valor=10.0).validar()


# --- Inter: posições conferidas contra o manual, já que não há paridade -------
#
# A fixture do Inter é auto-gerada (ver o docstring do módulo), então ela sozinha
# não prova nada sobre o layout. Este teste é a verificação de verdade: cada campo
# na posição que o *Manual CNAB 400* (V9, seção 4) documenta.


def test_remessa_inter_posicoes_do_manual() -> None:
    arquivo = _remessas_400()["inter"].gera_arquivo()
    header, detalhe, _, trailer = arquivo.replace("\r\n", "\n").rstrip("\n").split("\n")

    def campo(registro: str, de: int, ate: int) -> str:
        """Fatia pela numeração do manual (1-based, inclusiva nas duas pontas)."""
        return registro[de - 1 : ate]

    # 4.1 header
    assert campo(header, 1, 1) == "0"  # item 01
    assert campo(header, 2, 2) == "1"  # item 02
    assert campo(header, 3, 9) == "REMESSA"  # item 03
    assert campo(header, 10, 11) == "01"  # item 04
    assert campo(header, 12, 26) == "COBRANCA".ljust(15)  # item 05
    assert campo(header, 27, 46) == " " * 20  # item 06 — sem agência/conta
    assert campo(header, 77, 79) == "077"  # item 08
    assert campo(header, 80, 94) == "INTER".ljust(15)  # item 09
    assert campo(header, 95, 100) == "230726"  # item 10 — DDMMAA
    assert campo(header, 395, 400) == "000001"  # item 14

    # 4.2 transação tipo 1
    assert campo(detalhe, 1, 1) == "1"  # item 01
    assert campo(detalhe, 2, 20) == " " * 19  # item 02
    assert campo(detalhe, 21, 23) == "110"  # item 03
    assert campo(detalhe, 24, 27) == "0001"  # item 04 — agência única
    assert campo(detalhe, 28, 36) == "000123456"  # item 05
    assert campo(detalhe, 37, 37) == "7"  # item 06
    assert campo(detalhe, 90, 100) == "00043095401"  # item 13 — NN(10) + DV
    assert campo(detalhe, 109, 110) == "01"  # item 15 — remessa
    assert campo(detalhe, 121, 126) == "150826"  # item 17 — vencimento
    assert campo(detalhe, 127, 139) == "0000000019990"  # item 18 — R$ 199,90
    assert campo(detalhe, 140, 141) == "60"  # item 19
    assert campo(detalhe, 148, 149) == "01"  # item 21 — espécie
    assert campo(detalhe, 150, 150) == "N"  # item 22
    assert campo(detalhe, 221, 222) == "01"  # item 34 — CPF
    assert campo(detalhe, 223, 236) == "00052998224725"  # item 35
    assert campo(detalhe, 315, 316) == "MG"  # item 38
    assert campo(detalhe, 317, 324) == "30110000"  # item 39

    # 4.5 trailer — a contagem de boletos é o que difere do trailer genérico
    assert campo(trailer, 1, 1) == "9"  # item 01
    assert campo(trailer, 2, 7) == "000002"  # item 02 — dois boletos
    assert campo(trailer, 8, 394) == " " * 387  # item 03
    assert campo(trailer, 395, 400) == "000004"  # item 04


def test_remessa_inter_zera_o_nosso_numero_na_carteira_112() -> None:
    """Item 13: 'Se carteira 112, envie zeros' — ali quem numera é o banco.

    Mandar o nosso número na 112 seria informar um número que o Inter não
    reconhece, e o arquivo é justamente o pedido para que ele numere.
    """
    remessa = _remessas_400()["inter"]
    remessa.carteira = "112"
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert detalhe[20:23] == "112"
    assert detalhe[89:100] == "0" * 11


def test_remessa_inter_recusa_carteira_fora_do_manual() -> None:
    remessa = _remessas_400()["inter"]
    remessa.carteira = "109"
    with pytest.raises(BoletoInvalido):
        remessa.gera_arquivo()


def test_remessa_inter_grava_multa_juros_e_desconto() -> None:
    """Os três encargos, nas posições e nos códigos do manual (itens 9-12, 25-32).

    Estavam implementados e sem teste — a implementação sozinha não prova que o
    código do encargo, o valor e a data caem onde o banco espera. Aqui cada um é
    afirmado na sua faixa, com a modalidade percentual, que é a que usa os campos
    de taxa em vez dos de valor.
    """
    pagamento = Pagamento(
        nosso_numero="00043095401",
        data_vencimento=date(2026, 8, 15),
        valor=127.50,
        documento_sacado="52998224725",
        nome_sacado="Cliente Final da Silva",
        endereco_sacado="Rua das Flores, 100",
        uf_sacado="MG",
        cep_sacado="30110000",
        numero="CTRL1",
        documento="DOC1",
        codigo_multa="2",  # percentual
        percentual_multa=2.0,
        data_multa=date(2026, 8, 16),
        tipo_mora="2",  # taxa mensal, pro rata
        percentual_mora=1.0,
        data_mora=date(2026, 8, 16),
        cod_desconto="1",  # valor fixo até a data
        valor_desconto=10.0,
        data_desconto=date(2026, 8, 10),
    )
    remessa = _remessas_400()["inter"]
    remessa.pagamentos = [pagamento]
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]

    def campo(de: int, ate: int) -> str:
        return detalhe[de - 1 : ate]

    assert campo(66, 66) == "2"  # item 09 — multa percentual
    assert campo(80, 83) == "0200"  # item 11 — 2,00%
    assert campo(84, 89) == "160826"  # item 12 — data da multa

    assert campo(160, 160) == "2"  # item 25 — taxa mensal de juros
    assert campo(174, 177) == "0100"  # item 27 — 1,00% ao mês
    assert campo(178, 183) == "160826"  # item 28 — data da mora

    assert campo(184, 184) == "1"  # item 29 — desconto em valor fixo
    assert campo(185, 197) == "0000000001000"  # item 30 — R$ 10,00
    assert campo(202, 207) == "100826"  # item 32 — data limite


def test_tipo_mora_isento_da_febraban_vira_zero_no_inter() -> None:
    """O padrão da biblioteca (``"3"`` = isento) não existe no layout do Inter.

    Sem a tradução, todo pagamento sem juros sairia com um código que o banco não
    define — e o arquivo pareceria correto até ser recusado.
    """
    remessa = _remessas_400()["inter"]
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert remessa.pagamentos[0].tipo_mora == "3"  # o padrão da biblioteca
    assert detalhe[159] == "0"  # item 25 — o que vai no arquivo


def test_nosso_numero_sem_dv_ganha_o_digito_em_vez_de_zero_a_esquerda() -> None:
    """O erro que a comunidade do Inter relata como "DV inválido para o nosso número".

    A faixa que o banco entrega vem com 10 dígitos, sem DV. Completar para as 11
    posições do item 13 com zero à esquerda vira ``0`` + número: o dígito some, o
    valor inteiro desloca uma casa, e o banco recusa.

    O detalhe cruel é que as 11 posições continuam **numéricas** — o arquivo passa
    num validador de layout e só quebra no processamento. Por isso o teste compara
    com o número certo, não só com o formato.
    """
    remessa = _remessas_400()["inter"]
    remessa.pagamentos = [
        Pagamento(
            nosso_numero="0004309540",  # 10 dígitos, como o Inter entrega
            data_vencimento=date(2026, 8, 15),
            valor=127.50,
            documento_sacado="52998224725",
            nome_sacado="Cliente Final da Silva",
            endereco_sacado="Rua das Flores, 100",
            uf_sacado="MG",
            cep_sacado="30110000",
            numero="CTRL1",
            documento="DOC1",
        )
    ]
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert detalhe[89:100] == "00043095401"  # DV 1 calculado, não zero à esquerda
    assert detalhe[89:100] != "00004309540"  # o que o zfill produziria


def test_nosso_numero_com_dv_e_usado_como_veio() -> None:
    """Quem já tem o número impresso no boleto passa as 11 posições."""
    remessa = _remessas_400()["inter"]
    remessa.pagamentos[0].nosso_numero = "00043095401"
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert detalhe[89:100] == "00043095401"


@pytest.mark.parametrize("tamanho_errado", ["123", "123456789012"])
def test_nosso_numero_de_tamanho_impossivel_e_recusado(tamanho_errado: str) -> None:
    """Fora de 10 ou 11 dígitos não há como saber se falta ou sobra DV."""
    remessa = _remessas_400()["inter"]
    remessa.pagamentos[0].nosso_numero = tamanho_errado
    with pytest.raises(BoletoInvalido):
        remessa.gera_arquivo()


def test_digito_da_conta_e_obrigatorio_no_inter() -> None:
    """Item 06 é obrigatório; assumir ``0`` grava o dígito de outra conta.

    O arquivo sairia estruturalmente válido apontando para uma identidade de conta
    que não é a do beneficiário — falha silenciosa, recusada só no banco.
    """
    remessa = _remessas_400()["inter"]
    remessa.digito_conta = ""
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("digito_conta" in m for m in erro.value.erros)


def test_nome_do_arquivo_do_inter_casa_com_o_sequencial_do_header() -> None:
    """O manual (seção 3.1) condiciona o upload a essa igualdade.

    A biblioteca gera o conteúdo e o chamador nomeia o arquivo — é justamente onde
    os dois se separam. ``nome_arquivo()`` deriva o nome do mesmo campo que vai no
    header, então não há como divergirem.
    """
    remessa = _remessas_400()["inter"]
    remessa.sequencial_remessa = "0000001"
    header = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[0]
    assert remessa.nome_arquivo() == "CI400_001_0000001.REM"
    assert header[110:117] == "0000001"  # itens 111-117 do header
    assert remessa.nome_arquivo()[10:17] == header[110:117]


def test_nome_do_arquivo_preenche_o_sequencial_com_zeros() -> None:
    """Sequencial ``"1"`` vira ``0000001`` — as sete posições são exigidas."""
    remessa = _remessas_400()["inter"]
    remessa.sequencial_remessa = "1"
    assert remessa.nome_arquivo() == "CI400_001_0000001.REM"


# --- Safra: posições conferidas contra o manual, já que não há paridade -------
#
# Mesma situação do Inter: a fixture é auto-gerada, então ela sozinha não prova
# nada sobre o layout. A verificação de verdade é este teste, campo a campo nas
# posições do *Leiaute de Arquivos — Cobrança CNAB 400* (Banco Safra), seção 6.1.


def _campo(registro: str, de: int, ate: int) -> str:
    """Fatia pela numeração do manual (1-based, inclusiva nas duas pontas)."""
    return registro[de - 1 : ate]


def test_remessa_safra_posicoes_do_manual() -> None:
    arquivo = _remessas_400()["safra"].gera_arquivo()
    header, detalhe, _, trailer = arquivo.replace("\r\n", "\n").rstrip("\n").split("\n")

    # 6.1 header
    assert _campo(header, 1, 1) == "0"
    assert _campo(header, 2, 2) == "1"
    assert _campo(header, 3, 9) == "REMESSA"
    assert _campo(header, 10, 11) == "01"
    assert _campo(header, 12, 19) == "COBRANCA"
    assert _campo(header, 20, 26) == " " * 7
    # "Cod. Empresa (5 primeiras posições agência + 9 posições conta)"
    assert _campo(header, 27, 40) == "00811000053678"
    assert _campo(header, 41, 46) == " " * 6
    assert _campo(header, 77, 79) == "422"
    assert _campo(header, 80, 90) == "BANCO SAFRA"
    assert _campo(header, 91, 94) == " " * 4
    assert _campo(header, 95, 100) == "230726"  # DDMMAA
    assert _campo(header, 101, 391) == " " * 291
    assert _campo(header, 392, 394) == "001"
    assert _campo(header, 395, 400) == "000001"

    # 6.1 detalhe
    assert _campo(detalhe, 1, 1) == "1"
    assert _campo(detalhe, 2, 3) == "02"  # CNPJ do beneficiário
    assert _campo(detalhe, 4, 17) == "11222333000181"
    assert _campo(detalhe, 18, 31) == "00811000053678"
    assert _campo(detalhe, 32, 37) == " " * 6
    assert _campo(detalhe, 63, 71) == "123456789"  # sequencial(8) + DV
    assert _campo(detalhe, 72, 101) == " " * 30
    assert _campo(detalhe, 102, 102) == "0"  # IOF isento
    assert _campo(detalhe, 103, 104) == "00"  # moeda: real
    assert _campo(detalhe, 108, 108) == "1"  # carteira: cobrança simples
    assert _campo(detalhe, 109, 110) == "01"  # remessa de títulos
    assert _campo(detalhe, 121, 126) == "150826"  # vencimento
    assert _campo(detalhe, 127, 139) == "0000000019990"  # R$ 199,90
    assert _campo(detalhe, 140, 142) == "422"  # banco cobrador
    assert _campo(detalhe, 148, 149) == "01"  # espécie: duplicata mercantil
    assert _campo(detalhe, 150, 150) == "N"  # aceite
    assert _campo(detalhe, 151, 156) == "230726"  # emissão
    assert _campo(detalhe, 219, 220) == "01"  # CPF do pagador
    assert _campo(detalhe, 221, 234) == "00052998224725"
    assert _campo(detalhe, 315, 324) == "CENTRO".ljust(10)
    assert _campo(detalhe, 327, 334) == "30110000"
    assert _campo(detalhe, 350, 351) == "MG"
    assert _campo(detalhe, 389, 391) == "422"  # banco emitente
    assert _campo(detalhe, 392, 394) == "001"
    assert _campo(detalhe, 395, 400) == "000002"

    # 6.1 trailer — os totais são o que difere do trailer genérico da base
    assert _campo(trailer, 1, 1) == "9"
    assert _campo(trailer, 2, 368) == " " * 367
    assert _campo(trailer, 369, 376) == "00000002"  # dois títulos
    assert _campo(trailer, 377, 391) == "000000000155065"  # 199,90 + 1350,75
    assert _campo(trailer, 395, 400) == "000004"


def test_dv_do_nosso_numero_do_safra_bate_com_os_exemplos_do_manual() -> None:
    """Seção 7.1 traz três exemplos resolvidos — o terceiro é a borda de resto 0.

    O manual fecha a regra em duas linhas: *"Se na divisão o resto for 0, o dígito
    será 1"* e *"se for 1, o dígito será 0"*. Sem cobrir a borda, um DV errado
    passaria em um a cada onze títulos.
    """
    assert dv_nosso_numero("94550200") == 1
    assert dv_nosso_numero("93199999") == 5
    assert dv_nosso_numero("26173001") == 1  # soma 132, resto 0


def test_remessa_safra_completa_o_dv_sem_deslocar_o_numero() -> None:
    """Oito dígitos entram como a faixa chega do banco; o DV é calculado, não preenchido.

    Completar 8 para 9 com zero à esquerda deslocaria o valor inteiro uma casa e o
    banco recusaria na consistência de *"Dígito de Controle Válido"* — mas as nove
    posições continuariam numéricas, então passaria em validador de layout.
    """
    remessa = _remessas_400()["safra"]
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert _campo(detalhe, 63, 71) == "123456789"
    assert not _campo(detalhe, 63, 71).startswith("0")


def test_remessa_safra_aceita_nosso_numero_ja_com_dv() -> None:
    """As duas formas aparecem na prática: a faixa vem sem DV, o boleto já tem."""
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].nosso_numero = "123456789"  # os mesmos 9 dígitos
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert _campo(detalhe, 63, 71) == "123456789"


def test_remessa_safra_recusa_dv_do_nosso_numero_invalido() -> None:
    """Nove dígitos com DV errado é a consistência 01 da remessa, recusada na entrada."""
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].nosso_numero = "123456780"  # DV correto é 9
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("DV" in m for m in erro.value.erros)


def test_remessa_safra_recusa_nosso_numero_zerado() -> None:
    """Zeros marcam a cobrança convencional, em que quem numera é o banco.

    Ali não há boleto a compor antes do retorno — aceitar seria gerar um título
    cujo número o Safra nunca emitiu.
    """
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].nosso_numero = "00000000"
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("zero" in m for m in erro.value.erros)


def test_multa_do_safra_ocupa_o_campo_de_abatimento() -> None:
    """Nota 6.1.8: a multa não tem campo próprio, entra no do abatimento.

    A forma é específica — data em 206-211, percentual 99v99 em 212-215, zeros em
    216-218 — e exige o código 16 na primeira instrução. Gravar o valor do
    abatimento ali com multa presente produziria um arquivo aceito e com encargo
    errado.
    """
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].percentual_multa = 2.0
    remessa.pagamentos[0].data_multa = date(2026, 8, 16)  # posterior ao vencimento
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]

    assert _campo(detalhe, 157, 158) == "16"  # primeira instrução: multa
    assert _campo(detalhe, 206, 211) == "160826"  # data a partir da qual vale
    assert _campo(detalhe, 212, 215) == "0200"  # 2,00% em 99v99
    assert _campo(detalhe, 216, 218) == "000"


def test_sem_multa_o_campo_206_218_leva_o_abatimento() -> None:
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].valor_abatimento = 50.0
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert _campo(detalhe, 206, 218) == "0000000005000"
    assert _campo(detalhe, 157, 158) == "00"


def test_multa_e_abatimento_nao_cabem_no_mesmo_titulo() -> None:
    """Os dois disputam as posições 206-218: um sobrescreveria o outro em silêncio."""
    remessa = _remessas_400()["safra"]
    pagamento = remessa.pagamentos[0]
    pagamento.percentual_multa = 2.0
    pagamento.data_multa = date(2026, 8, 16)
    pagamento.valor_abatimento = 50.0
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("abatimento" in m for m in erro.value.erros)


def test_multa_do_safra_exige_data_posterior_ao_vencimento() -> None:
    """*"A data da multa deve ser superior a data de vencimento"* (nota 6.1.5)."""
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].percentual_multa = 2.0
    remessa.pagamentos[0].data_multa = date(2026, 8, 15)  # igual ao vencimento
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("vencimento" in m for m in erro.value.erros)


def test_safra_grava_multa_em_percentual_nao_em_valor() -> None:
    """O campo tem quatro posições em 99v99; não há onde caber um valor."""
    remessa = _remessas_400()["safra"]
    remessa.pagamentos[0].valor_multa = 20.0
    remessa.pagamentos[0].data_multa = date(2026, 8, 16)
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("percentual" in m for m in erro.value.erros)


def test_safra_recusa_carteira_fora_das_duas_do_manual() -> None:
    """Nota 6.1.2 define só 1 (simples) e 2 (vinculada)."""
    remessa = _remessas_400()["safra"]
    remessa.carteira = "9"
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("carteira" in m for m in erro.value.erros)


def test_safra_emite_como_correspondente_de_itau_e_bradesco() -> None:
    """Seções 8 e 9: o boleto pode sair sob o código do correspondente.

    As posições 140-142 (banco cobrador) e 389-391 (banco emitente) deixam de ser
    ``422`` — é o que distingue o arranjo, e sem isso o título seria roteado para
    o banco errado.
    """
    remessa = _remessas_400()["safra"]
    remessa.banco_cobrador = "341"
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert _campo(detalhe, 140, 142) == "341"
    assert _campo(detalhe, 389, 391) == "341"


def test_safra_recusa_banco_cobrador_desconhecido() -> None:
    remessa = _remessas_400()["safra"]
    remessa.banco_cobrador = "001"
    with pytest.raises(BoletoInvalido) as erro:
        remessa.gera_arquivo()
    assert any("banco_cobrador" in m for m in erro.value.erros)


# --- Sicoob: as 400 posições conferidas contra o layout oficial --------------
#
# O ``Layout_Cobranca_CNAB400.xls`` do portal do Sicoob (19/05/2025) traz as
# posições campo a campo. Esta tabela é a transcrição da aba *03.Remessa*, e o
# teste abaixo é a auditoria completa: **todo campo documentado**, na posição que
# a planilha declara, com a máscara que ela declara.
#
# Foi ela que encontrou dois problemas que a paridade byte a byte não pegava,
# porque a implementação de referência os reproduzia igual:
#
# - **111-120 é X(10)**, alfanumérico, e o campo era preenchido com zeros à
#   esquerda: ``DOC0001`` virava ``000DOC0001``. O banco devolve isso no retorno,
#   e quem guardou ``DOC0001`` não reencontra o título ao conciliar.
# - **Não existe "tipo de formulário" no layout 400.** O atributo homônimo era
#   aceito e nunca gravado.
#
# Por isso ``remessa_sicoob_cnab400.rem`` **deixou de ser vetor de paridade**: a
# planilha e a referência discordam em 111-120, e a planilha é a fonte primária.

#: ``(início, fim, conteúdo esperado, máscara e nome do campo na planilha)``.
LAYOUT_SICOOB_400 = [
    (1, 1, "1", "9(01) Identificação do Registro Detalhe"),
    (2, 3, "02", "9(02) Tipo de Inscrição do Beneficiário"),
    (4, 17, "11222333000181", "9(14) Número do CPF/CNPJ do Beneficiário"),
    (18, 21, "1234", "9(04) Prefixo da Cooperativa"),
    (22, 22, "3", "9(01) Dígito Verificador do Prefixo"),
    (23, 30, "12345678", "9(08) Conta Corrente"),
    (31, 31, "5", "X(01) Dígito Verificador da Conta"),
    (32, 37, "000000", "9(06) Número do Convênio de Cobrança do Benefici"),
    (38, 62, "                         ", "X(25) Número de Controle do Participante"),
    (63, 74, "000012345678", "9(12) Nosso Número"),
    (75, 76, "01", "9(02) Número da Parcela"),
    (77, 78, "00", "9(02) Grupo de Valor"),
    (79, 81, "   ", "X(03) Complemento do Registro"),
    (82, 82, " ", "X(01) Indicativo de Mensagem ou Sacador/Avalista"),
    (83, 85, "   ", "X(03) Prefixo do Título"),
    (86, 88, "000", "9(03) Variação da Carteira"),
    (89, 89, "0", "9(01) Conta Caução"),
    (90, 94, "00000", "9(05) Número do Contrato Garantia"),
    (95, 95, "0", "X(01) DV do contrato"),
    (96, 101, "000000", "9(06) Numero do borderô"),
    (102, 105, "    ", "X(04) Complemento do Registro"),
    (106, 106, "2", "9(01) Tipo de Emissão"),
    (107, 108, "01", "9(02) Carteira/Modalidade"),
    (109, 110, "01", "9(02) Comando/Movimento"),
    (111, 120, "DOC0001   ", "X(10) Seu Número/Número atribuído pela Empresa"),
    (121, 126, "150826", "A(06) Data Vencimento"),
    (127, 139, "0000000019990", "9(11)V99 Valor do Titulo"),
    (140, 142, "756", "9(03) Número Banco"),
    (143, 146, "1234", "9(04) Prefixo da Cooperativa"),
    (147, 147, "3", "X(01) Dígito Verificador do Prefixo"),
    (148, 149, "01", "9(02) Espécie do Título"),
    (150, 150, "0", "X(01) Aceite do Título"),
    (151, 156, "230726", "9(06) Data de Emissão do Título"),
    (157, 158, "00", "9(02) Primeira instrução codificada"),
    (159, 160, "00", "9(02) Segunda instrução"),
    (161, 166, "000000", "9(02)V9999 Taxa de mora mês"),
    (167, 172, "000000", "9(02)V9999 Taxa de multa"),
    (173, 173, "2", "9(01) Tipo Distribuição 1 – Cooperativa 2 - Clie"),
    (174, 179, "000000", "9(06) Data primeiro desconto"),
    (180, 192, "0000000000000", "9(11)V99 Valor primeiro desconto"),
    (193, 205, "0000000000000", "9(13) 193-193 – Código da moeda 194-205 – Valor "),
    (206, 218, "0000000000000", "9(11)V99 Valor Abatimento"),
    (219, 220, "01", "9(01) Tipo de Inscrição do Pagador"),
    (221, 234, "00052998224725", "9(14) Número do CNPJ ou CPF do Pagador"),
    (235, 274, "CLIENTE FINAL DA SILVA                  ", "A(40) Nome do Pagador"),
    (275, 311, "RUA DAS FLORES 100                   ", "A(37) Endereço do Pagador"),
    (312, 326, "CENTRO         ", "X(15) Bairro do Pagador"),
    (327, 334, "30110000", "9(08) CEP do Pagador"),
    (335, 349, "BELO HORIZONTE ", "A(15) Cidade do Pagador"),
    (350, 351, "MG", "A(02) UF do Pagador"),
    (352, 391, " " * 40, "X(40) Observações/Mensagem ou Sacador/Avalista"),
    (392, 393, "00", "X(02) Número de Dias Para Protesto"),
    # A planilha declara início 394, fim 395 e TAM 1 — os três não fecham, e o
    # campo seguinte começa em 395. Erro da própria planilha; vale o TAM.
    (394, 394, " ", "X(01) Complemento do Registro"),
    (395, 400, "000002", "9(06) Seqüencial do Registro"),
]


@pytest.mark.parametrize(("inicio", "fim", "esperado", "campo"), LAYOUT_SICOOB_400)
def test_remessa_sicoob_posicoes_do_layout_oficial(
    inicio: int, fim: int, esperado: str, campo: str
) -> None:
    """Um caso por campo: a falha aponta a posição e o nome, não "o arquivo mudou"."""
    detalhe = _remessas_400()["sicoob"].gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert detalhe[inicio - 1 : fim] == esperado, f"{inicio}-{fim} ({campo})"


def test_o_layout_do_sicoob_cobre_as_400_posicoes_sem_buraco() -> None:
    """A transcrição tem de ser contígua: buraco esconderia campo não conferido."""
    fim_anterior = 0
    for inicio, fim, _, campo in LAYOUT_SICOOB_400:
        assert inicio == fim_anterior + 1, f"salto antes de {inicio}-{fim} ({campo})"
        fim_anterior = fim
    assert fim_anterior == 400, f"a transcrição termina em {fim_anterior}, não em 400"


def test_seu_numero_do_sicoob_e_alfanumerico_alinhado_a_esquerda() -> None:
    """Posições 111-120, X(10): letras à esquerda, brancos à direita.

    Zero à esquerda produziria ``000DOC0001`` — outro valor, e é esse que o banco
    devolve no retorno.
    """
    detalhe = _remessas_400()["sicoob"].gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert detalhe[110:120] == "DOC0001   "


def test_seu_numero_so_de_digitos_mantem_os_zeros_a_esquerda() -> None:
    """Onde as duas convenções coincidem, o comportamento anterior se mantém."""
    remessa = _remessas_400()["sicoob"]
    remessa.pagamentos[0].numero = "4321"
    detalhe = remessa.gera_arquivo().replace("\r\n", "\n").split("\n")[1]
    assert detalhe[110:120] == "0000004321"


def test_o_sicoob_400_nao_aceita_mais_tipo_de_formulario() -> None:
    """O layout 400 não tem esse campo — é do 240, onde segue em uso.

    Aceitar um parâmetro e não gravá-lo é pior que recusá-lo: quem o informava
    acreditava estar mudando o arquivo.
    """
    with pytest.raises(TypeError):
        RemessaSicoob400(tipo_formulario="4")
    assert RemessaSicoob240(tipo_formulario="4").tipo_formulario == "4"


# --- Comprimento de registro: o formato define, e agora é cobrado ------------
#
# Quatro remessas produziam registros **fora do comprimento do formato** — 401 e
# 402 num CNAB 400, 241 num 240. Causa única nas quatro: ``str.rjust`` preenche
# mas **nunca corta**, então um valor maior que o campo atravessava para a
# posição seguinte e deslocava todo o resto do registro.
#
# As fixtures não pegavam: vinham da implementação de referência, que estoura
# igual. Foi preciso medir contra o invariante do formato — 400 e 240 posições —
# para o defeito aparecer.
#
# ``campo_numerico`` substituiu o ``rjust`` nos quatro pontos: descarta zeros à
# esquerda que sobram e **recusa** dígito significativo que não cabe.


def test_toda_remessa_400_produz_registros_de_400_posicoes() -> None:
    """O BRB é a única exceção, e por um motivo documentado: header DCB de 39."""
    for nome, remessa in _remessas_400().items():
        linhas = remessa.gera_arquivo().replace("\r\n", "\n").rstrip("\n").split("\n")
        comprimentos = sorted({len(linha) for linha in linhas})
        esperado = [39, 400] if nome == "banco_brasilia" else [400]
        assert comprimentos == esperado, f"{nome}: {comprimentos}"


def test_toda_remessa_240_produz_registros_de_240_posicoes() -> None:
    for nome, remessa in _remessas_240().items():
        linhas = remessa.gera_arquivo().replace("\r\n", "\n").rstrip("\n").split("\n")
        assert {len(linha) for linha in linhas} == {240}, nome


@pytest.mark.parametrize(
    ("banco", "digitos"),
    [("banco_nordeste", 7), ("credisis", 6), ("banco_brasilia", 6)],
)
def test_nosso_numero_maior_que_o_campo_e_recusado(banco: str, digitos: int) -> None:
    """Antes atravessava o campo em silêncio; hoje o erro diz quanto não coube.

    Os limites são os que ``regras_campos`` já declarava no boleto — a remessa
    é que não os aplicava.
    """
    remessa = _remessas_400()[banco]
    remessa.pagamentos[0].nosso_numero = "9" * (digitos + 1)
    with pytest.raises(BoletoInvalido, match="não cabe"):
        remessa.gera_arquivo()


def test_zeros_a_esquerda_que_sobram_nao_sao_erro() -> None:
    """``dias_baixa`` do Santander: padrão ``"000"`` num campo de duas posições.

    Descartar zero à esquerda não perde valor; recusar aqui quebraria todo
    Santander 240 por causa de um padrão, não de um dado do chamador.
    """
    from pycobranca.cnab.formatacao import campo_numerico

    assert campo_numerico("000", 2, "dias_baixa") == "00"
    assert campo_numerico("0012345", 5, "x") == "12345"
    with pytest.raises(BoletoInvalido, match="não cabe"):
        campo_numerico("123456", 5, "x")


# --- Nenhum atributo aceito e nunca gravado ----------------------------------
#
# O ``tipo_formulario`` do Sicoob 400 era aceito no construtor e não chegava ao
# arquivo: quem o informava acreditava estar mudando alguma coisa. A varredura
# encontrou mais quatro no Sicredi 240 (herdados pela Unicred) e um no Sicoob
# 240. Todos removidos.
#
# Este teste é a garantia de que não voltam: percorre **todas** as remessas e
# exige que cada campo declarado seja lido em algum lugar do módulo.


def _campos_nao_lidos(cls) -> set[str]:
    """Campos próprios da classe que nenhum ``self.<nome>`` do módulo consulta."""
    import ast
    import dataclasses
    import importlib
    from pathlib import Path as _Path

    from pycobranca.cnab.cnab240.base import RemessaCnab240Base
    from pycobranca.cnab.cnab400.base import RemessaCnab400Base

    mod = importlib.import_module(cls.__module__)
    arvore = ast.parse(_Path(mod.__file__).read_text(encoding="utf-8"))
    lidos = {
        no.attr
        for no in ast.walk(arvore)
        if isinstance(no, ast.Attribute)
        and isinstance(no.value, ast.Name)
        and no.value.id == "self"
    }
    herdados = {
        f.name
        for base in (RemessaCnab400Base, RemessaCnab240Base)
        for f in dataclasses.fields(base)
    }
    proprios = {f.name for f in dataclasses.fields(cls)} - herdados
    return proprios - lidos


def _classes_de_remessa():
    import dataclasses
    import importlib
    import pkgutil

    import pycobranca.cnab.cnab240 as c2
    import pycobranca.cnab.cnab400 as c4

    achadas = []
    for pacote in (c4, c2):
        for modulo in pkgutil.iter_modules(pacote.__path__):
            if modulo.name in ("base", "pix"):
                continue
            mod = importlib.import_module(f"{pacote.__name__}.{modulo.name}")
            for nome in dir(mod):
                cls = getattr(mod, nome)
                if (
                    isinstance(cls, type)
                    and nome.startswith("Remessa")
                    and dataclasses.is_dataclass(cls)
                    and cls.__module__ == mod.__name__
                ):
                    achadas.append(cls)
    return achadas


@pytest.mark.parametrize("cls", _classes_de_remessa(), ids=lambda c: c.__name__)
def test_nenhuma_remessa_aceita_campo_que_nao_grava(cls) -> None:
    """Campo aceito e ignorado é pior que ausente: promete e não cumpre."""
    assert _campos_nao_lidos(cls) == set()
