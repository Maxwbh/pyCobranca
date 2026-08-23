"""Boleto híbrido com PIX (Bolepix): BR Code copia-e-cola + QR no PDF.

    python examples/02_bolepix.py

O QR entra no PDF automaticamente quando o contexto tem dados de PIX.
"""

from __future__ import annotations

from datetime import date

from _comum import grava, titulo

from pycobranca.bancos import Bancos
from pycobranca.render import render_boleto_pdf


def main() -> None:
    Banco = Bancos.find("237")  # Bradesco
    boleto = Banco(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="1234",
        conta="56789",
        carteira="09",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final",
        sacado_documento="52998224725",
        cedente_cidade="SAO PAULO",
        pix_chave="11222333000181",
        pix_txid="TX2026080100001",
    )
    boleto.validar()

    titulo(f"Bolepix {Banco.nome} ({Banco.codigo})")
    print("Linha digitável:", boleto.linha_digitavel)

    contexto = boleto.contexto_render()
    pix = contexto.get("pix") or {}
    copia_cola = pix.get("copia_cola", "")
    print("BR Code (EMV):  ", copia_cola[:60], "...")
    print("CRC16 (4 finais):", copia_cola[-4:])
    print("QR:              matriz", len(pix.get("qrcode_matrix") or []), "módulos")

    # O QR entra no PDF automaticamente quando há dados de PIX no contexto.
    grava("02-bolepix.pdf", render_boleto_pdf(contexto, modelo="moderno"))


if __name__ == "__main__":
    main()
