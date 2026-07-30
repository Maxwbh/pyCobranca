"""Pagamento (título) da remessa — campos e formatadores CNAB."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from ..core.documentos import so_alfanumerico, so_digitos
from ..exceptions import BoletoInvalido
from .formatacao import format_valor

__all__ = ["Pagamento", "PagamentoPix"]


@dataclass
class Pagamento:
    """Título a registrar na remessa (equivalente a ``Remessa::Pagamento``).

    Os valores default cobrem os campos opcionais mais comuns para que a
    geração byte a byte não dependa de o chamador informar campos opcionais.
    """

    nosso_numero: str = ""
    data_vencimento: date | None = None
    valor: float = 0.0
    documento_sacado: str = ""
    nome_sacado: str = ""
    endereco_sacado: str = ""
    bairro_sacado: str = ""
    cep_sacado: str = ""
    cidade_sacado: str = ""
    uf_sacado: str = ""
    data_emissao: date | None = None
    numero: str = ""
    documento: str = ""
    nome_avalista: str = ""
    documento_avalista: str = ""
    identificacao_ocorrencia: str = "01"
    especie_titulo: str = "01"
    cod_primeira_instrucao: str = "00"
    cod_segunda_instrucao: str = "00"
    codigo_multa: str = "0"
    percentual_multa: float = 0.0
    data_multa: date | None = None
    tipo_mora: str = "3"
    valor_mora: float = 0.0
    #: Percentual de mora (taxa mensal) — usado quando ``tipo_mora == "2"``
    #: (FEBRABAN "Taxa Mensal"). ``valor_mora`` continua sendo o valor ao dia
    #: para ``tipo_mora == "1"``.
    percentual_mora: float = 0.0
    data_mora: date | None = None
    cod_desconto: str = "0"
    data_desconto: date | None = None
    valor_desconto: float = 0.0
    cod_segundo_desconto: str = "0"
    data_segundo_desconto: date | None = None
    valor_segundo_desconto: float = 0.0
    cod_terceiro_desconto: str = "0"
    data_terceiro_desconto: date | None = None
    valor_terceiro_desconto: float = 0.0
    valor_iof: float = 0.0
    valor_abatimento: float = 0.0
    codigo_protesto: str = "3"
    dias_protesto: str = "00"
    codigo_baixa: str = "0"
    dias_baixa: str = "000"
    parcela: str = "01"

    def __post_init__(self) -> None:
        if self.data_emissao is None:
            self.data_emissao = date.today()

    def validar(self) -> None:
        """Regras de geração da remessa CNAB (campos e coerência de encargos).

        Levanta :class:`BoletoInvalido` com a lista **estruturada** de erros
        (``.erros``) — pronta para uma camada REST mapear cada item.
        """
        erros: list[str] = []
        for campo in (
            "nosso_numero",
            "documento_sacado",
            "nome_sacado",
            "endereco_sacado",
            "cep_sacado",
        ):
            if not getattr(self, campo):
                erros.append(f"campo obrigatório ausente: {campo}")
        if self.data_vencimento is None:
            erros.append("campo obrigatório ausente: data_vencimento")
        if not self.valor or float(self.valor) <= 0:
            erros.append("valor deve ser positivo")
        for campo in (
            "valor_mora",
            "percentual_mora",
            "percentual_multa",
            "valor_desconto",
            "valor_segundo_desconto",
            "valor_terceiro_desconto",
            "valor_iof",
            "valor_abatimento",
        ):
            if float(getattr(self, campo) or 0) < 0:
                erros.append(f"{campo} não pode ser negativo")
        # coerência de juros/mora
        if self.tipo_mora == "1" and float(self.valor_mora or 0) <= 0:
            erros.append('tipo_mora="1" (valor ao dia) exige valor_mora > 0')
        if self.tipo_mora == "2" and float(self.percentual_mora or 0) <= 0:
            erros.append('tipo_mora="2" (taxa mensal) exige percentual_mora > 0')
        # coerência de multa (FEBRABAN: multa é sempre percentual)
        if self.codigo_multa in ("1", "2") and float(self.percentual_multa or 0) <= 0:
            erros.append("codigo_multa != 0 exige percentual_multa > 0")
        # coerência de desconto (1º/2º/3º)
        for cod, valor, data, rotulo in (
            (self.cod_desconto, self.valor_desconto, self.data_desconto, "1º desconto"),
            (
                self.cod_segundo_desconto,
                self.valor_segundo_desconto,
                self.data_segundo_desconto,
                "2º desconto",
            ),
            (
                self.cod_terceiro_desconto,
                self.valor_terceiro_desconto,
                self.data_terceiro_desconto,
                "3º desconto",
            ),
        ):
            if cod and cod != "0":
                if float(valor or 0) <= 0:
                    erros.append(f"{rotulo} indicado (cód. != 0) exige valor > 0")
                if data is None:
                    erros.append(f"{rotulo} indicado (cód. != 0) exige data")
        # sacado
        if self.uf_sacado and len(str(self.uf_sacado).strip()) != 2:
            erros.append("uf_sacado deve ter 2 letras")
        if self.cep_sacado and len(so_digitos(self.cep_sacado)) > 8:
            erros.append("cep_sacado deve ter no máximo 8 dígitos")
        if erros:
            raise BoletoInvalido(erros)

    @property
    def documento_ou_numero(self) -> str:
        return self.documento or self.numero

    def formata_documento_ou_numero(self, tamanho: int = 25, caracter: str = " ") -> str:
        doc = re.sub(r"[^0-9A-Za-z ]", "", str(self.documento_ou_numero))
        return doc.rjust(tamanho, caracter)[:tamanho]

    def identificacao_sacado(self, zero: bool = True) -> str:
        tipo = "1" if len(so_alfanumerico(self.documento_sacado)) <= 11 else "2"
        return tipo.rjust(2, "0") if zero else tipo

    def identificacao_avalista(self, zero: bool = True) -> str:
        if not self.documento_avalista:
            return "0"
        tipo = "1" if len(so_alfanumerico(self.documento_avalista)) <= 11 else "2"
        return tipo.rjust(2, "0") if zero else tipo

    # ---- valores (%.2f sem ponto, à direita com zeros) ----
    def formata_valor(self, tamanho: int = 13) -> str:
        return format_valor(self.valor, tamanho)

    def formata_valor_mora(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_mora, tamanho)

    def formata_percentual_mora(self, tamanho: int = 13) -> str:
        return format_valor(self.percentual_mora, tamanho)

    def formata_valor_desconto(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_desconto, tamanho)

    def formata_valor_segundo_desconto(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_segundo_desconto, tamanho)

    def formata_valor_terceiro_desconto(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_terceiro_desconto, tamanho)

    def formata_valor_iof(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_iof, tamanho)

    def formata_valor_abatimento(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_abatimento, tamanho)

    def formata_percentual_multa(self, tamanho: int = 4) -> str:
        return format_valor(self.percentual_multa, tamanho)

    def formata_valor_multa(self, tamanho: int = 6) -> str:
        """Compat.: no padrão FEBRABAN a multa do título é sempre **percentual**
        (não há valor monetário de multa), então isto é um alias de
        :meth:`formata_percentual_multa`. Prefira ``formata_percentual_multa``.
        """
        return self.formata_percentual_multa(tamanho)

    # ---- datas (strftime ou zeros) ----
    @staticmethod
    def _zeros_data(formato: str) -> str:
        return "000000" if formato == "%d%m%y" else "00000000"

    def formata_data_desconto(self, formato: str = "%d%m%y") -> str:
        return (
            self.data_desconto.strftime(formato)
            if self.data_desconto
            else self._zeros_data(formato)
        )

    def formata_data_segundo_desconto(self, formato: str = "%d%m%y") -> str:
        if self.data_segundo_desconto:
            return self.data_segundo_desconto.strftime(formato)
        return self._zeros_data(formato)

    def formata_data_terceiro_desconto(self, formato: str = "%d%m%y") -> str:
        if self.data_terceiro_desconto:
            return self.data_terceiro_desconto.strftime(formato)
        return self._zeros_data(formato)

    def formata_data_multa(self, formato: str = "%d%m%y") -> str:
        return self.data_multa.strftime(formato) if self.data_multa else self._zeros_data(formato)


@dataclass
class PagamentoPix(Pagamento):
    """Título de remessa com dados PIX (Bolepix) — equivale a ``PagamentoPix``.

    Acrescenta os campos da chave DICT/TXID e os limites de valor usados no
    registro tipo 8 (CNAB 400) e no segmento Y-03 (CNAB 240). Os defaults
    cobrem os campos opcionais mais comuns.
    """

    #: Tipos de chave DICT aceitos (BCB).
    TIPOS_CHAVE_DICT = ("cpf", "cnpj", "email", "telefone", "chave_aleatoria")

    tipo_chave_dict: str = "cnpj"
    codigo_chave_dict: str = ""
    txid: str = ""
    tipo_pagamento_pix: str = "00"
    quantidade_pagamentos_pix: str = "01"
    tipo_valor_pix: str = "1"
    valor_maximo_pix: float = 100.0
    percentual_maximo_pix: float = 100.0
    valor_minimo_pix: float = 100.0
    percentual_minimo_pix: float = 100.0

    def validar(self) -> None:
        super().validar()
        if not self.codigo_chave_dict:
            raise BoletoInvalido("pagamento PIX incompleto: codigo_chave_dict")
        if self.tipo_chave_dict not in self.TIPOS_CHAVE_DICT:
            raise BoletoInvalido(
                f"tipo_chave_dict inválido: {self.tipo_chave_dict!r} "
                f"(use {', '.join(self.TIPOS_CHAVE_DICT)})"
            )

    def formata_valor_maximo_pix(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_maximo_pix, tamanho)

    def formata_valor_minimo_pix(self, tamanho: int = 13) -> str:
        return format_valor(self.valor_minimo_pix, tamanho)

    def formata_percentual_maximo_pix(self, tamanho: int = 5) -> str:
        return format_valor(self.percentual_maximo_pix, tamanho)

    def formata_percentual_minimo_pix(self, tamanho: int = 5) -> str:
        return format_valor(self.percentual_minimo_pix, tamanho)
