"""Remessa CNAB 400 — Banco de Brasília / BRB (070), formato DCB.

Porta fiel de ``Remessa::Cnab400::BancoBrasilia``. Este layout **não** é o CNAB
400 FEBRABAN: o header tem 39 posições ("DCB...") e os demais registros 400 — daí
``tamanho_registro = (39, 400)``. O detalhe já saiu com 402, e o módulo atribuía
isso ao layout do banco; era o nosso número num campo menor, com ``rjust``, que
preenche mas não corta. O header inclui a data/hora de formação
(``AAAAMMDDHHMMSS``); para gerar arquivos determinísticos informe
``data_formacao``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo10, modulo11_flex
from ..formatacao import campo_numerico
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaBancoBrasilia400"]


@dataclass
class RemessaBancoBrasilia400(RemessaCnab400Base):
    #: ``AAAAMMDDHHMMSS`` — quando vazio, usa o horário atual (não determinístico).
    data_formacao: str = ""
    #: Header DCB de 39 posições, restante em 400.
    tamanho_registro: int | tuple[int, ...] | None = (39, 400)

    def cod_banco(self) -> str:
        return "070"

    def nome_banco(self) -> str:
        return ""

    def _agencia(self) -> str:
        # O header DCB reserva 3 posições e o detalhe 4 (com zero à esquerda):
        # o limite que vale é o menor dos dois, senão o header desloca.
        return campo_numerico(self.agencia, 3, "agencia")

    def _conta(self) -> str:
        return campo_numerico(self.conta_corrente, 7, "conta_corrente")

    def _carteira(self) -> str:
        return so_digitos(self.carteira).rjust(1, "0")

    def info_conta(self) -> str:
        return f"{self._agencia()}{self._conta()}"

    def _data_formacao(self) -> str:
        return self.data_formacao or datetime.now().strftime("%Y%m%d%H%M%S")

    def _quantidade_registros(self) -> str:
        return str(len(self.pagamentos) + 1).rjust(6, "0")

    def monta_header(self) -> str:
        return f"DCB001075{self.info_conta()}{self._data_formacao()}{self._quantidade_registros()}"

    def _monta_nosso_numero(self, pagamento: Pagamento) -> str:
        if self._carteira() == "3":
            return campo_numerico(pagamento.nosso_numero, 12, "nosso_numero")
        nn = campo_numerico(pagamento.nosso_numero, 6, "nosso_numero")
        base = f"{self._carteira()}{nn}{self.cod_banco()}"
        base += str(modulo10(base))
        base += str(
            modulo11_flex(
                base,
                fatores=(2, 3, 4, 5, 6, 7),
                mapa={10: 0, 11: 0},
                bloco=lambda total: 11 - (total % 11),
            )
        )
        return base

    @staticmethod
    def _codigo_tipo_juros(pagamento: Pagamento) -> str:
        return "50" if float(pagamento.valor_mora) > 0.0 else "00"

    @staticmethod
    def _codigo_tipo_desconto(pagamento: Pagamento) -> str:
        return "52" if float(pagamento.valor_desconto) > 0.0 else "00"

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        return (
            "01"
            + self._agencia()
            + self._conta()
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 35)
            + self._format_size(pagamento.endereco_sacado, 35)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + so_digitos(pagamento.cep_sacado)
            + pagamento.identificacao_sacado(False)
            + str(pagamento.documento_ou_numero).rjust(13, "0")
            + self._carteira()
            + pagamento.data_emissao.strftime("%d%m%Y")
            + "21"
            + "0"
            + "0"
            + "02"
            + self.cod_banco()
            + self._agencia().rjust(4, "0")
            + " " * 30
            + pagamento.data_vencimento.strftime("%d%m%Y")
            + pagamento.formata_valor(14)
            + self._monta_nosso_numero(pagamento)
            + self._codigo_tipo_juros(pagamento)
            + pagamento.formata_valor_mora(14)
            + pagamento.formata_valor_abatimento(14)
            + self._codigo_tipo_desconto(pagamento)
            + pagamento.formata_data_desconto("%d%m%Y")
            + pagamento.formata_valor_desconto(14)
            + "00"
            + "00"
            + "00"
            + "00"
            + "00000"
            + self._format_size(self.empresa_mae, 40)
            + " " * 40
            + " " * 32
        )
