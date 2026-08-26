"""Remessa CNAB 400 — Banco do Nordeste (004).

O detalhe já saiu com 401 posições, e o módulo atribuía isso ao layout do banco
— não era: era o nosso número de 8 dígitos num campo de 7, com ``rjust``, que
preenche mas não corta. Corrigido o campo, o registro tem as 400 posições da
FEBRABAN e ``tamanho_registro`` volta a valer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo11_flex
from ...exceptions import BoletoInvalido
from ..formatacao import campo_numerico
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBancoNordeste400"]


@dataclass
class RemessaBancoNordeste400(RemessaCnab400Base):
    emissao_boleto: str = "2"

    def cod_banco(self) -> str:
        return "004"

    def nome_banco(self) -> str:
        return "B.DO NORDESTE".ljust(15)

    def _agencia(self) -> str:
        return campo_numerico(self.agencia, 4, "agencia")

    def _conta(self) -> str:
        return campo_numerico(self.conta_corrente, 7, "conta_corrente")

    def info_conta(self) -> str:
        return f"{self._agencia()}00{self._conta()}{self.digito_conta}" + " " * 6

    def complemento(self) -> str:
        return " " * 294

    def _codigo_carteira(self) -> str:
        carteira = so_digitos(self.carteira).rjust(2, "0")
        if carteira == "51":
            return "I"
        carteiras = {
            "1": {"21": "1", "41": "2"},
            "2": {"21": "4", "41": "5"},
        }
        por_emissao = carteiras.get(str(self.emissao_boleto))
        if por_emissao is None or carteira not in por_emissao:
            # Era ``KeyError``: escapava da hierarquia de erros do pacote, então
            # quem chamasse com ``except PyCobrancaError`` via o processo morrer.
            raise BoletoInvalido(
                f"combinação inválida no Banco do Nordeste: carteira {carteira!r} "
                f"com emissao_boleto {self.emissao_boleto!r} "
                "(aceitas: 21 e 41, emissão 1 ou 2; 51 é a carteira I)"
            )
        return por_emissao[carteira]

    def _digito_nosso_numero(self, nosso_numero: str) -> str:
        return str(
            modulo11_flex(
                so_digitos(nosso_numero).rjust(7, "0"),
                fatores=(2, 3, 4, 5, 6, 7, 8),
                mapa={1: 0, 10: 0, 11: 0},
                bloco=lambda total: 11 - (total % 11),
            )
        )

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "1"
            + " " * 16
            + self._agencia()
            + "0" * 2
            + self._conta()
            + self.digito_conta
            + pagamento.formata_percentual_multa()[0:2]
            + " " * 4
            + str(pagamento.documento_ou_numero).ljust(25)
            + campo_numerico(pagamento.nosso_numero, 7, "nosso_numero")
            + self._digito_nosso_numero(pagamento.nosso_numero)
            + "0" * 10
            + "0" * 6
            + "0" * 13
            + " " * 8
            + self._codigo_carteira()
            + pagamento.identificacao_ocorrencia
            + str(pagamento.numero).rjust(10, "0")
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + "0" * 4
            + " "
            + "01"
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%y")
            + "0" * 4
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
            + self._format_size(pagamento.nome_avalista, 40)
            + "99"
            + "0"
            + str(sequencial).rjust(6, "0")
        )
