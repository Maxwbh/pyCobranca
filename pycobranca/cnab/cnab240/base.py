"""Base da remessa CNAB 240 — porta fiel de ``Remessa::Cnab240::Base``.

Estrutura em lotes: Header de Arquivo (registro 0), Header de Lote (1),
Segmentos P/Q/R (registro 3), Trailer de Lote (5) e Trailer de Arquivo (9).
Cada registro tem 240 posições. ``data_geracao``/``hora_geracao`` são
injetáveis para geração determinística (fixtures).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from ...core.documentos import so_alfanumerico, so_digitos
from ...exceptions import BoletoInvalido
from ..formatacao import confere_tamanhos, format_valor, remover_acentos
from ..pagamento import Pagamento, PagamentoPix

__all__ = ["RemessaCnab240Base"]


@dataclass
class RemessaCnab240Base:
    pagamentos: list[Pagamento] = field(default_factory=list)
    empresa_mae: str = ""
    agencia: str = ""
    conta_corrente: str = ""
    digito_conta: str = ""
    carteira: str = ""
    documento_cedente: str = ""
    aceite: str = "N"
    sequencial_remessa: str = "1"
    convenio: str = ""
    mensagem_1: str = ""
    mensagem_2: str = ""
    codigo_carteira: str = "1"
    forma_cadastramento: str = "1"
    emissao_boleto: str = "2"
    distribuicao_boleto: str = "2"
    especie_titulo: str = "02"
    tipo_documento: str = " "
    digito_agencia: str = ""
    #: ``DDMMAAAA``/``HHMMSS`` — vazios usam data/hora atuais (não determinístico).
    data_geracao_fixa: str = ""
    hora_geracao_fixa: str = ""
    tamanho_registro: int | tuple[int, ...] | None = 240

    # ------------------------------------------------------------------ #
    # Ganchos por banco (obrigatórios)
    # ------------------------------------------------------------------ #
    def cod_banco(self) -> str:
        raise NotImplementedError

    def nome_banco(self) -> str:
        raise NotImplementedError

    def info_conta(self) -> str:
        raise NotImplementedError

    def codigo_convenio(self) -> str:
        raise NotImplementedError

    def convenio_lote(self) -> str:
        raise NotImplementedError

    def versao_layout_arquivo(self) -> str:
        raise NotImplementedError

    def versao_layout_lote(self) -> str:
        raise NotImplementedError

    def complemento_header(self) -> str:
        raise NotImplementedError

    def complemento_trailer(self) -> str:
        raise NotImplementedError

    def complemento_p(self, pagamento: Pagamento) -> str:
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Ganchos com default (sobrescrever quando necessário)
    # ------------------------------------------------------------------ #
    def _digito_agencia(self) -> str:
        """DV da agência. Bancos que passam o dígito usam o campo homônimo;
        bancos que calculam (BB, Sicoob, Sicredi, Santander) sobrescrevem."""
        return str(self.digito_agencia)

    def densidade_gravacao(self) -> str:
        return "00000"

    def uso_exclusivo_banco(self) -> str:
        return "0" * 20

    def uso_exclusivo_empresa(self) -> str:
        return "0" * 20

    def exclusivo_servico(self) -> str:
        return " " * 2

    def dv_agencia_cobradora(self) -> str:
        return "0"

    def data_geracao(self) -> str:
        return self.data_geracao_fixa or date.today().strftime("%d%m%Y")

    def hora_geracao(self) -> str:
        return self.hora_geracao_fixa or datetime.now().strftime("%H%M%S")

    def _format_size(self, texto: str, tamanho: int) -> str:
        from ..formatacao import format_size

        return format_size(texto, tamanho)

    def _tipo_empresa(self, documento: str) -> str:
        return "1" if len(so_alfanumerico(documento)) <= 11 else "2"

    def _agencia5(self) -> str:
        return so_digitos(self.agencia).rjust(5, "0")

    # -- complementos do segmento (default) --
    def complemento_r(self) -> str:
        return " " * 20 + "0" * 8 + "0" * 3 + "0" * 5 + " " + "0" * 12 + " " + " " + "0" + " " * 9

    def numero(self, pagamento: Pagamento) -> str:
        return pagamento.formata_documento_ou_numero(15, "0")

    def identificacao_titulo_empresa(self, pagamento: Pagamento) -> str:
        return pagamento.formata_documento_ou_numero()

    def data_multa(self, pagamento: Pagamento) -> str:
        if pagamento.codigo_multa == "0":
            return "0" * 8
        data = pagamento.data_multa or pagamento.data_vencimento
        return data.strftime("%d%m%Y")

    def data_mora(self, pagamento: Pagamento) -> str:
        if pagamento.tipo_mora not in ("1", "2"):
            return "0" * 8
        data = pagamento.data_mora or pagamento.data_vencimento
        return data.strftime("%d%m%Y")

    def valor_mora_segmento(self, pagamento: Pagamento, tamanho: int = 15) -> str:
        """Juros de mora do segmento P: percentual quando ``tipo_mora == "2"``
        (Taxa Mensal, FEBRABAN); valor ao dia caso contrário."""
        if pagamento.tipo_mora == "2":
            return pagamento.formata_percentual_mora(tamanho)
        return pagamento.formata_valor_mora(tamanho)

    def descontos_adicionais(self, pagamento: Pagamento) -> str:
        """Slots de 2º e 3º desconto do segmento R (código[1] + data[8] + valor[15]
        cada). Com os defaults (sem 2º/3º desconto) resulta em zeros — idêntico ao
        preenchimento fixo anterior."""
        return (
            pagamento.cod_segundo_desconto
            + pagamento.formata_data_segundo_desconto("%d%m%Y")
            + pagamento.formata_valor_segundo_desconto(15)
            + pagamento.cod_terceiro_desconto
            + pagamento.formata_data_terceiro_desconto("%d%m%Y")
            + pagamento.formata_valor_terceiro_desconto(15)
        )

    def codigo_desconto(self, pagamento: Pagamento) -> str:
        return pagamento.cod_desconto

    def codigo_baixa(self, pagamento: Pagamento) -> str:
        return pagamento.codigo_baixa

    def dias_baixa(self, pagamento: Pagamento) -> str:
        return str(pagamento.dias_baixa).rjust(3, "0")

    # ------------------------------------------------------------------ #
    # Registros
    # ------------------------------------------------------------------ #
    def monta_header_arquivo(self) -> str:
        return (
            self.cod_banco()
            + "0000"
            + "0"
            + " " * 9
            + self._tipo_empresa(self.documento_cedente)
            + so_alfanumerico(self.documento_cedente).rjust(14, "0")
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

    def monta_header_lote(self, nro_lote: int) -> str:
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "1"
            + "R"
            + "01"
            + self.exclusivo_servico()
            + self.versao_layout_lote()
            + " "
            + self._tipo_empresa(self.documento_cedente)
            + so_alfanumerico(self.documento_cedente).rjust(15, "0")
            + self.convenio_lote()
            + self.info_conta()
            + self._format_size(self.empresa_mae, 30)
            + self._format_size(self.mensagem_1, 40)
            + self._format_size(self.mensagem_2, 40)
            + str(self.sequencial_remessa).rjust(8, "0")
            + self.data_geracao()
            + "0" * 8
            + " " * 33
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
            + self._agencia5()
            + self._digito_agencia()
            + self.complemento_p(pagamento)
            + self.codigo_carteira
            + self.forma_cadastramento
            + self.tipo_documento
            + self.emissao_boleto
            + self.distribuicao_boleto
            + self.numero(pagamento)
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
            + self.identificacao_titulo_empresa(pagamento)
            + pagamento.codigo_protesto
            + str(pagamento.dias_protesto).rjust(2, "0")
            + self.codigo_baixa(pagamento)
            + self.dias_baixa(pagamento)
            + "09"
            + "0" * 10
            + " "
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
            + "0" * 3
            + " " * 20
            + " " * 8
        )

    def monta_segmento_r(self, pagamento: Pagamento, nro_lote: int, sequencial: int) -> str | None:
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "3"
            + str(sequencial).rjust(5, "0")
            + "R"
            + " "
            + pagamento.identificacao_ocorrencia
            + self.descontos_adicionais(pagamento)
            + pagamento.codigo_multa
            + self.data_multa(pagamento)
            + pagamento.formata_percentual_multa(15)
            + " " * 10
            + " " * 40
            + " " * 40
            + self.complemento_r()
        )

    def monta_trailer_lote(self, nro_lote: int, nro_registros: int) -> str:
        return (
            self.cod_banco()
            + str(nro_lote).rjust(4, "0")
            + "5"
            + " " * 9
            + str(nro_registros).rjust(6, "0")
            + self.complemento_trailer()
        )

    def monta_trailer_arquivo(self, nro_lotes: int, sequencial: int) -> str:
        return (
            self.cod_banco()
            + "99999"
            + " " * 9
            + str(nro_lotes).rjust(6, "0")
            + str(sequencial).rjust(6, "0")
            + " " * 211
        )

    # ------------------------------------------------------------------ #
    # Montagem
    # ------------------------------------------------------------------ #
    def monta_lote(self, nro_lote: int) -> list[str]:
        contador = 1  # header do lote
        lote = [self.monta_header_lote(nro_lote)]
        for pagamento in self.pagamentos:
            pagamento.validar()
            lote.append(self.monta_segmento_p(pagamento, nro_lote, contador))
            contador += 1
            lote.append(self.monta_segmento_q(pagamento, nro_lote, contador))
            contador += 1
            seg_r = self.monta_segmento_r(pagamento, nro_lote, contador)
            if seg_r is not None:
                lote.append(seg_r)
                contador += 1
            if isinstance(pagamento, PagamentoPix) and hasattr(self, "monta_segmento_y"):
                seg_y = self.monta_segmento_y(pagamento, nro_lote, contador)
                if seg_y:
                    lote.append(seg_y)
                    contador += 1
        contador += 1  # trailer do lote
        lote.append(self.monta_trailer_lote(nro_lote, contador))
        return lote

    def validar(self) -> None:
        if not self.pagamentos:
            raise BoletoInvalido("remessa sem pagamentos")
        if not self.empresa_mae:
            raise BoletoInvalido("empresa_mae obrigatória")
        for pagamento in self.pagamentos:
            pagamento.validar()

    def gera_arquivo(self) -> str:
        self.validar()
        arquivo = [self.monta_header_arquivo()]
        contador = 1
        arquivo.extend(self.monta_lote(contador))
        # Quantidade de registros do arquivo (FEBRABAN): total físico de registros
        # (tipos 0, 1, 3, 5 e 9) — conta as linhas reais, incluindo o segmento Y do
        # PIX. O ``+ 1`` é o próprio trailer de arquivo, ainda não anexado.
        total_linhas = len(arquivo) + 1
        arquivo.append(self.monta_trailer_arquivo(contador, total_linhas))
        confere_tamanhos(arquivo, self.tamanho_registro)
        conteudo = "\n".join(arquivo)
        conteudo = remover_acentos(conteudo).upper() + "\n"
        return conteudo.replace("\n", "\r\n")

    # utilitário para trailers de cooperativas
    def _quantidade_titulos_cobranca(self) -> str:
        return str(len(self.pagamentos)).rjust(6, "0")

    def _valor_titulos_carteira(self, tamanho: int = 17) -> str:
        total = sum(float(p.valor) for p in self.pagamentos)
        return format_valor(total, tamanho)
