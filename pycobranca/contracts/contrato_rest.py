"""Contrato de dados para consumo via API REST.

Este módulo **não** faz chamadas HTTP (o SDK é um projeto à parte). Ele traduz
os artefatos da engine (boleto, remessa, retorno) para o formato exato dos
schemas REST (OpenAPI 3.0) e oferece um validador leve para os **testes de
contrato**, garantindo que a serialização permaneça compatível conforme a API
evolui.

Fonte do contrato: :data:`CONTRATO` (``contrato_rest.json``), mantido em
sincronia manual com o domínio — o próprio arquivo é a referência.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..exceptions import BancoNaoRegistrado, PyCobrancaError

__all__ = [
    "CONTRATO",
    "SLUG_POR_CODIGO",
    "TOTALIZADORES",
    "CAMPOS_POR_BANCO",
    "NOMES_DO_CONTRATO",
    "TEMA_DO_CONTRATO",
    "boleto_para_api",
    "boleto_de_api",
    "tema_de_api",
    "pagamento_para_api",
    "remessa_para_api",
    "retorno_item_para_api",
    "valida_contrato",
    "openapi_de",
    "ErroDeContrato",
]

_CAMINHO_CONTRATO = Path(__file__).with_name("contrato_rest.json")
CONTRATO: dict[str, Any] = json.loads(_CAMINHO_CONTRATO.read_text(encoding="utf-8"))

#: Código FEBRABAN → slug do banco aceito pela API (``bank``).
SLUG_POR_CODIGO: dict[str, str] = {
    "001": "banco_brasil",
    "004": "banco_nordeste",
    "021": "banestes",
    "033": "santander",
    "041": "banrisul",
    "070": "banco_brasilia",
    "077": "inter",
    "085": "ailos",
    "097": "credisis",
    "104": "caixa",
    "136": "unicred",
    "237": "bradesco",
    "336": "banco_c6",
    "341": "itau",
    "399": "hsbc",
    "422": "safra",
    "745": "citibank",
    "748": "sicredi",
    "756": "sicoob",
}

#: Inverso de :data:`SLUG_POR_CODIGO`, para o caminho de volta.
_CODIGO_POR_SLUG: dict[str, str] = {slug: cod for cod, slug in SLUG_POR_CODIGO.items()}


#: Os cinco campos da faixa FEBRABAN, na ordem em que aparecem no boleto. Os
#: nomes são idênticos aos de :class:`~pycobranca.bancos.base.BancoBase`, então
#: o consumidor não precisa de tradução nos dois sentidos.
TOTALIZADORES = (
    "desconto_abatimento",
    "outras_deducoes",
    "mora_multa",
    "outros_acrescimos",
    "valor_cobrado",
)

#: Campos específicos de banco que entram no campo livre ou são obrigatórios
#: por regra própria. Sem eles o contrato não expressa 7 dos 18 bancos — e o
#: Citibank sem ``portfolio`` produzia um código de barras **diferente**, válido
#: em estrutura e errado no destino, sem levantar exceção.
CAMPOS_POR_BANCO = (
    "data_documento",
    "digito_conta",
    "digito_agencia",
    "digito_convenio",
    "variacao",
    "incremento",
    "portfolio",
    "posto",
    "byte_idt",
)

#: ``nome no contrato -> nome no construtor``. São as únicas quatro divergências;
#: ``documento_cedente``/``cedente_documento`` inverte as palavras, que é o tipo
#: de detalhe em que um mapeamento escrito à mão erra.
NOMES_DO_CONTRATO: dict[str, str] = {
    "conta_corrente": "conta",
    "documento_cedente": "cedente_documento",
    "chave_pix": "pix_chave",
    "pix_copia_cola": "pix_copia_cola",
    "txid": "pix_txid",
    "pix_observacao": "pix_observacao",
}

#: ``nome no contrato -> chave do bloco ``tema`` no contexto de render``. O
#: renderizador usa outro vocabulário, e sem este mapa cada consumidor inventa
#: o seu. ``empresa`` não tem campo no contrato: cai de ``logo_empresa``.
TEMA_DO_CONTRATO: dict[str, str] = {
    "cor_marca": "cor",
    "logo_empresa": "logo_texto",
    "marca_dagua": "marca_dagua",
    "rodape_contato": "rodape",
}

#: Campos do ``BoletoData`` que a engine não consome na construção do título:
#: ``emv`` é saída (a própria PyCobrança o gera), ``tipo_chave_pix`` e
#: ``pix_label`` são rótulo, ``fonte_ttf`` não tem suporte, e ``itens``/``fatura``
#: pertencem a :func:`~pycobranca.render.render_fatura_pdf`.
_IGNORADOS_NA_CONSTRUCAO = frozenset(
    {"emv", "pix_label", "tipo_chave_pix", "fonte_ttf", "itens", "fatura"}
)

#: Datas do contrato chegam como ISO 8601 e o construtor espera ``date``.
_CAMPOS_DATA = frozenset({"data_vencimento", "data_documento"})


class ErroDeContrato(PyCobrancaError, ValueError):
    """Falha de validação de um artefato contra o contrato REST."""


# --------------------------------------------------------------------------- #
# Serializadores (engine → formato da API)
# --------------------------------------------------------------------------- #
def _num(valor: Decimal | str | float | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def _data_iso(valor: date | None) -> str | None:
    return valor.isoformat() if valor else None


def _sem_nulos(dados: dict) -> dict:
    return {k: v for k, v in dados.items() if v is not None}


def boleto_para_api(banco) -> dict[str, Any]:
    """Serializa um boleto (:class:`~pycobranca.bancos.base.BancoBase`) para o
    corpo esperado por ``GET /api/boleto`` — ``{"bank": slug, "data": BoletoData}``."""
    data: dict[str, Any] = {
        "agencia": banco.agencia,
        "conta_corrente": banco.conta,
        "nosso_numero": banco.nosso_numero,
        "valor": _num(banco.valor),
        "cedente": banco.cedente,
        "documento_cedente": banco.cedente_documento,
        "sacado": banco.sacado,
        "sacado_documento": banco.sacado_documento,
        "carteira": banco.carteira or None,
        "convenio": banco.convenio or None,
        "data_vencimento": _data_iso(banco.data_vencimento),
        "numero_documento": getattr(banco, "numero_documento", "") or None,
        "sacado_endereco": getattr(banco, "sacado_endereco", "") or None,
    }
    # Faixa de totalizadores. `_sem_nulos` derruba os não informados, então um
    # boleto sem encargos sai com o payload idêntico ao de antes deste campo —
    # e `0` informado de propósito sobrevive, porque só `None` é descartado.
    for campo in TOTALIZADORES:
        data[campo] = _num(getattr(banco, campo, None))
    # Campos específicos de banco: sem eles o payload não reconstrói o título.
    for campo in CAMPOS_POR_BANCO:
        valor = getattr(banco, campo, None)
        data[campo] = _data_iso(valor) if isinstance(valor, date) else (valor or None)
    # Bolepix: quando o banco suporta PIX e há chave configurada.
    if getattr(banco, "pix_copia_cola", ""):
        data["pix_copia_cola"] = banco.pix_copia_cola
    if getattr(banco, "suporta_pix", False) and getattr(banco, "pix_chave", ""):
        data["chave_pix"] = banco.pix_chave
        if getattr(banco, "pix_txid", ""):
            data["txid"] = banco.pix_txid
    # Sem ``.get`` com padrão: um banco fora do mapa devolvia o **código** no lugar
    # do slug, e o payload seguia parecendo válido — `boleto_para_api` entregava
    # ``bank: "077"`` e `boleto_de_api` recusava ``"inter"``, cada ponta com uma
    # verdade. Melhor falhar aqui, dizendo o que fazer.
    if banco.codigo not in SLUG_POR_CODIGO:
        raise ErroDeContrato(
            f"banco {banco.codigo} ({banco.nome}) não tem slug em SLUG_POR_CODIGO — "
            "todo banco do registro precisa de um para entrar no contrato REST"
        )
    return {"bank": SLUG_POR_CODIGO[banco.codigo], "data": _sem_nulos(data)}


def tema_de_api(data: dict[str, Any]) -> dict[str, Any] | None:
    """Bloco ``tema`` do contexto de render, a partir de um ``BoletoData``.

    O contrato e o renderizador usam vocabulários diferentes para a faixa de
    marca (``cor_marca`` × ``cor``, ``rodape_contato`` × ``rodape``…). Sem esta
    tradução cada consumidor escreve a sua, e ``empresa`` — o texto mais visível
    da faixa — não tem campo próprio no contrato, então herda ``logo_empresa``.

    Devolve ``None`` quando nenhum campo de tema foi informado, que é o caso em
    que o boleto sai sem faixa.
    """
    tema = {
        destino: data[origem]
        for origem, destino in TEMA_DO_CONTRATO.items()
        if data.get(origem) not in (None, "")
    }
    if not tema:
        return None
    if "logo_texto" in tema:
        tema.setdefault("empresa", tema["logo_texto"])
    atual, total = data.get("parcela_atual"), data.get("total_parcelas")
    if atual and total:
        tema["parcela_texto"] = f"Parcela {atual}/{total}"
    return {"habilitado": True, **tema}


def boleto_de_api(payload: dict[str, Any]):
    """``{"bank": slug, "data": BoletoData}`` → instância do banco, pronta para uso.

    É o caminho de volta de :func:`boleto_para_api`. Sem ele, todo consumidor
    reescreve as quatro traduções de nome, a conversão das datas ISO e a lista
    de campos que a engine não aceita no construtor — e errar qualquer uma
    delas produz título inválido ou, pior, título **válido e errado**.

    O bloco de instruções (``instrucao1``/``instrucao2``) vira a lista
    ``instrucoes``. Os campos de apresentação (tema, fatura) não entram aqui:
    use :func:`tema_de_api` e :func:`~pycobranca.render.render_fatura_pdf`.

    Toda falha sai como :class:`~pycobranca.exceptions.PyCobrancaError` — é o
    ponto da fronteira. Campo desconhecido e data mal formada viram
    ``ErroDeContrato`` nomeando o campo, em vez do ``TypeError`` do construtor e
    do ``ValueError`` de ``fromisoformat``, que escapariam de um ``except`` da
    biblioteca e não diriam onde está o problema.

    Raises:
        ErroDeContrato: se ``data`` não satisfizer o schema, trouxer campo que a
            engine não conhece ou data em formato diferente de ISO 8601.
        BancoNaoRegistrado: se ``bank`` não corresponder a banco suportado.
        BoletoInvalido: se os dados violarem as regras do banco (em ``validar()``).
    """
    import dataclasses

    from ..bancos import Bancos

    data = payload.get("data") or {}
    valida_contrato(data, "BoletoData")

    # `bank` vem de JSON e pode chegar como qualquer coisa; normalizar para texto
    # antes da busca evita TypeError num `dict.get` com chave não-hasheável.
    bank = payload.get("bank")
    procurado = bank if isinstance(bank, str) else str(bank)
    try:
        Banco = Bancos.find(_CODIGO_POR_SLUG.get(procurado, procurado))
    except BancoNaoRegistrado as erro:
        # A mensagem de `find` mostra o código já normalizado com zeros à
        # esquerda: um `bank` de lista virava "0[]", nomeando um banco que o
        # chamador nunca mandou. Aqui o valor recebido aparece como veio.
        raise BancoNaoRegistrado(f"bank {bank!r} não corresponde a banco suportado") from erro
    aceitos = {f.name for f in dataclasses.fields(Banco)}

    kwargs: dict[str, Any] = {}
    instrucoes = [data[c] for c in ("instrucao1", "instrucao2") if data.get(c)]
    for chave, valor in data.items():
        if valor is None or chave in _IGNORADOS_NA_CONSTRUCAO or chave in TEMA_DO_CONTRATO:
            continue
        if chave in ("instrucao1", "instrucao2", "parcela_atual", "total_parcelas"):
            continue
        destino = NOMES_DO_CONTRATO.get(chave, chave)
        # `additionalProperties` é permissivo no validador, então chave estranha
        # chega até aqui. Recusar nomeando-a acha o erro de digitação; deixar
        # passar entregaria um boleto sem o campo que o chamador achou que mandou.
        if destino not in aceitos:
            raise ErroDeContrato(
                f"BoletoData.{chave}: campo desconhecido para o banco {Banco.nome} ({Banco.codigo})"
            )
        if destino in _CAMPOS_DATA and isinstance(valor, str):
            try:
                valor = date.fromisoformat(valor)
            except ValueError as erro:
                raise ErroDeContrato(
                    f"BoletoData.{chave}: {valor!r} não é uma data ISO 8601 (AAAA-MM-DD)"
                ) from erro
        kwargs[destino] = valor
    if instrucoes:
        kwargs["instrucoes"] = instrucoes
    return Banco(**kwargs)


def _desconto_para_api(codigo, valor, data) -> dict[str, Any] | None:
    """Um desconto (código/valor/data) — ``None`` quando inativo (código ``0``
    e valor zero)."""
    ativo = str(codigo or "0") != "0" or bool(_num(valor))
    if not ativo:
        return None
    item = _sem_nulos(
        {"codigo": codigo or None, "valor": _num(valor) or None, "data": _data_iso(data)}
    )
    return item or None


def _encargos_para_api(pagamento) -> dict[str, Any] | None:
    """Serializa juros/mora, multa, descontos (1º/2º/3º), IOF e abatimento para o
    schema ``Encargos``. Retorna ``None`` quando nenhum encargo está ativo (assim
    o campo some do payload e pagamentos sem encargo ficam idênticos ao anterior)."""
    enc: dict[str, Any] = {}

    if (
        str(pagamento.tipo_mora) != "3"
        or _num(pagamento.valor_mora)
        or _num(pagamento.percentual_mora)
    ):
        enc["mora"] = _sem_nulos(
            {
                "tipo": pagamento.tipo_mora,
                "valor": _num(pagamento.valor_mora) or None,
                "percentual": _num(pagamento.percentual_mora) or None,
                "data": _data_iso(pagamento.data_mora),
            }
        )

    if str(pagamento.codigo_multa) != "0" or _num(pagamento.percentual_multa):
        enc["multa"] = _sem_nulos(
            {
                "codigo": pagamento.codigo_multa,
                "percentual": _num(pagamento.percentual_multa) or None,
                "data": _data_iso(pagamento.data_multa),
            }
        )

    descontos = [
        d
        for d in (
            _desconto_para_api(
                pagamento.cod_desconto, pagamento.valor_desconto, pagamento.data_desconto
            ),
            _desconto_para_api(
                pagamento.cod_segundo_desconto,
                pagamento.valor_segundo_desconto,
                pagamento.data_segundo_desconto,
            ),
            _desconto_para_api(
                pagamento.cod_terceiro_desconto,
                pagamento.valor_terceiro_desconto,
                pagamento.data_terceiro_desconto,
            ),
        )
        if d
    ]
    if descontos:
        enc["descontos"] = descontos
    if _num(pagamento.valor_iof):
        enc["iof"] = _num(pagamento.valor_iof)
    if _num(pagamento.valor_abatimento):
        enc["abatimento"] = _num(pagamento.valor_abatimento)
    return enc or None


def pagamento_para_api(pagamento) -> dict[str, Any]:
    """Serializa um :class:`~pycobranca.cnab.pagamento.Pagamento` para o schema
    ``Pagamento`` da remessa (inclui ``encargos`` quando houver)."""
    dados = {
        "nosso_numero": pagamento.nosso_numero,
        "numero_documento": pagamento.documento_ou_numero or None,
        "data_vencimento": _data_iso(pagamento.data_vencimento),
        "valor": _num(pagamento.valor),
        "nome_sacado": pagamento.nome_sacado or None,
        "documento_sacado": pagamento.documento_sacado or None,
        "endereco_sacado": pagamento.endereco_sacado or None,
        "bairro_sacado": pagamento.bairro_sacado or None,
        "cidade_sacado": pagamento.cidade_sacado or None,
        "uf_sacado": pagamento.uf_sacado or None,
        "cep_sacado": pagamento.cep_sacado or None,
        "encargos": _encargos_para_api(pagamento),
    }
    return _sem_nulos(dados)


def remessa_para_api(remessa) -> dict[str, Any]:
    """Serializa uma remessa (``RemessaCnab400Base``/``RemessaCnab240Base``) para
    o schema ``RemessaRequest``."""

    def opt(attr: str) -> str | None:
        valor = getattr(remessa, attr, "") or ""
        return valor or None

    sequencial = getattr(remessa, "sequencial_remessa", None)
    sequencial_texto = "" if sequencial is None else str(sequencial)
    sequencial_int = int(sequencial_texto) if sequencial_texto.isdigit() else None

    dados: dict[str, Any] = {
        "empresa_mae": remessa.empresa_mae,
        "documento_cedente": remessa.documento_cedente,
        "agencia": remessa.agencia,
        "conta_corrente": remessa.conta_corrente,
        "digito_conta": opt("digito_conta"),
        "convenio": opt("convenio"),
        "carteira": opt("carteira"),
        "variacao_carteira": opt("variacao_carteira"),
        "codigo_beneficiario": opt("codigo_beneficiario"),
        "sequencial_remessa": sequencial_int,
        "pagamentos": [pagamento_para_api(p) for p in remessa.pagamentos],
    }
    return _sem_nulos(dados)


def _valor_centavos(bruto: str | None) -> float | None:
    if not bruto:
        return None
    digitos = "".join(c for c in str(bruto) if c.isdigit())
    return int(digitos) / 100 if digitos else None


def retorno_item_para_api(
    registro, layout: str = "400", banco: str | None = None
) -> dict[str, Any]:
    """Serializa um :class:`~pycobranca.cnab.retorno.RegistroRetorno` para o
    schema ``RetornoItem`` (visão curada do retorno da API).

    Os valores monetários crus (centavos) viram ``float`` em reais e
    ``motivo_ocorrencia`` vira o rótulo legível da ocorrência.

    **Informe ``banco``** — é o ``codigo_banco`` do :class:`Retorno` que trouxe o
    registro. Há banco que redefine códigos do CNAB 400, e o sentido se inverte:
    o ``40`` do Safra é *baixa de título protestado*, e no mapa padrão da FEBRABAN
    é *baixa por ter sido liquidado*. Sem o banco, a API descreve um título
    protestado como pago — e o rótulo continua plausível, então o erro atravessa a
    conciliação sem nenhum sinal. Omitir só é seguro num retorno de banco que não
    redefine nada, e quem lê o payload não tem como saber se é o caso.
    """
    from ..cnab.retorno.ocorrencias import descreve_ocorrencia

    dados = {
        "nosso_numero": registro.nosso_numero or None,
        "numero_documento": registro.documento_numero or None,
        "data_credito": registro.data_credito or None,
        "data_ocorrencia": registro.data_ocorrencia or None,
        "valor_titulo": _valor_centavos(registro.valor_titulo),
        "valor_pago": _valor_centavos(registro.valor_recebido),
        "valor_tarifa": _valor_centavos(registro.valor_tarifa),
        "codigo_ocorrencia": registro.codigo_ocorrencia or None,
        "motivo_ocorrencia": descreve_ocorrencia(registro.codigo_ocorrencia, layout, banco),
    }
    return _sem_nulos(dados)


# --------------------------------------------------------------------------- #
# Validador de contrato (subconjunto de JSON Schema suficiente para os schemas)
# --------------------------------------------------------------------------- #
_TIPOS = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "array": list,
    "object": dict,
    "boolean": bool,
}


def valida_contrato(dados: dict, schema_nome: str) -> None:
    """Valida ``dados`` contra o schema ``schema_nome`` do contrato.

    Verifica campos obrigatórios, tipos declarados, ``enum`` e itens de array
    (via ``$ref``). Levanta :class:`ErroDeContrato` na primeira violação.
    Campos extras são permitidos (``additionalProperties`` implícito).
    """
    schema = CONTRATO["schemas"].get(schema_nome)
    if schema is None:
        raise ErroDeContrato(f"schema desconhecido: {schema_nome!r}")
    if not isinstance(dados, dict):
        raise ErroDeContrato(f"{schema_nome}: esperado objeto, recebido {type(dados).__name__}")

    for obrigatorio in schema.get("required", []):
        if dados.get(obrigatorio) in (None, ""):
            raise ErroDeContrato(f"{schema_nome}: campo obrigatório ausente/vazio: {obrigatorio!r}")

    propriedades = schema.get("properties", {})
    for chave, valor in dados.items():
        regra = propriedades.get(chave)
        if regra is None:
            continue  # additionalProperties permitido
        if valor is None:
            continue  # campo opcional nulo (ex.: OFX preserva null por paridade)
        tipo = regra.get("type")
        if tipo == "array":
            if not isinstance(valor, list):
                raise ErroDeContrato(f"{schema_nome}.{chave}: esperado array")
            ref = regra.get("items", {}).get("$ref")
            if ref:
                for item in valor:
                    valida_contrato(item, ref)
            continue
        esperado = _TIPOS.get(tipo)
        # `bool` é subclasse de `int` em Python, então `True` passaria por
        # `number`/`integer` e chegaria à engine como valor monetário — onde
        # `Decimal("True")` levanta InvalidOperation, fora da hierarquia de erros.
        if tipo in ("number", "integer") and isinstance(valor, bool):
            raise ErroDeContrato(f"{schema_nome}.{chave}: esperado {tipo}, recebido bool")
        if esperado and not isinstance(valor, esperado):
            raise ErroDeContrato(
                f"{schema_nome}.{chave}: esperado {tipo}, recebido {type(valor).__name__}"
            )
        if "enum" in regra and valor not in regra["enum"]:
            raise ErroDeContrato(f"{schema_nome}.{chave}: valor {valor!r} fora do enum")
        padrao = regra.get("pattern")
        if padrao and isinstance(valor, str) and not re.fullmatch(padrao, valor):
            raise ErroDeContrato(
                f"{schema_nome}.{chave}: valor {valor!r} não casa com o padrão {padrao!r}"
            )


def openapi_de(
    paths: dict[str, Any],
    *,
    info: dict[str, Any] | None = None,
    servers: list[dict[str, Any]] | None = None,
    schemas: dict[str, Any] | None = None,
    versao: str = "3.0.3",
) -> dict[str, Any]:
    """Monta um documento OpenAPI com **os seus paths** e **os schemas daqui**.

    A PyCobrança é biblioteca e não tem endpoints: publicar um OpenAPI completo
    aqui exigiria inventar rotas que ela não serve. Quem tem paths é a sua API —
    e quem tem os schemas de dados é esta biblioteca, que os versiona junto com
    o código que os implementa.

    Este helper cola os dois lados sem que ninguém precise copiar schema, que é
    onde a divergência começa: um arquivo copiado envelhece em silêncio quando a
    biblioteca sobe de versão.

    Args:
        paths: o bloco ``paths`` da sua API, no formato OpenAPI. Use
            ``{"$ref": "#/components/schemas/BoletoData"}`` para apontar aos
            schemas daqui.
        info: bloco ``info``. O título e a versão são seus; a **versão da
            PyCobrança é carimbada** em ``x-pycobranca`` e na ``description``,
            para quem lê o Swagger saber de qual engine veio o contrato.
        servers: bloco ``servers``, opcional.
        schemas: schemas seus, somados aos da biblioteca. **Colidir com um nome
            existente levanta** ``ErroDeContrato`` — sobrescrever ``BoletoData``
            em silêncio devolveria o problema que este helper evita.
        versao: versão do OpenAPI declarada no documento.

    :returns: ``dict`` pronto para virar JSON ou YAML. Os schemas são **copiados**,
        então mutar o resultado não afeta :data:`CONTRATO`.

    Exemplo::

        from pycobranca.contracts import openapi_de

        doc = openapi_de(
            {"/boletos": {"post": {...}}},
            info={"title": "cobranca_api", "version": "1.0.0"},
            servers=[{"url": "https://api.exemplo.com.br"}],
        )
        yaml.safe_dump(doc, sort_keys=False)  # sirva no Swagger UI
    """
    from .. import __version__

    do_pacote = copy.deepcopy(CONTRATO["schemas"])
    if schemas:
        colisoes = sorted(set(schemas) & set(do_pacote))
        if colisoes:
            raise ErroDeContrato(
                "schemas colidem com os da PyCobrança (renomeie os seus): " + ", ".join(colisoes)
            )
        do_pacote.update(copy.deepcopy(schemas))

    bloco_info: dict[str, Any] = dict(info or {})
    bloco_info.setdefault("title", "API de cobrança")
    bloco_info.setdefault("version", "1.0.0")
    bloco_info["x-pycobranca"] = __version__
    origem = f"Schemas de dados da PyCobrança {__version__}."
    bloco_info["description"] = (
        f"{bloco_info['description']}\n\n{origem}" if bloco_info.get("description") else origem
    )

    documento: dict[str, Any] = {"openapi": versao, "info": bloco_info}
    if servers:
        documento["servers"] = list(servers)
    documento["paths"] = paths
    documento["components"] = {"schemas": do_pacote}
    return documento
