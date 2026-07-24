"""Contrato de dados para consumo via API REST.

Este módulo **não** faz chamadas HTTP (o SDK é um projeto à parte). Ele traduz
os artefatos da engine (boleto, remessa, retorno) para o formato exato dos
schemas REST (OpenAPI 3.0) e oferece um validador leve para os **testes de
contrato**, garantindo que a serialização permaneça compatível conforme a API
evolui.

Fonte do contrato: :data:`CONTRATO` (``contrato_rest.json``), curado de
um ``openapi.yaml`` de referência (v1.5.0).
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

__all__ = [
    "CONTRATO",
    "SLUG_POR_CODIGO",
    "boleto_para_api",
    "pagamento_para_api",
    "remessa_para_api",
    "retorno_item_para_api",
    "valida_contrato",
    "ErroDeContrato",
]

_CAMINHO_CONTRATO = Path(__file__).with_name("contrato_rest.json")
CONTRATO: dict[str, Any] = json.loads(_CAMINHO_CONTRATO.read_text(encoding="utf-8"))

#: Código FEBRABAN → slug do banco aceito pela API (``bank``).
SLUG_POR_CODIGO: dict[str, str] = {
    "001": "banco_brasil",
    "004": "banco_nordeste",
    "021": "banestes",
    "033": "santander",
    "041": "banrisul",
    "070": "banco_brasilia",
    "085": "ailos",
    "097": "credisis",
    "104": "caixa",
    "136": "unicred",
    "237": "bradesco",
    "336": "banco_c6",
    "341": "itau",
    "399": "hsbc",
    "422": "safra",
    "745": "citibank",
    "748": "sicredi",
    "756": "sicoob",
}


class ErroDeContrato(ValueError):
    """Falha de validação de um artefato contra o contrato REST."""


# --------------------------------------------------------------------------- #
# Serializadores (engine → formato da API)
# --------------------------------------------------------------------------- #
def _num(valor: Decimal | str | float | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def _data_iso(valor: date | None) -> str | None:
    return valor.isoformat() if valor else None


def _sem_nulos(dados: dict) -> dict:
    return {k: v for k, v in dados.items() if v is not None}


def boleto_para_api(banco) -> dict[str, Any]:
    """Serializa um boleto (:class:`~pycobranca.bancos.base.BancoBase`) para o
    corpo esperado por ``GET /api/boleto`` — ``{"bank": slug, "data": BoletoData}``."""
    data: dict[str, Any] = {
        "agencia": banco.agencia,
        "conta_corrente": banco.conta,
        "nosso_numero": banco.nosso_numero,
        "valor": _num(banco.valor),
        "cedente": banco.cedente,
        "documento_cedente": banco.cedente_documento,
        "sacado": banco.sacado,
        "sacado_documento": banco.sacado_documento,
        "carteira": banco.carteira or None,
        "convenio": banco.convenio or None,
        "data_vencimento": _data_iso(banco.data_vencimento),
        "numero_documento": getattr(banco, "numero_documento", "") or None,
        "sacado_endereco": getattr(banco, "sacado_endereco", "") or None,
    }
    # Bolepix: quando o banco suporta PIX e há chave configurada.
    if getattr(banco, "suporta_pix", False) and getattr(banco, "pix_chave", ""):
        data["chave_pix"] = banco.pix_chave
        if getattr(banco, "pix_txid", ""):
            data["txid"] = banco.pix_txid
    return {"bank": SLUG_POR_CODIGO.get(banco.codigo, banco.codigo), "data": _sem_nulos(data)}


def pagamento_para_api(pagamento) -> dict[str, Any]:
    """Serializa um :class:`~pycobranca.cnab.pagamento.Pagamento` para o schema
    ``Pagamento`` da remessa."""
    dados = {
        "nosso_numero": pagamento.nosso_numero,
        "numero_documento": pagamento.documento_ou_numero or None,
        "data_vencimento": _data_iso(pagamento.data_vencimento),
        "valor": _num(pagamento.valor),
        "nome_sacado": pagamento.nome_sacado or None,
        "documento_sacado": pagamento.documento_sacado or None,
        "endereco_sacado": pagamento.endereco_sacado or None,
        "bairro_sacado": pagamento.bairro_sacado or None,
        "cidade_sacado": pagamento.cidade_sacado or None,
        "uf_sacado": pagamento.uf_sacado or None,
        "cep_sacado": pagamento.cep_sacado or None,
    }
    return _sem_nulos(dados)


def remessa_para_api(remessa) -> dict[str, Any]:
    """Serializa uma remessa (``RemessaCnab400Base``/``RemessaCnab240Base``) para
    o schema ``RemessaRequest``."""

    def opt(attr: str) -> str | None:
        valor = getattr(remessa, attr, "") or ""
        return valor or None

    sequencial = getattr(remessa, "sequencial_remessa", None)
    sequencial_texto = "" if sequencial is None else str(sequencial)
    sequencial_int = int(sequencial_texto) if sequencial_texto.isdigit() else None

    dados: dict[str, Any] = {
        "empresa_mae": remessa.empresa_mae,
        "documento_cedente": remessa.documento_cedente,
        "agencia": remessa.agencia,
        "conta_corrente": remessa.conta_corrente,
        "digito_conta": opt("digito_conta"),
        "convenio": opt("convenio"),
        "carteira": opt("carteira"),
        "variacao_carteira": opt("variacao_carteira"),
        "codigo_beneficiario": opt("codigo_beneficiario"),
        "sequencial_remessa": sequencial_int,
        "pagamentos": [pagamento_para_api(p) for p in remessa.pagamentos],
    }
    return _sem_nulos(dados)


def _valor_centavos(bruto: str | None) -> float | None:
    if not bruto:
        return None
    digitos = "".join(c for c in str(bruto) if c.isdigit())
    return int(digitos) / 100 if digitos else None


def retorno_item_para_api(registro, layout: str = "400") -> dict[str, Any]:
    """Serializa um :class:`~pycobranca.cnab.retorno.RegistroRetorno` para o
    schema ``RetornoItem`` (visão curada do retorno da API).

    Os valores monetários crus (centavos) viram ``float`` em reais e
    ``motivo_ocorrencia`` vira o rótulo legível da ocorrência.
    """
    from ..cnab.retorno.ocorrencias import descreve_ocorrencia

    dados = {
        "nosso_numero": registro.nosso_numero or None,
        "numero_documento": registro.documento_numero or None,
        "data_credito": registro.data_credito or None,
        "data_ocorrencia": registro.data_ocorrencia or None,
        "valor_titulo": _valor_centavos(registro.valor_titulo),
        "valor_pago": _valor_centavos(registro.valor_recebido),
        "valor_tarifa": _valor_centavos(registro.valor_tarifa),
        "codigo_ocorrencia": registro.codigo_ocorrencia or None,
        "motivo_ocorrencia": descreve_ocorrencia(registro.codigo_ocorrencia, layout),
    }
    return _sem_nulos(dados)


# --------------------------------------------------------------------------- #
# Validador de contrato (subconjunto de JSON Schema suficiente para os schemas)
# --------------------------------------------------------------------------- #
_TIPOS = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "array": list,
    "object": dict,
    "boolean": bool,
}


def valida_contrato(dados: dict, schema_nome: str) -> None:
    """Valida ``dados`` contra o schema ``schema_nome`` do contrato.

    Verifica campos obrigatórios, tipos declarados, ``enum`` e itens de array
    (via ``$ref``). Levanta :class:`ErroDeContrato` na primeira violação.
    Campos extras são permitidos (``additionalProperties`` implícito).
    """
    schema = CONTRATO["schemas"].get(schema_nome)
    if schema is None:
        raise ErroDeContrato(f"schema desconhecido: {schema_nome!r}")
    if not isinstance(dados, dict):
        raise ErroDeContrato(f"{schema_nome}: esperado objeto, recebido {type(dados).__name__}")

    for obrigatorio in schema.get("required", []):
        if dados.get(obrigatorio) in (None, ""):
            raise ErroDeContrato(f"{schema_nome}: campo obrigatório ausente/vazio: {obrigatorio!r}")

    propriedades = schema.get("properties", {})
    for chave, valor in dados.items():
        regra = propriedades.get(chave)
        if regra is None:
            continue  # additionalProperties permitido
        tipo = regra.get("type")
        if tipo == "array":
            if not isinstance(valor, list):
                raise ErroDeContrato(f"{schema_nome}.{chave}: esperado array")
            ref = regra.get("items", {}).get("$ref")
            if ref:
                for item in valor:
                    valida_contrato(item, ref)
            continue
        esperado = _TIPOS.get(tipo)
        if esperado and not isinstance(valor, esperado):
            raise ErroDeContrato(
                f"{schema_nome}.{chave}: esperado {tipo}, recebido {type(valor).__name__}"
            )
        if "enum" in regra and valor not in regra["enum"]:
            raise ErroDeContrato(f"{schema_nome}.{chave}: valor {valor!r} fora do enum")
