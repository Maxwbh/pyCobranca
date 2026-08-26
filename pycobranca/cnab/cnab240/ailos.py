"""Remessa CNAB 240 — Ailos (085)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...core.documentos import so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab240Base

__all__ = ["RemessaAilos240"]


@dataclass
class RemessaAilos240(RemessaCnab240Base):
    campo_de_carteira: ClassVar[str | None] = "codigo_carteira"

    def __post_init__(self) -> None:
        self.forma_cadastramento = "0"
        self.tipo_documento = "1"

    def cod_banco(self) -> str:
        return "085"

    def nome_banco(self) -> str:
        return "AILOS".ljust(30)

    def versao_layout_arquivo(self) -> str:
        return "087"

    def versao_layout_lote(self) -> str:
        return "045"

    def _convenio(self) -> str:
        return so_digitos(self.convenio).rjust(6, "0")

    def _conta(self) -> str:
        return so_digitos(self.conta_corrente).rjust(7, "0")

    def _conta_dv(self) -> str:
        return str(modulo11_flex(self._conta(), mapa={10: 0}))

    def codigo_convenio(self) -> str:
        return self._convenio().ljust(20)

    def convenio_lote(self) -> str:
        return self.codigo_convenio()

    def uso_exclusivo_banco(self) -> str:
        return " " * 20

    def uso_exclusivo_empresa(self) -> str:
        return " " * 20

    def info_conta(self) -> str:
        agencia_conta = (
            self._agencia5()
            + str(self.digito_agencia)
            + self._conta().rjust(12, "0")
            + self._conta_dv()
        )
        return agencia_conta + " "

    def complemento_header(self) -> str:
        return " " * 29

    def complemento_trailer(self) -> str:
        total_simples = self._quantidade_titulos_cobranca() + self._valor_titulos_carteira()
        return (total_simples + "0" * 23 + "0" * 23 + "0" * 23).ljust(217)

    def _ajusta_nosso_numero(self, pagamento: Pagamento) -> str:
        return (
            self._conta() + self._conta_dv() + so_digitos(pagamento.nosso_numero).rjust(9, "0")
        ).ljust(20)

    def complemento_p(self, pagamento: Pagamento) -> str:
        return (
            self._conta().rjust(12, "0")
            + self._conta_dv()
            + " "
            + self._ajusta_nosso_numero(pagamento)
        )

    def identificacao_titulo_empresa(self, pagamento: Pagamento) -> str:
        return str(pagamento.documento_ou_numero).ljust(25)

    def monta_segmento_r(self, pagamento: Pagamento, nro_lote: int, sequencial: int):
        if pagamento.codigo_multa == "0":
            return None
        return super().monta_segmento_r(pagamento, nro_lote, sequencial)

    def codigo_baixa(self, pagamento: Pagamento) -> str:
        return "2"

    def dias_baixa(self, pagamento: Pagamento) -> str:
        return " " * 3
