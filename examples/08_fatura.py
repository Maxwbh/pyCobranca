"""Fatura = corpo livre + boleto na mesma página, nos três níveis de liberdade.

    python examples/08_fatura.py

Nível 1 ``itens``      — a tabela pronta (o caso comum).
Nível 2 ``fatura.blocos`` — corpo declarativo (campos, tabela, texto, total…).
Nível 3 ``fatura.desenhar`` — um callable com liberdade total sobre a Tela.
"""

from __future__ import annotations

from datetime import date

from _comum import grava, titulo

from pycobranca.bancos import Bancos
from pycobranca.render import render_fatura_pdf


def contexto_base(valor: str) -> dict:
    Banco = Bancos.find("341")
    boleto = Banco(
        valor=valor,
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
    boleto.validar()
    return boleto.contexto_render()


def nivel_1_itens() -> None:
    """A tabela pronta: descrição, quantidade e valor."""
    contexto = contexto_base("127.50")
    contexto["itens"] = [
        {"descricao": "Mensalidade — agosto/2026", "quantidade": 1, "valor": 99.90},
        {"descricao": "Serviço adicional", "quantidade": 2, "valor_unitario": 13.80},
    ]
    grava("08-fatura-nivel1-itens.pdf", render_fatura_pdf(contexto))


def nivel_2_blocos() -> None:
    """Corpo declarativo — serve a qualquer modalidade (consumo, condomínio…)."""
    contexto = contexto_base("127.50")
    contexto["fatura"] = {
        "titulo": "Fatura de Serviços",
        "blocos": [
            {
                "tipo": "campos",
                "itens": [("Período", "01/08 a 31/08/2026"), ("Contrato", "4471")],
            },
            {
                "tipo": "tabela",
                "colunas": ["Descrição", "Qtd.", "Unitário", "Total"],
                "linhas": [
                    ["Consumo medido (m³)", "18", "3,50", "63,00"],
                    ["Taxa de disponibilidade", "1", "64,50", "64,50"],
                ],
                "alinhamento": "llrr",
            },
            {"tipo": "texto", "conteudo": "Leitura registrada em <b>18/08/2026</b>."},
            {"tipo": "total", "rotulo": "Total da fatura", "valor": 127.50},
        ],
    }
    grava("08-fatura-nivel2-blocos.pdf", render_fatura_pdf(contexto))


def nivel_3_desenhar() -> None:
    """Liberdade total: desenha direto na Tela e o boleto vem abaixo."""

    def corpo(tela, info) -> None:
        tela.avanca(4)
        tela.texto(
            tela.x_(0),
            tela.y_(),
            "DEMONSTRATIVO PERSONALIZADO",
            fonte="Helvetica-Bold",
            tam=12,
            cor=tela.marca,
        )
        tela.avanca(8)
        tela.texto(tela.x_(0), tela.y_(), f"Beneficiário: {info.beneficiario_nome}")
        tela.avanca(5)
        tela.texto(tela.x_(0), tela.y_(), f"Valor do documento: {info.valor_documento}")
        tela.avanca(6)

    contexto = contexto_base("127.50")
    contexto["fatura"] = {"desenhar": corpo}
    grava("08-fatura-nivel3-desenhar.pdf", render_fatura_pdf(contexto))


def main() -> None:
    titulo("Fatura — nível 1 (itens)")
    nivel_1_itens()
    titulo("Fatura — nível 2 (blocos declarativos)")
    nivel_2_blocos()
    titulo("Fatura — nível 3 (callable)")
    nivel_3_desenhar()


if __name__ == "__main__":
    main()
