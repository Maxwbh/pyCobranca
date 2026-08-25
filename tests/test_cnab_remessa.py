"""Remessa CNAB (400 e 240) — validada byte a byte contra vetores de referência.

As fixtures em ``tests/fixtures/*.rem`` foram geradas por uma implementação de referência (Ruby)
com os mesmos dados de entrada; os testes garantem que a PyCobrança produz
arquivos **byte a byte idênticos** (incluindo CRLF, maiúsculas e remoção de
acentos).

**Exceção de procedência — Inter (077).** Não há implementação de referência que gere
remessa do Inter, então ``remessa_inter_cnab400.rem`` foi gerada pela própria PyCobrança
a partir do layout do *Manual CNAB400* do banco (v2.2, seção 4). Ali a fixture é **guarda
de regressão, não paridade**: prende a saída de hoje, e prenderia igual se estivesse
errada. O que confere a saída contra a fonte primária é
``test_remessa_inter_posicoes_do_manual``, que afirma cada campo na posição documentada.
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
    RemessaSantander240,
    RemessaSantander400,
    RemessaSicoob240,
    RemessaSicoob400,
    RemessaSicredi240,
    RemessaUnicred240,
    RemessaUnicred400,
)
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
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="1234567",
            digito_conta="5",
            carteira="21",
            **_COMUM_400,
        ),
        "banco_brasilia": RemessaBancoBrasilia400(
            pagamentos=_pagamentos(),
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
            pagamentos=_pagamentos(),
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
            tipo_formulario="4",
            parcela="01",
            digito_conta="5",
            **_COMUM_240,
        ),
        "sicredi": RemessaSicredi240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            byte_idt="2",
            modalidade_carteira="01",
            parcela="01",
            posto="00",
            digito_conta="5",
            **_COMUM_240,
        ),
        "unicred": RemessaUnicred240(
            pagamentos=_pagamentos(),
            agencia="1234",
            conta_corrente="12345",
            byte_idt="2",
            modalidade_carteira="01",
            parcela="01",
            posto="00",
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
# na posição que o *Manual CNAB400* (v2.2, seção 4) documenta.


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
