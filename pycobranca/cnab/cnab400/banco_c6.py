"""Remessa CNAB 400 — Banco C6 (336).

Layout do manual oficial "Cobrança Bancária Padrão CNAB 400 Posições" do C6 Bank.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBancoC6_400"]


@dataclass
class RemessaBancoC6_400(RemessaCnab400Base):
    codigo_beneficiario: str = ""

    def __post_init__(self) -> None:
        if not self.carteira:
            self.carteira = "10"

    def cod_banco(self) -> str:
        return "336"

    def nome_banco(self) -> str:
        return " " * 15

    def _codigo_beneficiario(self) -> str:
        return so_digitos(self.codigo_beneficiario).rjust(12, "0")

    def info_conta(self) -> str:
        return self._codigo_beneficiario() + " " * 8

    def complemento(self) -> str:
        return (
            " " * 8
            + self._codigo_beneficiario()
            + " " * 266
            + so_digitos(self.sequencial_remessa).rjust(8, "0")
        )

    def _carteira(self) -> str:
        return so_digitos(self.carteira).rjust(2, "0")

    def _nosso_numero_remessa(self, pagamento: Pagamento) -> str:
        if self._carteira() == "10":
            return " " * 11
        return "0" + so_digitos(pagamento.nosso_numero).rjust(10, "0")

    def _dv_nosso_numero(self, pagamento: Pagamento) -> str:
        if self._carteira() == "10":
            return " "
        base = "0" + self._carteira() + so_digitos(pagamento.nosso_numero).rjust(10, "0")
        return str(
            modulo11_flex(
                base,
                fatores=(2, 3, 4, 5, 6, 7),
                mapa={10: "P", 11: 0},
                bloco=lambda total: 11 - (total % 11),
            )
        )

    def _banco_cobranca_direta(self) -> str:
        return self.cod_banco() if self._carteira() == "20" else "000"

    @staticmethod
    def _indicador_multa(pagamento: Pagamento) -> str:
        return "2" if int(pagamento.codigo_multa or "0") > 0 else "0"

    @staticmethod
    def _percentual_multa(pagamento: Pagamento) -> str:
        valor = int(round(float(pagamento.percentual_multa)))
        return str(valor).rjust(2, "0")[:2]

    @staticmethod
    def _formata_data_juros(pagamento: Pagamento) -> str:
        return pagamento.data_mora.strftime("%d%m%y") if pagamento.data_mora else "000000"

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + "02"
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
            + self._codigo_beneficiario()
            + " " * 8
            + str(pagamento.documento_ou_numero).ljust(25)[:25]
            + self._nosso_numero_remessa(pagamento)
            + self._dv_nosso_numero(pagamento)
            + " " * 8
            + self._banco_cobranca_direta()
            + " " * 21
            + self._carteira()
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + " " * 8
            + pagamento.especie_titulo.rjust(2, "0")
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%y")
            + "00"
            + "00"
            + pagamento.formata_valor_mora()
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_data_multa()
            + " " * 7
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado()
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 40)
            + self._format_size(pagamento.endereco_sacado, 40)
            + self._format_size(pagamento.bairro_sacado, 12)
            + so_digitos(pagamento.cep_sacado).rjust(8, "0")
            + self._format_size(pagamento.cidade_sacado, 15)
            + str(pagamento.uf_sacado).rjust(2)[:2]
            + self._format_size(pagamento.nome_avalista, 30)
            + self._indicador_multa(pagamento)
            + self._percentual_multa(pagamento)
            + " "
            + self._formata_data_juros(pagamento)
            + " " * 3
            + str(sequencial).rjust(6, "0")
        )
