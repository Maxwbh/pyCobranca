"""Remessa CNAB 400 — CrediSIS (097).

O registro detalhe é emitido com **402 posições** (conforme o layout do
banco); ``tamanho_registro`` fica
``None`` e a garantia é a comparação byte a byte com a fixture.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaCredisis400"]


@dataclass
class RemessaCredisis400(RemessaCnab400Base):
    codigo_cedente: str = ""
    convenio: str = ""
    tamanho_registro: int | None = None

    def cod_banco(self) -> str:
        return "097"

    def nome_banco(self) -> str:
        return "CENTRALCRED".ljust(15)

    def _agencia(self) -> str:
        return so_digitos(self.agencia).rjust(4, "0")

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente).rjust(8, "0")

    def _codigo_cedente(self) -> str:
        return so_digitos(self.codigo_cedente).rjust(4, "0")

    def _tipo_empresa(self) -> str:
        return "01" if len(so_digitos(self.documento_cedente)) <= 11 else "02"

    def info_conta(self) -> str:
        return f"{self._agencia()} {self._conta()}{self.digito_conta}" + " " * 6

    def complemento(self) -> str:
        return so_digitos(self.sequencial_remessa).rjust(7, "0").ljust(294)

    def _formata_nosso_numero(self, nosso_numero: str) -> str:
        return "0" + self._codigo_cedente() + so_digitos(nosso_numero).rjust(6, "0")

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + self._tipo_empresa()
            + so_digitos(self.documento_cedente).rjust(14, "0")
            + self._agencia()
            + " " * 1
            + self._conta()
            + self.digito_conta
            + " " * 6
            + str(pagamento.documento_ou_numero).ljust(25)
            + self._formata_nosso_numero(pagamento.nosso_numero)
            + " " * 37
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + " " * 11
            + pagamento.data_emissao.strftime("%d%m%y")
            + " " * 4
            + pagamento.formata_valor_mora(4).ljust(6, "0")
            + pagamento.formata_percentual_multa().ljust(6, "0")
            + " " * 33
            + pagamento.formata_valor_desconto()
            + pagamento.identificacao_sacado()
            + so_digitos(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 40)
            + self._format_size(pagamento.endereco_sacado, 37)
            + self._format_size(pagamento.bairro_sacado, 15)
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + self._format_size(pagamento.nome_avalista, 25)
            + " " * 1
            + " " * 14
            + str(pagamento.dias_protesto).rjust(2, "0")
            + " " * 1
            + str(sequencial).rjust(6, "0")
        )
