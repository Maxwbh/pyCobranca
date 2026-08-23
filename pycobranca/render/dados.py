"""Render DADOS — view-model dos renderizadores de PDF.

Separa **dados** (isto) de **desenho** (:mod:`pycobranca.render.boleto` e
:mod:`pycobranca.render.carne`): o dicionário de contexto do boleto é lido uma
única vez aqui, em :func:`extrai_dados`, e os layouts consomem apenas os campos
já normalizados de :class:`DadosBoleto`. Criar um tema/layout novo não exige
mexer na extração de dados.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["DadosBoleto", "extrai_dados"]


@dataclass(frozen=True)
class DadosBoleto:
    """Informações de um boleto/parcela — **fonte única de dados** dos renderizadores.

    Separa dados (isto) do desenho (layout): boleto e carnê consomem estes campos e
    não acessam o dicionário de contexto diretamente, o que facilita criar novos
    temas/layouts sem mexer na extração de dados.
    """

    banco_nome: str
    banco_dv: str
    banco_sigla: str
    banco_cor: str
    banco_logo: Any
    linha_digitavel: str
    local_pagamento: str
    vencimento: str
    valor_documento: str
    nosso_numero: str
    carteira: str
    especie_moeda: str
    quantidade: str
    beneficiario_nome: str
    beneficiario_documento: str
    beneficiario_endereco: str
    agencia_codigo: str
    doc_data: str
    doc_numero: str
    doc_especie: str
    doc_aceite: str
    doc_processamento: str
    sacado_nome: str
    sacado_documento: str
    sacado_endereco: str
    instrucoes: list
    demonstrativo: str
    codigo_barras: str
    sacador_avalista: str | None
    codigo_baixa: str
    tem_pix: bool
    qrcode_matrix: list | None
    #: Os cinco campos da faixa FEBRABAN, já formatados. String vazia quando o
    #: emissor não informou — é o caixa quem preenche no ato do pagamento.
    totalizadores: dict[str, str]

    def total(self, chave: str) -> str:
        """Totalizador formatado, ou vazio se não informado."""
        return self.totalizadores.get(chave, "")

    @property
    def beneficiario(self) -> str:
        return f"{self.beneficiario_nome} - {self.beneficiario_documento}"

    @property
    def sacado_curto(self) -> str:
        return f"{self.sacado_nome} - {self.sacado_documento}"

    @property
    def sacado_completo(self) -> str:
        return f"{self.sacado_nome} - {self.sacado_documento} — {self.sacado_endereco}"


def extrai_dados(contexto: dict[str, Any]) -> DadosBoleto:
    """Constrói o view-model a partir do dicionário de contexto."""
    d = contexto
    banco = d.get("banco", {})
    benef = d["beneficiario"]
    doc = d["documento"]
    pagador = d["pagador"]
    pix = d.get("pix") or {}
    return DadosBoleto(
        banco_nome=banco["nome"],
        banco_dv=banco["codigo_dv"],
        banco_sigla=banco.get("sigla", ""),
        banco_cor=banco.get("cor", "#003a70"),
        banco_logo=banco.get("logo"),
        linha_digitavel=d["linha_digitavel"],
        local_pagamento=d["local_pagamento"],
        vencimento=d["vencimento"],
        valor_documento=d["valor_documento"],
        nosso_numero=d["nosso_numero"],
        carteira=d["carteira"],
        especie_moeda=d["especie_moeda"],
        quantidade=str(d.get("quantidade") or ""),
        beneficiario_nome=benef["nome"],
        beneficiario_documento=benef["documento"],
        beneficiario_endereco=benef["endereco"],
        agencia_codigo=benef["agencia_codigo"],
        doc_data=doc["data"],
        doc_numero=doc["numero"],
        doc_especie=doc["especie"],
        doc_aceite=doc["aceite"],
        doc_processamento=doc["data_processamento"],
        sacado_nome=pagador["nome"],
        sacado_documento=pagador["documento"],
        sacado_endereco=pagador["endereco"],
        instrucoes=d.get("instrucoes") or [],
        demonstrativo=d.get("demonstrativo") or "",
        codigo_barras=d["codigo_barras"],
        sacador_avalista=d.get("sacador_avalista"),
        codigo_baixa=d.get("codigo_baixa") or "",
        tem_pix=bool(pix.get("habilitado") and pix.get("qrcode_matrix")),
        qrcode_matrix=pix.get("qrcode_matrix"),
        totalizadores=d.get("totalizadores") or {},
    )


# Aliases privados — compatibilidade com os nomes internos anteriores.
_Info = DadosBoleto
_informacoes = extrai_dados
