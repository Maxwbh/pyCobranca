"""Contrato de dados para consumo via API REST.

Serialização dos artefatos (boleto, pagamento, remessa, retorno) para schemas
JSON (OpenAPI 3.0) e validador leve para os testes de contrato.
Ver :mod:`pycobranca.contracts.contrato_rest`.
"""

from .contrato_rest import (
    CONTRATO,
    SLUG_POR_CODIGO,
    ErroDeContrato,
    boleto_para_api,
    pagamento_para_api,
    remessa_para_api,
    retorno_item_para_api,
    valida_contrato,
)

__all__ = [
    "CONTRATO",
    "SLUG_POR_CODIGO",
    "ErroDeContrato",
    "boleto_para_api",
    "pagamento_para_api",
    "remessa_para_api",
    "retorno_item_para_api",
    "valida_contrato",
]
