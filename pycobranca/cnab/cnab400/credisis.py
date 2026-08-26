"""Remessa CNAB 400 — CrediSIS (097).

O detalhe já saiu com 402 posições, e o módulo atribuía isso ao layout do banco
— não era: era o nosso número de 8 dígitos num campo de 6, com ``rjust``, que
preenche mas não corta. Corrigido o campo, o registro tem as 400 posições da
FEBRABAN e ``tamanho_registro`` volta a valer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ..formatacao import campo_numerico
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaCredisis400"]


@dataclass
class RemessaCredisis400(RemessaCnab400Base):
    codigo_cedente: str = ""
    convenio: str = ""

    def cod_banco(self) -> str:
        return "097"

    def nome_banco(self) -> str:
        return "CENTRALCRED".ljust(15)

    def _agencia(self) -> str:
        return campo_numerico(self.agencia, 4, "agencia")

    def _conta(self) -> str:
        return campo_numerico(self.conta_corrente, 8, "conta_corrente")

    def _codigo_cedente(self) -> str:
        return so_digitos(self.codigo_cedente).rjust(4, "0")

    def _tipo_empresa(self) -> str:
        return "01" if len(so_alfanumerico(self.documento_cedente)) <= 11 else "02"

    def info_conta(self) -> str:
        return f"{self._agencia()} {self._conta()}{self.digito_conta}" + " " * 6

    def complemento(self) -> str:
        return so_digitos(self.sequencial_remessa).rjust(7, "0").ljust(294)

    def _formata_nosso_numero(self, nosso_numero: str) -> str:
        return "0" + self._codigo_cedente() + campo_numerico(nosso_numero, 6, "nosso_numero")

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + self._tipo_empresa()
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
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
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
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
