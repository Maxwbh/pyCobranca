"""Remessa CNAB 240 — Caixa Econômica Federal (104), layout SIGCB."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ...core.documentos import so_digitos
from ..pagamento import Pagamento
from .base import RemessaCnab240Base

__all__ = ["RemessaCaixa240"]


@dataclass
class RemessaCaixa240(RemessaCnab240Base):
    versao_aplicativo: str = ""
    modalidade_carteira: str = "14"

    def __post_init__(self) -> None:
        self.emissao_boleto = "2"
        self.distribuicao_boleto = "0"
        self.especie_titulo = "99"
        self.tipo_documento = "2"

    def cod_banco(self) -> str:
        return "104"

    def nome_banco(self) -> str:
        return "CAIXA ECONOMICA FEDERAL".ljust(30)

    def versao_layout_arquivo(self) -> str:
        return "050"

    def versao_layout_lote(self) -> str:
        return "030"

    def _convenio(self) -> str:
        return so_digitos(self.convenio).rjust(6, "0")

    def codigo_convenio(self) -> str:
        return "0" * 20

    def uso_exclusivo_banco(self) -> str:
        return " " * 20

    def uso_exclusivo_empresa(self) -> str:
        return "REMESSA-PRODUCAO".ljust(20)

    def convenio_lote(self) -> str:
        return self._convenio() + "0" * 14

    def info_conta(self) -> str:
        return self._agencia5() + str(self.digito_agencia) + self._convenio() + "0" * 7 + "0"

    def complemento_header(self) -> str:
        versao = so_digitos(self.versao_aplicativo).rjust(4, "0")
        return versao.rjust(4) + " " * 25

    def exclusivo_servico(self) -> str:
        return "00"

    def complemento_trailer(self) -> str:
        return "0" * 69 + " " * 148

    def complemento_p(self, pagamento: Pagamento) -> str:
        return (
            self._convenio()
            + "0" * 11
            + self.modalidade_carteira
            + so_digitos(pagamento.nosso_numero).rjust(15, "0")
        )

    def complemento_r(self) -> str:
        return " " * 50 + " " * 11

    def numero(self, pagamento: Pagamento) -> str:
        return pagamento.formata_documento_ou_numero(11, "0") + " " * 4

    def identificacao_titulo_empresa(self, pagamento: Pagamento) -> str:
        return pagamento.formata_documento_ou_numero(11, "0") + " " * 14

    def data_multa(self, pagamento: Pagamento) -> str:
        if pagamento.codigo_multa == "0":
            return "0" * 8
        return (pagamento.data_vencimento + timedelta(days=1)).strftime("%d%m%Y")

    def codigo_baixa(self, pagamento: Pagamento) -> str:
        return "1" if str(pagamento.codigo_protesto) == "3" else "2"

    def dias_baixa(self, pagamento: Pagamento) -> str:
        return "120" if str(pagamento.codigo_protesto) == "3" else "000"

    def data_mora(self, pagamento: Pagamento) -> str:
        if pagamento.tipo_mora not in ("1", "2"):
            return "0" * 8
        return (pagamento.data_vencimento + timedelta(days=1)).strftime("%d%m%Y")
