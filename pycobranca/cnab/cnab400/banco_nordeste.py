"""Remessa CNAB 400 — Banco do Nordeste (004).

O registro detalhe é gerado com **401 posições** (um caractere a mais em
relação ao padrão FEBRABAN de 400, conforme o layout do banco); por isso
``tamanho_registro`` é
``None`` e a garantia passa a ser a comparação byte a byte com a fixture.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBancoNordeste400"]


@dataclass
class RemessaBancoNordeste400(RemessaCnab400Base):
    emissao_boleto: str = "2"
    tamanho_registro: int | None = None

    def cod_banco(self) -> str:
        return "004"

    def nome_banco(self) -> str:
        return "B.DO NORDESTE".ljust(15)

    def _agencia(self) -> str:
        return so_digitos(self.agencia).rjust(4, "0")

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente).rjust(7, "0")

    def info_conta(self) -> str:
        return f"{self._agencia()}00{self._conta()}{self.digito_conta}" + " " * 6

    def complemento(self) -> str:
        return " " * 294

    def _codigo_carteira(self) -> str:
        carteira = so_digitos(self.carteira).rjust(2, "0")
        if carteira == "51":
            return "I"
        carteiras = {
            "1": {"21": "1", "41": "2"},
            "2": {"21": "4", "41": "5"},
        }
        return carteiras[str(self.emissao_boleto)][carteira]

    def _digito_nosso_numero(self, nosso_numero: str) -> str:
        return str(
            modulo11_flex(
                so_digitos(nosso_numero).rjust(7, "0"),
                fatores=(2, 3, 4, 5, 6, 7, 8),
                mapa={1: 0, 10: 0, 11: 0},
                bloco=lambda total: 11 - (total % 11),
            )
        )

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + " " * 16
            + self._agencia()
            + "0" * 2
            + self._conta()
            + self.digito_conta
            + pagamento.formata_percentual_multa()[0:2]
            + " " * 4
            + str(pagamento.documento_ou_numero).ljust(25)
            + so_digitos(pagamento.nosso_numero).rjust(7, "0")
            + self._digito_nosso_numero(pagamento.nosso_numero)
            + "0" * 10
            + "0" * 6
            + "0" * 13
            + " " * 8
            + self._codigo_carteira()
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + "0" * 4
            + " "
            + "01"
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%y")
            + "0" * 4
            + pagamento.formata_valor_mora()
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_valor_iof()
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado()
            + so_digitos(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 40)
            + self._format_size(pagamento.endereco_sacado, 40)
            + self._format_size(pagamento.bairro_sacado, 12)
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + self._format_size(pagamento.nome_avalista, 40)
            + "99"
            + "0"
            + str(sequencial).rjust(6, "0")
        )
