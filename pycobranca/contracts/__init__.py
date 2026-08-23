"""Contrato de dados para consumo via API REST.

Serialização dos artefatos (boleto, pagamento, remessa, retorno) para schemas
JSON (OpenAPI 3.0) e validador leve para os testes de contrato.
Ver :mod:`pycobranca.contracts.contrato_rest`.
"""

from .contrato_rest import (
    CAMPOS_POR_BANCO,
    CONTRATO,
    NOMES_DO_CONTRATO,
    SLUG_POR_CODIGO,
    TEMA_DO_CONTRATO,
    TOTALIZADORES,
    ErroDeContrato,
    boleto_de_api,
    boleto_para_api,
    pagamento_para_api,
    remessa_para_api,
    retorno_item_para_api,
    tema_de_api,
    valida_contrato,
)

__all__ = [
    "CONTRATO",
    "CAMPOS_POR_BANCO",
    "NOMES_DO_CONTRATO",
    "SLUG_POR_CODIGO",
    "TEMA_DO_CONTRATO",
    "TOTALIZADORES",
    "ErroDeContrato",
    "boleto_de_api",
    "boleto_para_api",
    "pagamento_para_api",
    "remessa_para_api",
    "retorno_item_para_api",
    "tema_de_api",
    "valida_contrato",
]
