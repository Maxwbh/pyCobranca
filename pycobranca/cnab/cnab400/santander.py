"""Remessa CNAB 400 — Santander (033)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...core.documentos import so_alfanumerico, so_digitos
from ..formatacao import format_valor
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaSantander400"]


@dataclass
class RemessaSantander400(RemessaCnab400Base):
    campo_de_carteira: ClassVar[str | None] = "codigo_carteira"

    codigo_transmissao: str = ""
    codigo_carteira: str = "1"

    def cod_banco(self) -> str:
        return "033"

    def nome_banco(self) -> str:
        return self._format_size("SANTANDER", 15)

    def _codigo_transmissao(self) -> str:
        return str(self.codigo_transmissao).strip().rjust(20, "0")

    def _tipo_empresa(self) -> str:
        return "01" if len(so_alfanumerico(self.documento_cedente)) <= 11 else "02"

    def info_conta(self) -> str:
        return self._codigo_transmissao()

    def complemento(self) -> str:
        return " " * 275

    def _conta_padrao_novo(self) -> bool:
        return bool(self.conta_corrente) and len(str(self.conta_corrente)) > 8

    def monta_header(self) -> str:
        empresa = str(self.empresa_mae)[:30].ljust(30)
        return (
            "01REMESSA01COBRANCA       "
            + self.info_conta()
            + empresa
            + self.cod_banco()
            + self.nome_banco()
            + self._data_geracao()
            + "0" * 16
            + self.complemento()
            + "058"
            + "000001"
        )

    def _ident_movimento_complemento(self) -> str:
        return "I" if self._conta_padrao_novo() else " "

    def _movimento_complemento(self) -> str:
        if self._conta_padrao_novo():
            return f"{str(self.conta_corrente)[8]}{self.digito_conta}"
        return "  "

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + self._tipo_empresa()
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
            + self._codigo_transmissao()
            + str(pagamento.documento_ou_numero).ljust(25)
            + so_digitos(pagamento.nosso_numero).rjust(8, "0")
            + pagamento.formata_data_segundo_desconto()
            + " "
            + pagamento.codigo_multa
            + pagamento.formata_percentual_multa()
            + "00"
            + "0" * 13
            + " " * 4
            + pagamento.formata_data_multa()
            + self.codigo_carteira
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + "0" * 5
            + pagamento.especie_titulo
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%y")
            + str(pagamento.cod_primeira_instrucao)
            + str(pagamento.cod_segunda_instrucao)
            + pagamento.formata_valor_mora()
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_valor_iof()
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado()
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 40)
            + self._format_size(pagamento.endereco_sacado, 40)
            + self._format_size(pagamento.bairro_sacado, 12)
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + self._format_size(pagamento.nome_avalista, 30)
            + " "
            + self._ident_movimento_complemento()
            + self._movimento_complemento()
            + " " * 6
            + str(pagamento.dias_protesto).rjust(2, "0")
            + " "
            + str(sequencial).rjust(6, "0")
        )

    def _total_titulos(self) -> str:
        total = sum(float(p.valor) for p in self.pagamentos)
        return format_valor(total, 13)

    def monta_trailer(self, sequencial: int) -> str:
        seq = str(sequencial).rjust(6, "0")
        return "9" + seq + self._total_titulos() + "0" * 374 + seq
