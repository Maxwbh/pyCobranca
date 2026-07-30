"""Remessa CNAB 400 — Banrisul (041)."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import duplo_digito
from ..formatacao import format_valor
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBanrisul400"]


@dataclass
class RemessaBanrisul400(RemessaCnab400Base):
    convenio: str = ""

    def cod_banco(self) -> str:
        return "041"

    def nome_banco(self) -> str:
        return "BANRISUL".ljust(15)

    def _codigo_cedente(self) -> str:
        return so_digitos(self.convenio).rjust(13, "0")

    def info_conta(self) -> str:
        return self._codigo_cedente().ljust(20)

    def complemento(self) -> str:
        return " " * 294

    def monta_header(self) -> str:
        return (
            "01REMESSA"
            + " " * 17
            + self.info_conta()
            + self._format_size(self.empresa_mae, 30)
            + self.cod_banco()
            + self.nome_banco()
            + self._data_geracao()
            + self.complemento()
            + "000001"
        )

    def _codigo_primeira_instrucao(self, pagamento: Pagamento) -> str:
        if float(pagamento.percentual_multa) > 0.0:
            return "18"
        return str(pagamento.cod_primeira_instrucao)

    def _tipo_mora(self, pagamento: Pagamento) -> str:
        return " " if pagamento.tipo_mora == "3" else pagamento.tipo_mora

    def _formata_valor_mora(self, pagamento: Pagamento, tamanho: int) -> str:
        if pagamento.tipo_mora == "3":
            return " " * tamanho
        return pagamento.formata_valor_mora(tamanho)

    def _formata_percentual_multa(self, pagamento: Pagamento) -> str:
        return f"{float(pagamento.percentual_multa):.1f}".replace(".", "").rjust(3, "0")

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        doc = str(pagamento.documento_ou_numero)
        return (
            "1"
            + " " * 16
            + self._codigo_cedente().rjust(13)
            + " " * 7
            + doc.ljust(25)
            + so_digitos(pagamento.nosso_numero).rjust(8, "0")
            + duplo_digito(pagamento.nosso_numero)
            + " " * 32
            + " " * 3
            + so_digitos(self.carteira)
            + pagamento.identificacao_ocorrencia
            + doc.ljust(10)
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + " " * 5
            + "08"
            + "N"
            + pagamento.data_emissao.strftime("%d%m%y")
            + self._codigo_primeira_instrucao(pagamento)
            + str(pagamento.cod_segunda_instrucao)
            + self._tipo_mora(pagamento)
            + self._formata_valor_mora(pagamento, 12)
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_valor_iof()
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado()
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 35)
            + " " * 5
            + self._format_size(pagamento.endereco_sacado, 40)
            + " " * 7
            + self._formata_percentual_multa(pagamento)
            + "00"
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + "0000"
            + " "
            + "0" * 13
            + str(pagamento.dias_protesto).rjust(2, "0")
            + " " * 23
            + str(sequencial).rjust(6, "0")
        )

    def _valor_titulos(self) -> str:
        total = sum(float(p.valor) for p in self.pagamentos)
        return format_valor(total, 13)

    def monta_trailer(self, sequencial: int) -> str:
        return "9" + " " * 26 + self._valor_titulos() + " " * 354 + str(sequencial).rjust(6, "0")
