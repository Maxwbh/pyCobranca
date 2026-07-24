"""Remessa CNAB 400 — Citibank (745)."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaCitibank400"]


@dataclass
class RemessaCitibank400(RemessaCnab400Base):
    portfolio: str = ""

    def __post_init__(self) -> None:
        if not self.carteira:
            self.carteira = "1"

    def cod_banco(self) -> str:
        return "745"

    def nome_banco(self) -> str:
        return "CITIBANK".ljust(15)

    def _portfolio(self) -> str:
        return str(self.portfolio).rjust(20)

    def _tipo_empresa(self) -> str:
        return "01" if len(so_digitos(self.documento_cedente)) <= 11 else "02"

    def info_conta(self) -> str:
        return self._portfolio()

    def complemento(self) -> str:
        return "01600BPI".rjust(294)

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + self._tipo_empresa()
            + so_digitos(self.documento_cedente).rjust(14, "0")
            + self._portfolio()
            + str(pagamento.documento_ou_numero).ljust(25)
            + pagamento.especie_titulo
            + so_digitos(pagamento.nosso_numero).rjust(12, "0")
            + " " * 6
            + pagamento.formata_data_segundo_desconto()
            + pagamento.formata_valor_segundo_desconto()
            + "000"
            + "000"
            + so_digitos(self.carteira)
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + "0" * 5
            + "07"
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%y")
            + "00"
            + "00"
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
            + " " * 2
            + "9"
            + str(sequencial).rjust(6, "0")
        )
