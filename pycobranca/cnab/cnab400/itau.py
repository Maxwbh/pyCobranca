"""Remessa CNAB 400 — Itaú (341), porta fiel de ``Remessa::Cnab400::Itau``."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ..formatacao import format_size
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaItau400"]


@dataclass
class RemessaItau400(RemessaCnab400Base):
    def cod_banco(self) -> str:
        return "341"

    def nome_banco(self) -> str:
        return "BANCO ITAU SA".ljust(15)

    def info_conta(self) -> str:
        agencia = so_digitos(self.agencia).zfill(4)
        conta = so_digitos(self.conta_corrente).zfill(5)
        return f"{agencia}00{conta}{self.digito_conta}" + " " * 8

    def complemento(self) -> str:
        return " " * 294

    def _codigo_carteira(self) -> str:
        carteira = so_digitos(self.carteira).zfill(3)
        return {"150": "U", "191": "1", "147": "E"}.get(carteira, "I")

    def _tipo_empresa(self) -> str:
        return "01" if len(so_alfanumerico(self.documento_cedente)) <= 11 else "02"

    def _prazo_instrucao(self, pagamento: Pagamento) -> str:
        if pagamento.cod_primeira_instrucao not in ("09", "34", "35"):
            return "03"
        return str(pagamento.dias_protesto).rjust(2, "0")

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        agencia = so_digitos(self.agencia).zfill(4)
        conta = so_digitos(self.conta_corrente).zfill(5)
        carteira = so_digitos(self.carteira).zfill(3)
        return (
            "1"
            + self._tipo_empresa()
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
            + agencia
            + "00"
            + conta
            + self.digito_conta
            + " " * 4
            + "0" * 4
            + str(pagamento.documento_ou_numero).ljust(25)
            + so_digitos(pagamento.nosso_numero).rjust(8, "0")
            + "0" * 13
            + carteira
            + " " * 21
            + self._codigo_carteira()
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + "0" * 5
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
            + format_size(pagamento.nome_sacado, 30)
            + " " * 10
            + format_size(pagamento.endereco_sacado, 40)
            + format_size(pagamento.bairro_sacado, 12)
            + so_digitos(pagamento.cep_sacado).zfill(8)
            + format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado.ljust(2)
            + format_size(pagamento.nome_avalista, 30)
            + " " * 4
            + "0" * 6
            + self._prazo_instrucao(pagamento)
            + " "
            + str(sequencial).rjust(6, "0")
        )
