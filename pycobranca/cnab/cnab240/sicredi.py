"""Remessa CNAB 240 — Sicredi (748)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ...core.documentos import so_digitos
from ..pagamento import Pagamento
from .base import RemessaCnab240Base

__all__ = ["RemessaSicredi240"]


@dataclass
class RemessaSicredi240(RemessaCnab240Base):
    modalidade_carteira: str = "01"
    parcela: str = "01"
    posto: str = "00"
    byte_idt: str = ""

    def __post_init__(self) -> None:
        self.especie_titulo = "03"
        self.forma_cadastramento = "1"
        self.tipo_documento = "1"

    def cod_banco(self) -> str:
        return "748"

    def nome_banco(self) -> str:
        return "SICREDI".ljust(30)

    def versao_layout_arquivo(self) -> str:
        return "081"

    def versao_layout_lote(self) -> str:
        return "040"

    def densidade_gravacao(self) -> str:
        return "01600"

    def _digito_agencia(self) -> str:
        return " "

    def dv_agencia_cobradora(self) -> str:
        return " "

    def uso_exclusivo_banco(self) -> str:
        return " " * 20

    def uso_exclusivo_empresa(self) -> str:
        return " " * 20

    def codigo_convenio(self) -> str:
        return " " * 20

    def convenio_lote(self) -> str:
        return " " * 20

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente)

    def info_conta(self) -> str:
        return (
            self._agencia5()
            + self._digito_agencia()
            + self._conta().rjust(12, "0")
            + str(self.digito_conta)
            + " "
        )

    def complemento_header(self) -> str:
        return " " * 29

    def complemento_trailer(self) -> str:
        return ("0" * 23 * 4).ljust(217)

    def monta_trailer_arquivo(self, nro_lotes: int, sequencial: int) -> str:
        return (
            self.cod_banco()
            + "99999"
            + " " * 9
            + str(nro_lotes).rjust(6, "0")
            + str(sequencial).rjust(6, "0")
            + "0" * 6
            + " " * 205
        )

    def _formata_nosso_numero(self, nosso_numero: str) -> str:
        return so_digitos(nosso_numero).ljust(20)

    def complemento_p(self, pagamento: Pagamento) -> str:
        return (
            self._conta().rjust(12, "0")
            + str(self.digito_conta)
            + " "
            + self._formata_nosso_numero(pagamento.nosso_numero)
        )

    def codigo_desconto(self, pagamento: Pagamento) -> str:
        return "1"

    def codigo_baixa(self, pagamento: Pagamento) -> str:
        return "1"

    def dias_baixa(self, pagamento: Pagamento) -> str:
        return "060"

    def data_mora(self, pagamento: Pagamento) -> str:
        if pagamento.tipo_mora not in ("1", "2"):
            return "0" * 8
        return (pagamento.data_vencimento + timedelta(days=1)).strftime("%d%m%Y")
