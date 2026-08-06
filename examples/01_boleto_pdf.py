"""Emitir um boleto: linha digitável, código de barras e PDF (dois modelos).

    python examples/01_boleto_pdf.py

Gera três PDFs em examples/saida/: modelo moderno, clássico e com logo.
"""

from __future__ import annotations

from datetime import date

from _comum import grava, titulo

from pycobranca.bancos import Bancos
from pycobranca.render import logo_do_banco, render_boleto_pdf


def main() -> None:
    Banco = Bancos.find("341")  # Itaú, pelo código FEBRABAN
    boleto = Banco(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11.222.333/0001-81",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="529.982.247-25",
    )

    # Levanta BoletoInvalido (com .erros) se algum campo violar as regras do banco.
    boleto.validar()

    titulo(f"Boleto {Banco.nome} ({Banco.codigo})")
    print("Linha digitável:", boleto.linha_digitavel)
    print("Código de barras:", boleto.codigo_barras)
    print("Nosso número:   ", boleto.nosso_numero_formatado())
    print("Agência/Conta:  ", boleto.agencia_conta_formatado())

    contexto = boleto.contexto_render()
    titulo("PDFs")
    grava("01-boleto-moderno.pdf", render_boleto_pdf(contexto, modelo="moderno"))
    grava("01-boleto-classico.pdf", render_boleto_pdf(contexto, modelo="classico"))

    # Logo do banco no cabeçalho (opt-in): arquivo próprio ou um dos empacotados.
    boleto.logo = logo_do_banco("341")
    grava("01-boleto-com-logo.pdf", render_boleto_pdf(boleto.contexto_render()))


if __name__ == "__main__":
    main()
