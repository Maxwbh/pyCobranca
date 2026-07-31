"""Contrato de erros: como uma camada de serviço trata `BoletoInvalido`.

    python examples/10_validacao_erros.py

`BoletoInvalido` carrega `.erros` — uma lista com **um item por problema** —
além da mensagem única. É o que permite devolver todas as violações de uma vez
(ex.: um 422 com a lista completa), em vez de uma por requisição.
"""

from __future__ import annotations

from datetime import date

from _comum import titulo

from pycobranca.bancos import Bancos
from pycobranca.exceptions import BoletoInvalido


def emite(**campos):
    """Tenta emitir e devolve a lista de erros (vazia quando válido)."""
    Banco = Bancos.find("341")
    base = dict(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    try:
        Banco(**{**base, **campos}).validar()
    except BoletoInvalido as erro:
        return erro.erros
    return []


def main() -> None:
    titulo("Boleto válido")
    print("  erros:", emite() or "nenhum")

    titulo("Carteira fora do conjunto aceito pelo banco")
    for erro in emite(carteira="999"):
        print("  •", erro)

    titulo("Vários problemas de uma vez (tamanho e documento)")
    for erro in emite(agencia="123456", conta="1234567890", sacado_documento="11111111111"):
        print("  •", erro)

    titulo("Tratamento típico numa camada de serviço")
    erros = emite(carteira="999", agencia="123456", nosso_numero="1234567890123")
    resposta = {"status": 422, "erros": erros}
    print(" ", resposta)


if __name__ == "__main__":
    main()
