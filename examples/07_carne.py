"""Carnê: 12 parcelas, 3 por página A4.

    python examples/07_carne.py

Cada parcela é um boleto completo; o carnê só cuida da paginação.
"""

from __future__ import annotations

from datetime import date

from _comum import grava, titulo

from pycobranca.bancos import Bancos
from pycobranca.render import render_carne_pdf


def vencimento(parcela: int) -> date:
    """1º vencimento em 15/08/2026, depois todo dia 15."""
    mes = 8 + parcela - 1
    return date(2026 + (mes - 1) // 12, (mes - 1) % 12 + 1, 15)


def main() -> None:
    Banco = Bancos.find("341")
    total = 12

    parcelas = []
    for parcela in range(1, total + 1):
        boleto = Banco(
            valor="199.90",
            cedente="Empresa Exemplo LTDA",
            cedente_documento="11222333000181",
            agencia="0057",
            conta="12345",
            carteira="109",
            nosso_numero=f"{12345678 + parcela:08d}",
            numero_documento=f"{parcela:02d}/{total}",
            data_vencimento=vencimento(parcela),
            sacado="Cliente Final da Silva",
            sacado_documento="52998224725",
        )
        boleto.validar()
        parcelas.append(boleto.contexto_render())

    titulo(f"Carnê — {total} parcelas ({(total + 2) // 3} páginas A4)")
    print("1ª parcela vence em", parcelas[0]["vencimento"])
    print("Última parcela vence em", parcelas[-1]["vencimento"])
    grava("07-carne.pdf", render_carne_pdf({"parcelas": parcelas}))


if __name__ == "__main__":
    main()
