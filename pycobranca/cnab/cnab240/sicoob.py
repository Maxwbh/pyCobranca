"""Remessa CNAB 240 — Sicoob (756)."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab240Base

__all__ = ["RemessaSicoob240"]


@dataclass
class RemessaSicoob240(RemessaCnab240Base):
    modalidade_carteira: str = "01"
    tipo_formulario: str = "4"
    parcela: str = "01"

    def __post_init__(self) -> None:
        self.forma_cadastramento = "0"

    def cod_banco(self) -> str:
        return "756"

    def nome_banco(self) -> str:
        return "SICOOB".ljust(30)

    def versao_layout_arquivo(self) -> str:
        return "081"

    def versao_layout_lote(self) -> str:
        return "040"

    def _agencia4(self) -> str:
        return so_digitos(self.agencia).rjust(4, "0")

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente)

    def _digito_agencia(self) -> str:
        return str(modulo11_flex(self._agencia4(), mapa={10: "0"}))

    def _digito_conta(self) -> str:
        return str(modulo11_flex(self._conta(), mapa={10: "0"}))

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

    def info_conta(self) -> str:
        return (
            self._agencia5()
            + self._digito_agencia()
            + self._conta().rjust(12, "0")
            + self._digito_conta()
            + " "
        )

    def complemento_header(self) -> str:
        return " " * 29

    def complemento_trailer(self) -> str:
        total_simples = self._quantidade_titulos_cobranca() + self._valor_titulos_carteira()
        return (total_simples + "0" * 23 + "0" * 23 + "0" * 23).ljust(217)

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
        return (
            so_digitos(nosso_numero).rjust(10, "0")
            + self.parcela
            + self.modalidade_carteira
            + self.tipo_formulario
            + " " * 5
        )

    def complemento_p(self, pagamento: Pagamento) -> str:
        return (
            self._conta().rjust(12, "0")
            + self._digito_conta()
            + " "
            + self._formata_nosso_numero(pagamento.nosso_numero)
        )

    def data_multa(self, pagamento: Pagamento) -> str:
        if pagamento.codigo_multa == "0":
            return "0" * 8
        return pagamento.data_vencimento.strftime("%d%m%Y")

    def dias_baixa(self, pagamento: Pagamento) -> str:
        return " " * 3

    def monta_segmento_r(self, pagamento: Pagamento, nro_lote: int, sequencial: int) -> str:
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "3"
            + str(sequencial).rjust(5, "0")
            + "R"
            + " "
            + "01"
            + self.descontos_adicionais(pagamento)
            + pagamento.codigo_multa
            + self.data_multa(pagamento)
            + pagamento.formata_percentual_multa(15)
            + " " * 10
            + " " * 40
            + " " * 40
            + " " * 20
            + "0" * 8
            + "0" * 3
            + "0" * 5
            + " "
            + "0" * 12
            + " "
            + " "
            + "0"
            + " " * 9
        )
