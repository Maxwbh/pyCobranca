"""Remessa CNAB 400 — Banco do Brasil (001)."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBancoBrasil400"]


@dataclass
class RemessaBancoBrasil400(RemessaCnab400Base):
    convenio: str = ""
    variacao_carteira: str = ""
    convenio_lider: str = ""

    def cod_banco(self) -> str:
        return "001"

    def nome_banco(self) -> str:
        return "BANCODOBRASIL".ljust(15)

    def _agencia(self) -> str:
        return str(self.agencia)

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente).rjust(8, "0")

    def _agencia_dv(self) -> str:
        return str(modulo11_flex(self._agencia(), mapa={10: "X"}))

    def _conta_dv(self) -> str:
        return str(modulo11_flex(self._conta(), mapa={10: "X"}))

    def _tipo_empresa(self) -> str:
        return "01" if len(so_alfanumerico(self.documento_cedente)) <= 11 else "02"

    def info_conta(self) -> str:
        return f"{self._agencia()}{self._agencia_dv()}{self._conta()}{self._conta_dv()}" + "0" * 6

    def complemento(self) -> str:
        return (
            so_digitos(self.sequencial_remessa).rjust(7, "0")
            + " " * 22
            + so_digitos(self.convenio_lider or "0").rjust(7, "0")
            + " " * 258
        )

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        convenio = so_digitos(self.convenio).rjust(7, "0")
        return (
            "7"
            + self._tipo_empresa()
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
            + self._agencia()
            + self._agencia_dv()
            + self._conta()
            + self._conta_dv()
            + convenio
            + " " * 25
            + convenio
            + so_digitos(pagamento.nosso_numero).rjust(10, "0")
            + "00"
            + "00"
            + " " * 3
            + " "
            + " " * 3
            + so_digitos(self.variacao_carteira).rjust(3, "0")
            + "0"
            + "000000"
            + " " * 5
            + so_digitos(self.carteira).rjust(2, "0")
            + pagamento.identificacao_ocorrencia
            + str(pagamento.documento_ou_numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + "0000"
            + " "
            + pagamento.especie_titulo
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%y")
            + str(pagamento.cod_primeira_instrucao).rjust(2, "0")
            + str(pagamento.cod_segunda_instrucao).rjust(2, "0")
            + pagamento.formata_valor_mora()
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_valor_iof()
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado()
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 37)
            + " " * 3
            + self._format_size(pagamento.endereco_sacado, 40)
            + self._format_size(pagamento.bairro_sacado, 12)
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + " " * 40
            + str(pagamento.dias_protesto).ljust(2)
            + " "
            + str(sequencial).rjust(6, "0")
        )
