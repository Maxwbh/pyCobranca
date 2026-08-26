"""Exemplos de boleto por banco — fonte única dos testes de validação.

Cada entrada traz o construtor do título e a saída de referência (código de
barras, linha digitável e nosso número) gerada pela BrCobrança (Ruby) com
exatamente os mesmos dados de entrada. É consumida por:

- ``test_validacao_cruzada.py`` — paridade byte a byte com vetores de referência;
- ``test_validacao_externa.py`` — validador FEBRABAN independente (round-trip
  linha digitável ↔ código de barras, como faria um app de banco/PSP).

Divergência conhecida (cosmética, arbitrada pela documentação oficial): o
Santander imprime o nosso número com 13 posições (12 dígitos + DV) no layout
oficial — a PyCobrança segue o manual; a BrCobrança omite os zeros à esquerda
(``1234567-9``). O código de barras é idêntico nos dois sistemas.

**Exceção de procedência — Inter (077).** O Inter não existe na BrCobrança nem em
nenhuma outra implementação aberta conhecida, então a entrada dele **não tem vetor
cruzado**: a saída foi derivada do *Manual CNAB400* do próprio banco (V9, 06/07/2026),
posição a posição, com o DV do nosso número conferido contra o exemplo resolvido da
seção 8.3. Aqui o valor congelado é **guarda de regressão**, não concordância entre dois
sistemas — prende a saída de hoje, e prenderia igual se estivesse errada. O que continua
valendo para o Inter como verificação independente é ``test_validacao_externa.py``, que
não usa nada do núcleo. Ver ``test_bancos_inter.py`` para o detalhe da evidência.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import TypedDict

from pycobranca.bancos import (
    BRB,
    C6,
    HSBC,
    Ailos,
    BancoDoBrasil,
    BancoNordeste,
    Banestes,
    Banrisul,
    Bradesco,
    Caixa,
    Citibank,
    CrediSIS,
    Inter,
    Itau,
    Safra,
    Santander,
    Sicoob,
    Sicredi,
    Unicred,
)
from pycobranca.bancos.base import BancoBase

COMUM = dict(
    valor="127.50",
    cedente="Empresa Exemplo LTDA",
    cedente_documento="11222333000181",
    sacado="Cliente Final da Silva",
    sacado_documento="52998224725",
    data_vencimento=date(2026, 8, 15),
    data_documento=date(2026, 7, 23),
)


class Exemplo(TypedDict):
    boleto: Callable[[], BancoBase]
    codigo_barras: str
    linha_digitavel: str
    nosso_numero: str


# Saída literal da BrCobrança para os mesmos dados (brcobranca-saida.json).
EXEMPLOS: dict[str, Exemplo] = {
    "itau": {
        "boleto": lambda: Itau(
            **COMUM, agencia="0057", conta="12345", carteira="109", nosso_numero="12345678"
        ),
        "codigo_barras": "34195153900000127501091234567800057123457000",
        "linha_digitavel": "34191.09123 34567.800056 71234.570001 5 15390000012750",
        "nosso_numero": "109/12345678-0",
    },
    "banco_brasil": {
        "boleto": lambda: BancoDoBrasil(
            **COMUM,
            agencia="1234",
            conta="56789",
            convenio="1234567",
            carteira="18",
            nosso_numero="123",
        ),
        "codigo_barras": "00199153900000127500000001234567000000012318",
        "linha_digitavel": "00190.00009 01234.567004 00000.123182 9 15390000012750",
        "nosso_numero": "12345670000000123",
    },
    "bradesco": {
        "boleto": lambda: Bradesco(
            **COMUM, agencia="1234", conta="56789", carteira="06", nosso_numero="2"
        ),
        "codigo_barras": "23799153900000127501234060000000000200567890",
        "linha_digitavel": "23791.23405 60000.000004 02005.678905 9 15390000012750",
        "nosso_numero": "06/00000000002-9",
    },
    "santander": {
        "boleto": lambda: Santander(
            **COMUM, convenio="3300123", carteira="101", nosso_numero="1234567"
        ),
        "codigo_barras": "03396153900000127509330012300000123456790101",
        "linha_digitavel": "03399.33004 12300.000127 34567.901011 6 15390000012750",
        # BrCobrança: "1234567-9" (sem zeros); PyCobrança segue as 13 posições do layout oficial
        "nosso_numero": "000001234567-9",
    },
    "caixa": {
        "boleto": lambda: Caixa(
            **COMUM, agencia="1234", convenio="123456", carteira="14", nosso_numero="123"
        ),
        "codigo_barras": "10491153900000127501234560000100040000001230",
        "linha_digitavel": "10491.23456 60000.100044 00000.012302 1 15390000012750",
        "nosso_numero": "14000000000000123-1",
    },
    "banrisul": {
        "boleto": lambda: Banrisul(
            **COMUM,
            agencia="1102",
            conta="12345678",
            convenio="9000150",
            digito_convenio="46",
            carteira="2",
            nosso_numero="22832563",
        ),
        "codigo_barras": "04195153900000127502111029000150228325634059",
        "linha_digitavel": "04192.11107 29000.150226 83256.340593 5 15390000012750",
        "nosso_numero": "22832563-51",
    },
    "sicoob": {
        "boleto": lambda: Sicoob(
            **COMUM,
            agencia="3007",
            conta="12345678",
            convenio="229385",
            carteira="1",
            variacao="01",
            nosso_numero="246",
        ),
        "codigo_barras": "75696153900000127501300701022938500002463001",
        "linha_digitavel": "75691.30078 01022.938508 00024.630014 6 15390000012750",
        "nosso_numero": "00002463",
    },
    "sicredi": {
        "boleto": lambda: Sicredi(
            **COMUM,
            agencia="0165",
            posto="05",
            conta="00623",
            convenio="00623",
            carteira="3",
            byte_idt="2",
            nosso_numero="12345",
        ),
        "codigo_barras": "74891153900000127503126212345301650500623105",
        "linha_digitavel": "74893.12624 12345.301654 05006.231053 1 15390000012750",
        "nosso_numero": "26/212345-3",
    },
    "unicred": {
        "boleto": lambda: Unicred(
            **COMUM,
            agencia="1234",
            conta="123456789",
            digito_conta="1",
            carteira="21",
            nosso_numero="12345",
        ),
        "codigo_barras": "13697153900000127501234123456789100000123455",
        "linha_digitavel": "13691.23417 23456.789108 00001.234558 7 15390000012750",
        "nosso_numero": "0000012345-5",
    },
    "ailos": {
        "boleto": lambda: Ailos(
            **COMUM,
            agencia="0001",
            conta="1234567",
            convenio="123456",
            carteira="01",
            nosso_numero="12345678",
        ),
        "codigo_barras": "08594153900000127501234561234567901234567801",
        "linha_digitavel": "08591.23457 61234.567909 12345.678010 4 15390000012750",
        "nosso_numero": "12345679012345678",
    },
    "brb": {
        "boleto": lambda: BRB(
            **COMUM,
            agencia="082",
            conta="0000528",
            carteira="2",
            nosso_numero="000403",
            incremento="100",
        ),
        "codigo_barras": "07097153900000127501000820000528200040307035",
        "linha_digitavel": "07091.00085 20000.528206 00403.070352 7 15390000012750",
        "nosso_numero": "200040307035",
    },
    "banco_nordeste": {
        "boleto": lambda: BancoNordeste(
            **COMUM,
            agencia="0016",
            conta="0001193",
            digito_conta="2",
            carteira="21",
            nosso_numero="0000053",
        ),
        "codigo_barras": "00493153900000127500016000119320000053121000",
        "linha_digitavel": "00490.01605 00119.320000 00531.210003 3 15390000012750",
        "nosso_numero": "0000053-1",
    },
    "banestes": {
        "boleto": lambda: Banestes(
            **COMUM,
            agencia="0274",
            conta="0009206981",
            digito_conta="9",
            carteira="11",
            variacao="2",
            nosso_numero="90002720",
        ),
        "codigo_barras": "02197153900000127509000272000092069819202187",
        "linha_digitavel": "02199.00024 72000.092063 98192.021875 7 15390000012750",
        "nosso_numero": "90002720-71",
    },
    "citibank": {
        "boleto": lambda: Citibank(
            **COMUM,
            agencia="0123",
            conta="1234567",
            portfolio="172",
            convenio="0006247107",
            carteira="3",
            nosso_numero="01099994022",
        ),
        "codigo_barras": "74593153900000127503172006247107010999940225",
        "linha_digitavel": "74593.17207 06247.107011 09999.402259 3 15390000012750",
        "nosso_numero": "01099994022.5",
    },
    "credisis": {
        "boleto": lambda: CrediSIS(
            **COMUM,
            agencia="0001",
            conta="0000002",
            convenio="000527",
            carteira="18",
            nosso_numero="000001",
        ),
        "codigo_barras": "09796153900000127500000009780001000527000001",
        "linha_digitavel": "09790.00007 09780.001005 05270.000010 6 15390000012750",
        "nosso_numero": "09780001000527000001",
    },
    "hsbc_cnr": {
        "boleto": lambda: HSBC(
            **COMUM, agencia="4321", conta="1122334", carteira="CNR", nosso_numero="12345678"
        ),
        "codigo_barras": "39998153900000127501122334000001234567822762",
        "linha_digitavel": "39991.12232 34000.001239 45678.227625 8 15390000012750",
        "nosso_numero": "0000012345678945",
    },
    # Sem vetor cruzado: derivado do manual do próprio banco. Ver o docstring do módulo.
    "inter": {
        "boleto": lambda: Inter(
            **COMUM,
            agencia="0001",
            conta="123456",
            carteira="110",
            convenio="1234567",
            nosso_numero="0004309540",
        ),
        "codigo_barras": "07796153900000127500001110123456700043095401",
        "linha_digitavel": "07790.00116 10123.456708 00430.954016 6 15390000012750",
        "nosso_numero": "0004309540-1",
    },
    "safra": {
        "boleto": lambda: Safra(
            **COMUM,
            agencia="0811",
            digito_agencia="1",
            conta="00053678",
            digito_conta="8",
            carteira="2",
            nosso_numero="12345678",
        ),
        "codigo_barras": "42294153900000127507081110005367881234567892",
        "linha_digitavel": "42297.08112 10005.367882 12345.678929 4 15390000012750",
        "nosso_numero": "12345678-9",
    },
    "c6": {
        "boleto": lambda: C6(
            **COMUM,
            agencia="0001",
            conta="1234567",
            convenio="123456789012",
            carteira="20",
            nosso_numero="1234567890",
        ),
        "codigo_barras": "33691153900000127501234567890121234567890204",
        "linha_digitavel": "33691.23454 67890.121238 45678.902045 1 15390000012750",
        "nosso_numero": "1234567890-0",
    },
}
