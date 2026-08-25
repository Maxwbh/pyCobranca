"""Parsing de retorno CNAB 240 — porta fiel de ``Retorno::Cnab240``.

O CNAB 240 usa dois registros de detalhe por título: o **segmento T** (dados
gerais) e o **segmento U** (valores). Ambos usam o mesmo mapa posicional; os
campos de ``T_FIELDS`` vêm da linha T e os de ``U_FIELDS`` da linha U. Apenas
linhas de detalhe (registro ``3``, segmento ``T``/``U``) são consideradas.
"""

from __future__ import annotations

import warnings

from ...exceptions import LayoutGenerico
from .base import RegistroRetorno, extrai_campo, transforma_motivo

__all__ = ["parse_cnab240", "banco_do_arquivo_240", "LAYOUTS_240"]

_RANGES_BASE = {
    "codigo_registro": (7, 7),
    "tipo_registro": (13, 13),
    "sequencial": (8, 12),
    "codigo_ocorrencia": (15, 16),
    "agencia_com_dv": (17, 22),
    "cedente_com_dv": (23, 35),
    "nosso_numero": (46, 56),
    "carteira": (57, 57),
    "data_vencimento": (73, 80),
    "valor_titulo": (81, 95),
    "banco_recebedor": (96, 98),
    "agencia_recebedora_com_dv": (99, 104),
    "data_ocorrencia": (137, 144),
    "data_credito": (145, 152),
    "outras_despesas": (107, 121),
    "iof_desconto": (62, 76),
    "valor_abatimento": (47, 61),
    "desconto_concedito": (32, 46),
    "valor_recebido": (77, 91),
    "juros_mora": (17, 31),
    "outros_recebimento": (122, 136),
    "valor_tarifa": (198, 212),
    "motivo_ocorrencia": (213, 222, "chunk2"),
}

_T_BASE = [
    "codigo_registro",
    "codigo_ocorrencia",
    "agencia_com_dv",
    "cedente_com_dv",
    "nosso_numero",
    "carteira",
    "data_vencimento",
    "valor_titulo",
    "banco_recebedor",
    "agencia_recebedora_com_dv",
    "sequencial",
    "valor_tarifa",
    "motivo_ocorrencia",
]
_U_BASE = [
    "desconto_concedito",
    "valor_abatimento",
    "iof_desconto",
    "juros_mora",
    "valor_recebido",
    "outras_despesas",
    "outros_recebimento",
    "data_ocorrencia",
    "data_credito",
]


def _layout(ranges: dict, t_fields: list[str], u_fields: list[str]) -> dict:
    return {"ranges": ranges, "T": t_fields, "U": u_fields}


LAYOUTS_240: dict[str, dict] = {
    "default": _layout(dict(_RANGES_BASE), list(_T_BASE), list(_U_BASE)),
    "104": _layout(  # Caixa (SIGCB): sobrepõe nosso_numero e ag. recebedora
        {**_RANGES_BASE, "nosso_numero": (39, 55), "agencia_recebedora_com_dv": (99, 103)},
        list(_T_BASE),
        list(_U_BASE),
    ),
    "085": _layout(  # Ailos
        {
            **_RANGES_BASE,
            "agencia_com_dv": (17, 22),
            "nosso_numero": (37, 56),
        },
        list(_T_BASE),
        [
            "desconto_concedito",
            "valor_abatimento",
            "iof_desconto",
            "juros_mora",
            "valor_recebido",
            "outras_despesas",
            "outros_recebimento",
            "data_credito",
            "data_ocorrencia",
        ],
    ),
    "748": _layout(  # Sicredi
        {**_RANGES_BASE, "nosso_numero": (37, 56)},
        list(_T_BASE),
        [
            "desconto_concedito",
            "valor_abatimento",
            "iof_desconto",
            "juros_mora",
            "valor_recebido",
            "outras_despesas",
            "outros_recebimento",
            "data_ocorrencia",
            "data_credito",
        ],
    ),
    "756": _layout(  # Sicoob
        {
            **_RANGES_BASE,
            "nosso_numero": (37, 46),
            "documento_numero": (58, 72),
            "especie_documento": (111, 113),
        },
        [
            "codigo_registro",
            "codigo_ocorrencia",
            "agencia_com_dv",
            "cedente_com_dv",
            "nosso_numero",
            "carteira",
            "documento_numero",
            "data_vencimento",
            "valor_titulo",
            "banco_recebedor",
            "agencia_recebedora_com_dv",
            "especie_documento",
            "sequencial",
            "valor_tarifa",
            "motivo_ocorrencia",
        ],
        [
            "juros_mora",
            "desconto_concedito",
            "valor_abatimento",
            "iof_desconto",
            "valor_recebido",
            "outras_despesas",
            "outros_recebimento",
            "data_credito",
            "data_ocorrencia",
        ],
    ),
    "033": _layout(  # Santander
        {
            **_RANGES_BASE,
            "agencia_com_dv": (17, 21),
            "cedente_com_dv": (22, 31),
            "nosso_numero": (40, 52),
            "carteira": (53, 53),
            "data_vencimento": (69, 76),
            "valor_titulo": (77, 91),
            "banco_recebedor": (92, 94),
            "agencia_recebedora_com_dv": (95, 99),
            "valor_tarifa": (193, 207),
            "motivo_ocorrencia": (208, 117, "chunk2"),  # faixa inválida → vazio
        },
        list(_T_BASE),
        [
            "desconto_concedito",
            "data_ocorrencia",
            "valor_abatimento",
            "iof_desconto",
            "juros_mora",
            "valor_recebido",
            "outras_despesas",
            "outros_recebimento",
            "data_credito",
        ],
    ),
}

# valor_recebido (77..91) coincide com valor_titulo; ambos ficam nos seus segmentos.


def banco_do_arquivo_240(primeira_linha: str) -> str:
    """Código do banco no header do retorno CNAB 240 (posições 0–2)."""
    return primeira_linha[0:3]


def _linha_de_detalhe(linha: str) -> bool:
    # padrão: ^.{7}3.{5}[T|U] → registro '3' na pos. 7 e T/U na pos. 13
    return len(linha) > 13 and linha[7] == "3" and linha[13] in ("T", "U", "|")


def parse_cnab240(linhas: list[str], codigo_banco: str) -> list[RegistroRetorno]:
    layout = LAYOUTS_240.get(codigo_banco)
    if layout is None:
        # Mesmo caso do 400: lê tudo, não levanta nada, e os campos podem sair
        # de posições que não são as deste banco.
        layout = LAYOUTS_240["default"]
        warnings.warn(
            f"retorno CNAB 240 do banco {codigo_banco!r} lido com o layout genérico: "
            "não há mapa próprio para ele, e os campos podem estar em outras posições",
            LayoutGenerico,
            stacklevel=2,
        )
    ranges = layout["ranges"]
    detalhes = [linha for linha in linhas if _linha_de_detalhe(linha)]

    def aplica(registro: RegistroRetorno, linha: str, campos: list[str]) -> None:
        for attr in campos:
            faixa = ranges.get(attr)
            if faixa is None:
                continue
            if attr == "motivo_ocorrencia":
                inicio, fim, modo = faixa
                setattr(registro, attr, transforma_motivo(linha[inicio : fim + 1], modo))
            else:
                setattr(registro, attr, extrai_campo(linha, faixa))

    registros = []
    for i in range(0, len(detalhes) - 1, 2):
        par = detalhes[i : i + 2]
        registro = RegistroRetorno()
        for linha in par:
            tipo = linha[13:14]
            campos = layout["T"] if tipo == "T" else layout["U"]
            aplica(registro, linha, campos)
        registros.append(registro)
    return registros
