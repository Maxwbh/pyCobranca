"""Remessa CNAB 400 — Sicoob (756).

Layout do ``Layout_Cobranca_CNAB400.xls`` publicado no portal do banco
(19/05/2025), aba *03.Remessa - CNAB400*. As posições foram conferidas uma a uma
contra essa planilha em ``test_remessa_sicoob_posicoes_do_layout_oficial``.

Duas coisas que a planilha esclareceu:

- **Não existe "tipo de formulário" no layout 400.** O atributo homônimo existia
  aqui e nunca era gravado — quem o informava mudava nada. É campo do **CNAB
  240**, onde segue em uso. Foi removido.
- ``modalidade_carteira`` grava a posição **106**, que a planilha chama de
  *Tipo de Emissão* (``1`` = cooperativa, ``2`` = cliente). Quem ocupa
  *Carteira/Modalidade* (107–108) é ``carteira``. O nome do atributo aponta para
  o campo vizinho; mantido por compatibilidade, documentado aqui.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_alfanumerico, so_digitos
from ...core.dv import modulo11_flex
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaSicoob400"]


@dataclass
class RemessaSicoob400(RemessaCnab400Base):
    convenio: str = ""
    #: Posição 106 — *Tipo de Emissão*: ``1`` cooperativa, ``2`` cliente.
    modalidade_carteira: str = "2"
    #: Posição 173 — *Tipo Distribuição*: ``1`` cooperativa, ``2`` cliente.
    distribuicao_boleto: str = "2"
    nome_banco_header: str = "BANCOOBCED"

    def cod_banco(self) -> str:
        return "756"

    def nome_banco(self) -> str:
        return self._format_size(self.nome_banco_header, 15)

    def _agencia(self) -> str:
        return so_digitos(self.agencia)

    def _convenio(self) -> str:
        return so_digitos(self.convenio).rjust(9, "0")

    def _digito_agencia(self) -> str:
        return str(modulo11_flex(self._agencia(), mapa={10: "0"}))

    def _tipo_empresa(self) -> str:
        return "01" if len(so_alfanumerico(self.documento_cedente)) <= 11 else "02"

    def info_conta(self) -> str:
        return f"{self._agencia()}{self._digito_agencia()}{self._convenio()}" + " " * 6

    @staticmethod
    def _seu_numero(pagamento: Pagamento) -> str:
        """Posições 111–120: *Seu Número*, que a planilha declara **X(10)**.

        Campo alfanumérico se alinha à esquerda e completa com brancos; numérico
        se alinha à direita e completa com zeros. Preencher com zero um valor que
        tem letras produz outro valor: ``DOC0001`` vira ``000DOC0001``, e é isso
        que o banco devolve no retorno. Quem guardou ``DOC0001`` não reencontra o
        título ao conciliar por esse campo.

        Valor só de dígitos continua com zeros à esquerda — ali as duas
        convenções coincidem e o comportamento anterior se mantém.
        """
        valor = str(pagamento.numero or "")
        if valor.isdigit():
            return valor.rjust(10, "0")[-10:]
        return valor.ljust(10)[:10]

    def complemento(self) -> str:
        return " " * 287

    def monta_header(self) -> str:
        return (
            "01REMESSA01COBRANCA       "
            + self.info_conta()
            + self._format_size(self.empresa_mae, 30)
            + self.cod_banco()
            + self.nome_banco()
            + self._data_geracao()
            + so_digitos(self.sequencial_remessa).rjust(7, "0")
            + self.complemento()
            + "000001"
        )

    def monta_trailer(self, sequencial: int) -> str:
        return "9" + "0" * 393 + str(sequencial).rjust(6, "0")

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        pagamento.validar()
        agencia = self._agencia()
        dig_ag = self._digito_agencia()
        return (
            "1"
            + self._tipo_empresa()
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
            + agencia
            + dig_ag
            + so_digitos(self.conta_corrente)
            + self.digito_conta
            + "000000"
            + " " * 25
            + so_digitos(pagamento.nosso_numero).rjust(12, "0")
            + str(pagamento.parcela).rjust(2, "0")
            + "00"
            + " " * 3
            + " "
            + " " * 3
            + "000"
            + "0"
            + "00000"
            + "0"
            + "000000"
            + " " * 4
            + self.modalidade_carteira
            + so_digitos(self.carteira).rjust(2, "0")
            + pagamento.identificacao_ocorrencia
            + self._seu_numero(pagamento)
            + pagamento.data_vencimento.strftime("%d%m%y")
            + pagamento.formata_valor()
            + self.cod_banco()
            + agencia
            + dig_ag
            + pagamento.especie_titulo
            + "0"
            + pagamento.data_emissao.strftime("%d%m%y")
            + "00"
            + "00"
            + pagamento.formata_valor_mora(6)
            + pagamento.formata_percentual_multa(6)
            + self.distribuicao_boleto
            + pagamento.formata_data_desconto()
            + pagamento.formata_valor_desconto()
            + pagamento.formata_valor_iof()
            + pagamento.formata_valor_abatimento()
            + pagamento.identificacao_sacado().rjust(2, "0")
            + so_alfanumerico(pagamento.documento_sacado).rjust(14, "0")
            + self._format_size(pagamento.nome_sacado, 40).ljust(40)
            + self._format_size(pagamento.endereco_sacado, 37).ljust(37)
            + self._format_size(pagamento.bairro_sacado, 15).ljust(15)
            + so_digitos(pagamento.cep_sacado)
            + self._format_size(pagamento.cidade_sacado, 15)
            + pagamento.uf_sacado
            + " " * 40
            + "00"
            + " "
            + str(sequencial).rjust(6, "0")
        )
