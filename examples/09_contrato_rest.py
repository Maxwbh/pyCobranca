"""Contrato REST: serializar os artefatos em JSON e validar o payload.

    python examples/09_contrato_rest.py

A PyCobrança não fala HTTP — ela entrega o contrato (OpenAPI 3.0), os
serializadores e um validador leve. Quem expõe a API é a sua camada web.
"""

from __future__ import annotations

import json
from datetime import date

from _comum import titulo

from pycobranca.bancos import Bancos
from pycobranca.contracts import (
    CONTRATO,
    ErroDeContrato,
    boleto_para_api,
    valida_contrato,
)


def main() -> None:
    Banco = Bancos.find("341")
    boleto = Banco(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="12ABC34501DE35",  # CNPJ alfanumérico (IN RFB 2.229/2024)
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="529.982.247-25",
    )
    boleto.validar()

    payload = boleto_para_api(boleto)

    titulo("Payload GET /api/boleto")
    print(json.dumps(payload, ensure_ascii=False, indent=2)[:600], "...")

    titulo("Validação contra o contrato")
    valida_contrato(payload["data"], "BoletoData")
    print("  ✓ BoletoData válido")

    # O contrato tem `pattern` nos campos de documento: um serviço HTTP rejeita
    # o formato antes mesmo de chamar a engine.
    invalido = dict(payload["data"], sacado_documento="123")
    try:
        valida_contrato(invalido, "BoletoData")
    except ErroDeContrato as erro:
        print("  ✓ documento malformado recusado:", erro)

    titulo("Schemas disponíveis")
    print(" ", ", ".join(sorted(CONTRATO["schemas"])))


if __name__ == "__main__":
    main()
