"""Base da remessa CNAB 400 — porta fiel de ``Remessa::Cnab400::Base``."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import ClassVar

from ...exceptions import BoletoInvalido
from ..formatacao import avisa_carteira_ignorada, confere_tamanhos, remover_acentos
from ..pagamento import Pagamento, PagamentoPix

__all__ = ["RemessaCnab400Base"]


@dataclass
class RemessaCnab400Base:
    pagamentos: list[Pagamento] = field(default_factory=list)
    empresa_mae: str = ""
    agencia: str = ""
    conta_corrente: str = ""
    digito_conta: str = ""
    carteira: str = ""
    documento_cedente: str = ""
    aceite: str = "N"
    sequencial_remessa: str = "1"
    data_geracao: date | None = None

    #: Tamanhos aceitos para cada registro — um número, ou uma tupla quando o
    #: layout mistura tamanhos (o BRB tem header DCB de 39 e o resto de 400).
    #: ``None`` desliga a checagem, e desligar é caro: sem ela um campo que não
    #: cabe atravessa para a posição seguinte e o arquivo sai deslocado, sem
    #: nenhum sinal até o banco recusá-lo. Só a comparação byte a byte com a
    #: fixture sobra como guarda, e ela cobre um conjunto de dados apenas.
    tamanho_registro: int | tuple[int, ...] | None = 400

    # ---- por banco ----
    def cod_banco(self) -> str:
        raise NotImplementedError

    def nome_banco(self) -> str:
        raise NotImplementedError

    def info_conta(self) -> str:
        raise NotImplementedError

    def complemento(self) -> str:
        raise NotImplementedError

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        raise NotImplementedError

    # ---- comum ----
    def _data_geracao(self) -> str:
        return (self.data_geracao or date.today()).strftime("%d%m%y")

    def _format_size(self, texto: str, tamanho: int) -> str:
        from ..formatacao import format_size

        return format_size(texto, tamanho)

    def monta_header(self) -> str:
        return (
            "01REMESSA01COBRANCA       "
            f"{self.info_conta()}{self._format_size(self.empresa_mae, 30)}"
            f"{self.cod_banco()}{self.nome_banco()}{self._data_geracao()}"
            f"{self.complemento()}000001"
        )

    def monta_trailer(self, sequencial: int) -> str:
        return "9" + " " * 393 + str(sequencial).rjust(6, "0")

    #: Quando o layout **não** grava ``carteira``, o nome do campo que ele grava
    #: no lugar — ou ``""`` quando o layout não tem campo de carteira nenhum.
    #: ``None`` (o padrão) significa que este layout usa ``carteira``.
    campo_de_carteira: ClassVar[str | None] = None

    def validar(self) -> None:
        if not self.pagamentos:
            raise BoletoInvalido("remessa sem pagamentos")
        avisa_carteira_ignorada(self)
        for pagamento in self.pagamentos:
            pagamento.validar()

    def _monta_registros(self) -> list[str]:
        """Monta a lista de registros (sem CRLF/upcase), mirror de ``gera_arquivo``."""
        contador = 1
        linhas = [self.monta_header()]
        for pagamento in self.pagamentos:
            contador += 1
            linhas.append(self.monta_detalhe(pagamento, contador))
            if int(pagamento.codigo_multa or "0") > 0 and hasattr(self, "monta_detalhe_multa"):
                contador += 1
                linhas.append(self.monta_detalhe_multa(pagamento, contador))
            if isinstance(pagamento, PagamentoPix) and hasattr(self, "monta_detalhe_pix"):
                contador += 1
                linhas.append(self.monta_detalhe_pix(pagamento, contador))
        linhas.append(self.monta_trailer(contador + 1))
        return linhas

    def gera_arquivo(self) -> str:
        """Gera o arquivo completo (registros, CRLF, maiúsculas, sem acentos)."""
        self.validar()
        linhas = self._monta_registros()
        confere_tamanhos(linhas, self.tamanho_registro)
        conteudo = "\n".join(linhas)
        conteudo = remover_acentos(conteudo).upper() + "\n"
        return conteudo.replace("\n", "\r\n")
