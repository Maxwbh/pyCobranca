"""Remessa CNAB 400 — Unicred (136)."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaUnicred400"]


@dataclass
class RemessaUnicred400(RemessaCnab400Base):
    codigo_beneficiario: str = ""

    def cod_banco(self) -> str:
        return "136"

    def nome_banco(self) -> str:
        return "UNICRED".ljust(15)

    def _agencia(self) -> str:
        return so_digitos(self.agencia).rjust(4, "0")

    def _conta5(self) -> str:
        return so_digitos(self.conta_corrente).rjust(5, "0")

    def _digito_agencia(self) -> str:
        return str(modulo11_flex(self._agencia(), mapa={10: "X"}))

    def _digito_conta(self) -> str:
        return str(modulo11_flex(self._conta5(), mapa={10: "0"}))

    def info_conta(self) -> str:
        return so_digitos(self.codigo_beneficiario).rjust(20, "0")

    def complemento(self) -> str:
        return "codigo_beneficiario".rjust(277)

    def _formata_nosso_numero(self, nosso_numero: str) -> str:
        nn = so_digitos(nosso_numero).rjust(10, "0")
        dv = modulo11_flex(nn, mapa={10: 0, 11: 0})
        return f"{nn}{dv}"

    def monta_header(self) -> str:
        return (
            "01REMESSA01COBRANCA       "
            + self.info_conta()
            + self._format_size(self.empresa_mae, 30)
            + self.cod_banco()
            + self.nome_banco()
            + self._data_geracao()
            + " " * 7
            + "000"
            + so_digitos(self.sequencial_remessa).rjust(7, "0")
            + self.complemento()
            + "000001"
        )

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + self._agencia().rjust(5, "0")
            + self._digito_agencia()
            + self._conta5().rjust(12, "0")
            + self._digito_conta()
            + "0"
            + so_digitos(self.carteira).rjust(3, "0")
            + "0" * 13
            + " " * 25
            + self.cod_banco()
            + "00"
            + " " * 25
            + "0"
            + pagamento.codigo_multa
            + pagamento.formata_percentual_multa(10)
            + pagamento.tipo_mora
            + "N"
            + " " * 2
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + "0" * 10
            + pagamento.cod_desconto
            + pagamento.data_emissao.strftime("%d%m%y")
            + "0"
            + pagamento.codigo_protesto
            + str(pagamento.dias_protesto).rjust(2, "0")
            + pagamento.formata_valor_mora(13)
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + self._formata_nosso_numero(pagamento.nosso_numero)
            + "00"
            + pagamento.formata_valor_abatimento(13)
            + pagamento.identificacao_sacado()
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 40)
            + self._format_size(pagamento.endereco_sacado, 40)
            + self._format_size(pagamento.bairro_sacado, 12)
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 20)
            + pagamento.uf_sacado
            + self._format_size(pagamento.nome_avalista, 38)
            + str(sequencial).rjust(6, "0")
        )
