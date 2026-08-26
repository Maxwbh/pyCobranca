"""Remessa CNAB 240 — Santander (033).

Header de arquivo e segmentos P/Q são customizados. O segmento P já saiu com
241 posições, e o módulo atribuía isso ao layout do banco — não era: era o
``dias_baixa`` de 3 dígitos num campo de 2, com ``rjust``, que preenche mas não
corta. Corrigido o campo, o registro tem as 240 posições da FEBRABAN e
``tamanho_registro`` volta a valer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo11_flex
from ..formatacao import campo_numerico
from ..pagamento import Pagamento
from .base import RemessaCnab240Base

__all__ = ["RemessaSantander240"]


@dataclass
class RemessaSantander240(RemessaCnab240Base):
    campo_de_carteira: ClassVar[str | None] = "codigo_carteira"

    codigo_transmissao: str = ""

    def __post_init__(self) -> None:
        self.emissao_boleto = " "
        self.distribuicao_boleto = " "
        self.especie_titulo = "02"
        self.tipo_documento = "2"

    def cod_banco(self) -> str:
        return "033"

    def nome_banco(self) -> str:
        return "BANCO SANTANDER".ljust(30)

    def versao_layout_arquivo(self) -> str:
        return "040"

    def versao_layout_lote(self) -> str:
        return "030"

    def _codigo_transmissao(self) -> str:
        return str(self.codigo_transmissao).strip().rjust(15, "0")

    def _agencia4(self) -> str:
        return campo_numerico(self.agencia, 4, "agencia")

    def _conta(self) -> str:
        return campo_numerico(self.conta_corrente, 9, "conta_corrente")

    def _digito_agencia(self) -> str:
        return str(modulo11_flex(self._agencia4(), mapa={10: "X", 11: "X"}))

    def dv_agencia_cobradora(self) -> str:
        return " "

    def densidade_gravacao(self) -> str:
        return " " * 5

    def hora_geracao(self) -> str:
        return " " * 6

    def uso_exclusivo_banco(self) -> str:
        return " " * 20

    def uso_exclusivo_empresa(self) -> str:
        return " " * 20

    def info_conta(self) -> str:
        return ""

    def codigo_convenio(self) -> str:
        return self._codigo_transmissao() + " " * 25

    def convenio_lote(self) -> str:
        return " " * 20 + self._codigo_transmissao() + " " * 5

    def complemento_header(self) -> str:
        return " " * 29

    def complemento_trailer(self) -> str:
        return " " * 217

    def complemento_r(self) -> str:
        return " " * 61

    def dias_baixa(self, pagamento: Pagamento) -> str:
        # O campo tem 2 posições (precedido do "0" literal no segmento P, fecha
        # as 3 da FEBRABAN). O padrão de ``dias_baixa`` é "000", com três — e
        # ``rjust`` não cortava, estourando o registro para 241 posições.
        return campo_numerico(pagamento.dias_baixa, 2, "dias_baixa")

    def _identificador_titulo(self, nosso_numero: str) -> str:
        dv = modulo11_flex(
            so_digitos(nosso_numero),
            fatores=(2, 3, 4, 5, 6, 7, 8, 9),
            mapa={10: 0, 11: 0},
            bloco=lambda total: 11 - (total % 11),
        )
        return f"{so_digitos(nosso_numero)}{dv}".rjust(13, "0")

    def complemento_p(self, pagamento: Pagamento) -> str:
        conta = self._conta()
        dc = str(self.digito_conta)
        return conta + dc + conta + dc + "  " + self._identificador_titulo(pagamento.nosso_numero)

    def _doc_ou_numero(self, pagamento: Pagamento, tamanho: int = 25) -> str:
        import re

        doc = re.sub(r"[^0-9A-Za-z ]", "", str(pagamento.documento_ou_numero))
        return doc.ljust(tamanho)[:tamanho]

    def monta_header_arquivo(self) -> str:
        return (
            self.cod_banco()
            + "0000"
            + "0"
            + " " * 8
            + self._tipo_empresa(self.documento_cedente)
            + so_alfanumerico(self.documento_cedente).rjust(15, "0")
            + self.codigo_convenio()
            + self.info_conta()
            + self._format_size(self.empresa_mae, 30)
            + self._format_size(self.nome_banco(), 30)
            + " " * 10
            + "1"
            + self.data_geracao()
            + self.hora_geracao()
            + str(self.sequencial_remessa).rjust(6, "0")
            + self.versao_layout_arquivo()
            + self.densidade_gravacao()
            + self.uso_exclusivo_banco()
            + self.uso_exclusivo_empresa()
            + self.complemento_header()
        )

    def monta_segmento_p(self, pagamento: Pagamento, nro_lote: int, sequencial: int) -> str:
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "3"
            + str(sequencial).rjust(5, "0")
            + "P"
            + " "
            + pagamento.identificacao_ocorrencia
            + self._agencia4()
            + self._digito_agencia()
            + self.complemento_p(pagamento)
            + self.codigo_carteira
            + self.forma_cadastramento
            + self.tipo_documento
            + self.emissao_boleto
            + self.distribuicao_boleto
            + self._doc_ou_numero(pagamento, 15)
            + pagamento.data_vencimento.strftime("%d%m%Y")
            + pagamento.formata_valor(15)
            + "0" * 5
            + self.dv_agencia_cobradora()
            + self.especie_titulo
            + self.aceite
            + pagamento.data_emissao.strftime("%d%m%Y")
            + pagamento.tipo_mora
            + self.data_mora(pagamento)
            + self.valor_mora_segmento(pagamento)
            + self.codigo_desconto(pagamento)
            + pagamento.formata_data_desconto("%d%m%Y")
            + pagamento.formata_valor_desconto(15)
            + pagamento.formata_valor_iof(15)
            + pagamento.formata_valor_abatimento(15)
            + self._doc_ou_numero(pagamento, 25)
            + pagamento.codigo_protesto
            + str(pagamento.dias_protesto).rjust(2, "0")
            + self.codigo_baixa(pagamento)
            + "0"
            + self.dias_baixa(pagamento)
            + "00"
            + " " * 11
        )

    def monta_segmento_q(self, pagamento: Pagamento, nro_lote: int, sequencial: int) -> str:
        cep = so_digitos(pagamento.cep_sacado).rjust(8, "0")
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "3"
            + str(sequencial).rjust(5, "0")
            + "Q"
            + " "
            + pagamento.identificacao_ocorrencia
            + pagamento.identificacao_sacado(False)
            + so_alfanumerico(pagamento.documento_sacado).rjust(15, "0")
            + self._format_size(pagamento.nome_sacado, 40)
            + self._format_size(pagamento.endereco_sacado, 40)
            + self._format_size(pagamento.bairro_sacado, 15)
            + cep[0:5]
            + cep[5:8]
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + pagamento.identificacao_avalista(False)
            + so_alfanumerico(pagamento.documento_avalista).rjust(15, "0")
            + self._format_size(pagamento.nome_avalista, 40)
            + "0" * 12
            + " " * 19
        )
