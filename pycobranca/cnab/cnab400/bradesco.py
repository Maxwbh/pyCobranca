"""Remessa CNAB 400 — Bradesco (237), porta fiel de ``Remessa::Cnab400::Bradesco``."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ...core.dv import modulo11_flex
from ..formatacao import format_size
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBradesco400"]


@dataclass
class RemessaBradesco400(RemessaCnab400Base):
    codigo_empresa: str = ""

    def cod_banco(self) -> str:
        return "237"

    def nome_banco(self) -> str:
        return "BRADESCO".ljust(15)

    def info_conta(self) -> str:
        return so_digitos(self.codigo_empresa).zfill(20)

    def complemento(self) -> str:
        return " " * 8 + "MX" + so_digitos(self.sequencial_remessa).zfill(7) + " " * 277

    def _identificacao_empresa(self) -> str:
        return (
            "0"
            + so_digitos(self.carteira).zfill(3)
            + so_digitos(self.agencia).zfill(5)
            + so_digitos(self.conta_corrente).zfill(7)
            + self.digito_conta
        )

    def _digito_nosso_numero(self, nosso_numero: str) -> str:
        base = f"{self.carteira}{so_digitos(nosso_numero).rjust(11, chr(48))}"
        return str(
            modulo11_flex(
                base,
                fatores=(2, 3, 4, 5, 6, 7),
                mapa={10: "P", 11: 0},
                bloco=lambda total: 11 - (total % 11),
            )
        )

    def _endereco_sacado(self, pagamento: Pagamento) -> str:
        endereco = f"{pagamento.endereco_sacado}, {pagamento.cidade_sacado}/{pagamento.uf_sacado}"
        if len(endereco) <= 40:
            return endereco.ljust(40)
        return format_size(
            f"{pagamento.endereco_sacado[:20]} {pagamento.cidade_sacado[:15]}"
            f"/{pagamento.uf_sacado}",
            40,
        )

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        cep = so_digitos(pagamento.cep_sacado).zfill(8)
        return (
            "1"
            + "0" * 5
            + "0"
            + "0" * 5
            + "0" * 7
            + "0"
            + self._identificacao_empresa()
            + str(pagamento.documento_ou_numero).ljust(25)
            + "0" * 3
            + pagamento.codigo_multa
            + pagamento.formata_percentual_multa()
            + so_digitos(pagamento.nosso_numero).rjust(11, "0")
            + self._digito_nosso_numero(pagamento.nosso_numero)
            + "0" * 10
            + "2"
            + "N"
            + " " * 10
            + " "
            + "2"
            + " " * 2
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).ljust(10)
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + "0" * 3
            + "0" * 5
            + "01"
            + "N"
            + pagamento.data_emissao.strftime("%d%m%y")
            + "0" * 2
            + "0" * 2
            + pagamento.formata_valor_mora()
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_valor_iof()
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado()
            + so_digitos(pagamento.documento_sacado).rjust(14, "0")
            + format_size(pagamento.nome_sacado, 40)
            + self._endereco_sacado(pagamento)
            + " " * 12
            + cep[:5]
            + cep[5:8]
            + " " * 60
            + str(sequencial).rjust(6, "0")
        )
