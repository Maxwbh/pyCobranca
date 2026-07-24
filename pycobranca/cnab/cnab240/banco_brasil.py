"""Remessa CNAB 240 — Banco do Brasil (001)."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ...core.dv import modulo11_flex
from ...exceptions import BoletoInvalido
from ..pagamento import Pagamento
from .base import RemessaCnab240Base

__all__ = ["RemessaBancoBrasil240"]


@dataclass
class RemessaBancoBrasil240(RemessaCnab240Base):
    variacao: str = ""

    def __post_init__(self) -> None:
        self.emissao_boleto = "0"
        self.distribuicao_boleto = "0"
        self.especie_titulo = "02"
        self.codigo_carteira = "7"

    def cod_banco(self) -> str:
        return "001"

    def nome_banco(self) -> str:
        return "BANCO DO BRASIL S.A.".ljust(30)

    def versao_layout_arquivo(self) -> str:
        return "083"

    def versao_layout_lote(self) -> str:
        return "042"

    def _agencia(self) -> str:
        return so_digitos(self.agencia)

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente)

    def _carteira(self) -> str:
        return so_digitos(self.carteira).rjust(2, "0")

    def _variacao(self) -> str:
        return so_digitos(self.variacao).rjust(3, "0")

    def _digito_agencia(self) -> str:
        return str(modulo11_flex(self._agencia(), mapa={10: "X"}))

    def _digito_conta(self) -> str:
        return str(modulo11_flex(self._conta(), mapa={10: "X"}))

    def codigo_convenio(self) -> str:
        return (
            f"{so_digitos(self.convenio).rjust(9, '0')}0014{self._carteira()}{self._variacao()}  "
        )

    def convenio_lote(self) -> str:
        return self.codigo_convenio()

    def info_conta(self) -> str:
        return (
            self._agencia().rjust(5, "0")
            + self._digito_agencia()
            + self._conta().rjust(12, "0")
            + self._digito_conta()
            + " "
        )

    def complemento_header(self) -> str:
        return " " * 29

    def complemento_trailer(self) -> str:
        return "0" * 217

    def _formata_nosso_numero(self, nosso_numero: str) -> str:
        convenio = so_digitos(self.convenio)
        quantidade = {4: 7, 6: 5, 7: 10}.get(len(convenio))
        if quantidade is None:
            raise BoletoInvalido("Tipo de convênio não implementado.")
        nn = so_digitos(nosso_numero).rjust(quantidade, "0")
        if quantidade == 10:
            return nn
        digito = modulo11_flex(f"{convenio}{nn}", mapa={10: "X"})
        return f"{nn}{digito}"

    def _identificador_titulo(self, nosso_numero: str) -> str:
        return f"{so_digitos(self.convenio)}{self._formata_nosso_numero(nosso_numero)}".ljust(20)

    def complemento_p(self, pagamento: Pagamento) -> str:
        return (
            self._conta().rjust(12, "0")
            + self._digito_conta()
            + " "
            + self._identificador_titulo(pagamento.nosso_numero)
        )

    def monta_segmento_p(self, pagamento: Pagamento, nro_lote: int, sequencial: int) -> str:
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "3"
            + str(sequencial).rjust(5, "0")
            + "P"
            + " "
            + pagamento.identificacao_ocorrencia
            + self._agencia().rjust(5, "0")
            + self._digito_agencia()
            + self.complemento_p(pagamento)
            + self.codigo_carteira
            + self.forma_cadastramento
            + self.tipo_documento
            + self.emissao_boleto
            + self.distribuicao_boleto
            + self.numero(pagamento)
            + pagamento.data_vencimento.strftime("%d%m%Y")
            + pagamento.formata_valor(15)
            + "0" * 5
            + " "
            + self.especie_titulo
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%Y")
            + pagamento.tipo_mora
            + self.data_mora(pagamento)
            + pagamento.formata_valor_mora(15)
            + pagamento.cod_desconto
            + pagamento.formata_data_desconto("%d%m%Y")
            + pagamento.formata_valor_desconto(15)
            + pagamento.formata_valor_iof(15)
            + pagamento.formata_valor_abatimento(15)
            + self.identificacao_titulo_empresa(pagamento)
            + pagamento.codigo_protesto
            + str(pagamento.dias_protesto).rjust(2, "0")
            + "0"
            + "000"
            + "09"
            + "0" * 10
            + " "
        )
