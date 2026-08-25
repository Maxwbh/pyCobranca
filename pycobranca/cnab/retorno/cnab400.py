"""Parsing de retorno CNAB 400.

Cada banco é identificado pelo código lido do header (posições 76–78) e possui
um mapa posicional próprio. O **header** (primeira linha, tipo 0) e o **trailer**
(tipo 9) são ignorados: ``registros`` contém apenas os registros de detalhe
(títulos), não os registros de controle.
"""

from __future__ import annotations

from ...core.dv import modulo11_flex
from .base import RegistroRetorno, extrai_campo, transforma_motivo

__all__ = ["parse_cnab400", "banco_do_arquivo_400", "LAYOUTS_400"]

# Mapa posicional por banco: {atributo: (inicio, fim)} com faixas inclusivas.
# ``motivo_ocorrencia`` recebe uma tupla extra (inicio, fim, modo).
LAYOUTS_400: dict[str, dict[str, tuple]] = {
    "077": {  # Banco Inter — manual CNAB400 v2.2, seção 5.2 (posições 1-based no manual)
        # Layout bem distante do comum: a ocorrência fica em 90-91, não em 109-110,
        # e o vencimento em 119-124, não em 147-152. Sem esta entrada o parser cairia
        # no fallback do Itaú e leria "seu número" como código de ocorrência — erro
        # silencioso, com o arquivo inteiro parecendo válido.
        "codigo_registro": (0, 0),
        "cedente_com_dv": (3, 16),  # 004-017 inscrição da empresa
        "carteira": (20, 22),  # 021-023
        "agencia_sem_dv": (23, 26),  # 024-027 — agência única 0001
        "convenio": (27, 36),  # 028-037 conta corrente
        "nosso_numero": (70, 80),  # 071-081 nosso número + DV
        "codigo_ocorrencia": (89, 90),  # 090-091
        "data_ocorrencia": (91, 96),  # 092-097
        "documento_numero": (97, 106),  # 098-107 "seu número"
        "data_vencimento": (118, 123),  # 119-124
        "valor_titulo": (124, 136),  # 125-137
        "banco_recebedor": (137, 139),  # 138-140
        "agencia_recebedora_com_dv": (140, 143),  # 141-144
        "especie_documento": (144, 145),  # 145-146
        "valor_recebido": (159, 171),  # 160-172 valor pago
        "data_credito": (172, 177),  # 173-178
        "motivo_ocorrencia": (240, 379, "raw"),  # 241-380 motivo da rejeição
        "sequencial": (394, 399),  # 395-400
    },
    "341": {  # Itaú
        "codigo_registro": (0, 0),
        "agencia_com_dv": (17, 20),
        "cedente_com_dv": (23, 28),
        "nosso_numero": (62, 69),
        "carteira_variacao": (82, 84),
        "carteira": (107, 107),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "especie_documento": (173, 174),
        "valor_tarifa": (175, 187),
        "iof": (214, 226),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "outros_recebimento": (279, 291),
        "data_credito": (295, 300),
        "motivo_ocorrencia": (377, 384, "chunk2"),
        "sequencial": (394, 399),
    },
    "237": {  # Bradesco
        "codigo_registro": (0, 0),
        "carteira": (21, 23),
        "agencia_sem_dv": (24, 28),
        "cedente_com_dv": (29, 36),
        "nosso_numero": (70, 81),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "documento_numero": (116, 125),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "especie_documento": (173, 174),
        "valor_tarifa": (175, 187),
        "iof": (214, 226),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "outros_recebimento": (279, 291),
        "data_credito": (295, 300),
        "motivo_ocorrencia": (318, 327, "chunk2"),
        "sequencial": (394, 399),
    },
    "001": {  # Banco do Brasil
        "codigo_registro": (0, 0),
        "agencia_com_dv": (17, 21),
        "cedente_com_dv": (22, 30),
        "nosso_numero": (63, 79),
        "motivo_ocorrencia": (86, 87, "bb2"),
        "carteira_variacao": (91, 93),
        "carteira": (106, 107),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "especie_documento": (173, 174),
        "data_credito": (175, 180),
        "valor_tarifa": (181, 187),
        "iof": (214, 226),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "outros_recebimento": (279, 291),
        "sequencial": (394, 399),
    },
    "033": {  # Santander (inclui campos PIX)
        "codigo_registro": (0, 0),
        "tipo_chave_dict": (1, 1),
        "codigo_chave_dict": (2, 78),
        "txid": (79, 113),
        "agencia_com_dv": (17, 20),
        "cedente_com_dv": (23, 28),
        "nosso_numero": (62, 69),
        "carteira": (107, 107),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "motivo_ocorrencia": (136, 145, "chunk2"),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "especie_documento": (173, 174),
        "valor_tarifa": (175, 187),
        "iof": (214, 226),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "outros_recebimento": (279, 291),
        "data_credito": (295, 300),
        "sequencial": (394, 399),
    },
    "004": {  # Banco do Nordeste
        "codigo_registro": (0, 0),
        "agencia_sem_dv": (17, 20),
        "cedente_com_dv": (23, 30),
        "nosso_numero": (62, 69),
        "carteira": (107, 107),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "especie_documento": (173, 174),
        "valor_tarifa": (175, 187),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "data_credito": (146, 151),
        "motivo_ocorrencia": (279, 393, "raw"),
        "sequencial": (394, 399),
    },
    "041": {  # Banrisul
        "codigo_registro": (0, 0),
        "agencia_sem_dv": (17, 20),
        "cedente_com_dv": (21, 29),
        "nosso_numero": (62, 71),
        "carteira": (107, 107),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "especie_documento": (173, 174),
        "valor_tarifa": (175, 187),
        "iof": (188, 200),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "outros_recebimento": (279, 291),
        "data_credito": (295, 300),
        "motivo_ocorrencia": (382, 391, "raw"),
        "sequencial": (394, 399),
    },
    "097": {  # CrediSIS
        "codigo_registro": (0, 0),
        "nosso_numero": (62, 72),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "valor_recebido": (253, 265),
        "data_credito": (175, 180),
        "sequencial": (394, 399),
    },
    "336": {  # C6
        "codigo_registro": (0, 0),
        "cedente_com_dv": (17, 28),
        "documento_numero": (37, 61),
        "nosso_numero": (62, 72),
        "carteira": (106, 107),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 115),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "valor_tarifa": (175, 187),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "outros_recebimento": (279, 291),
        "data_credito": (295, 300),
        "motivo_ocorrencia": (377, 392, "chunk4"),
        "sequencial": (394, 399),
    },
    "136": {  # Unicred
        "codigo_registro": (0, 0),
        "agencia_sem_dv": (17, 20),
        "cedente_com_dv": (22, 30),
        "nosso_numero": (45, 61),
        "codigo_ocorrencia": (108, 109),
        "data_credito": (110, 115),
        "data_vencimento": (146, 151),
        "valor_titulo": (152, 164),
        "banco_recebedor": (165, 167),
        "agencia_recebedora_com_dv": (168, 172),
        "valor_tarifa": (181, 187),
        "valor_abatimento": (227, 239),
        "desconto": (240, 252),
        "valor_recebido": (253, 265),
        "juros_mora": (266, 278),
        "motivo_ocorrencia": (318, 325, "chunk2"),
        "sequencial": (394, 399),
    },
    "070": {  # Banco de Brasília / BRB (datas de 8 posições)
        "codigo_registro": (0, 0),
        "cedente_com_dv": (20, 36),
        "nosso_numero": (70, 81),
        "codigo_ocorrencia": (108, 109),
        "data_ocorrencia": (110, 117),
        "data_vencimento": (148, 155),
        "valor_titulo": (156, 168),
        "banco_recebedor": (169, 171),
        "especie_documento": (177, 178),
        "valor_tarifa": (179, 191),
        "iof": (218, 230),
        "valor_abatimento": (231, 243),
        "desconto": (244, 256),
        "valor_recebido": (257, 269),
        "outros_recebimento": (283, 295),
        "data_credito": (299, 306),
        "motivo_ocorrencia": (364, 393, "raw"),
        "sequencial": (394, 399),
    },
}


def banco_do_arquivo_400(primeira_linha: str) -> str:
    """Código do banco no header do retorno CNAB 400 (posições 76–78)."""
    return primeira_linha[76:79]


def parse_cnab400(linhas: list[str], codigo_banco: str) -> list[RegistroRetorno]:
    layout = LAYOUTS_400.get(codigo_banco)
    if layout is None:
        # fallback: layout do Itaú (equivalente ao RetornoCnab400 legado)
        layout = LAYOUTS_400["341"]
    registros = []
    for linha in linhas[1:]:  # ignora o header (except: [1])
        if not linha.strip():
            continue
        if linha[0] == "9":  # ignora o trailer: registro de controle, não é título
            continue
        registro = RegistroRetorno()
        for attr, faixa in layout.items():
            if attr == "motivo_ocorrencia":
                inicio, fim, modo = faixa
                bruto = linha[inicio : fim + 1]
                setattr(registro, attr, transforma_motivo(bruto, modo))
            else:
                setattr(registro, attr, extrai_campo(linha, faixa))
        # Bradesco calcula a agência com DV a partir da agência sem DV (módulo 11).
        if codigo_banco == "237" and registro.agencia_sem_dv:
            dv = modulo11_flex(registro.agencia_sem_dv)
            registro.agencia_com_dv = f"{registro.agencia_sem_dv}-{dv}"
        registros.append(registro)
    return registros
