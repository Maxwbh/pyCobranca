"""Fatura — corpo livre + boleto na mesma página.

A fatura desenha um **corpo** no topo da página e, logo abaixo, o **boleto**
completo (modelo moderno ou clássico). O corpo aceita três níveis de liberdade,
do mais simples ao mais aberto — todos em Python puro, sem engine de HTML:

**1. ``itens``** — a tabela pronta (o caso comum)::

    contexto["itens"] = [
        {"descricao": "Mensalidade — agosto/2026", "quantidade": 1, "valor": 99.90},
        {"descricao": "Serviço adicional", "quantidade": 2, "valor_unitario": 13.80},
    ]

**2. ``fatura.blocos``** — corpo declarativo, para qualquer modalidade
(mensalidade, condomínio, consumo, escola, serviços)::

    contexto["fatura"] = {
        "titulo": "Fatura de Serviços",
        "blocos": [
            {"tipo": "campos", "itens": [("Período", "01/08 a 31/08"), ("Contrato", "4471")]},
            {"tipo": "tabela", "colunas": ["Descrição", "Qtd.", "Unitário", "Total"],
             "linhas": [["Consumo", "18", "3,50", "63,00"]], "alinhamento": "llrr"},
            {"tipo": "texto", "conteudo": "Leitura em <b>18/08</b>."},
            {"tipo": "total", "rotulo": "Total da fatura", "valor": 127.50},
        ],
    }

Blocos disponíveis: ``campos``, ``tabela``, ``texto``, ``total``, ``separador``
e ``espaco``. O bloco ``texto`` aceita a marcação inline do ReportLab
(``<b>``, ``<i>``, ``<font color="#...">``, ``<br/>``) — mini-HTML sem
dependência nova.

**3. ``fatura.desenhar``** — liberdade total: um ``callable(tela, info)`` que
desenha o que quiser usando a :class:`~pycobranca.render.tela.Tela`; o boleto é
composto abaixo::

    contexto["fatura"] = {"desenhar": lambda tela, info: minha_arte(tela, info)}

Precedência: ``desenhar`` > ``blocos`` > ``itens``. Sem nenhum dos três, a saída
é o boleto puro.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from ..comum import _LARGURA

__all__ = [
    "MODERNO",
    "desenha",
    "desenha_corpo",
    "cabecalho_fatura",
    "tabela_itens",
    "normaliza_itens",
    "BLOCOS",
]

#: paleta usada quando a fatura é montada sem um modelo de boleto explícito
MODERNO = True

#: colunas da tabela de ``itens``: (rótulo, largura em mm, alinhado à direita)
_COLUNAS: list[tuple[str, float, bool]] = [
    ("Descrição", 110.0, False),
    ("Qtd.", 18.0, True),
    ("Valor unitário", 28.0, True),
    ("Total", 34.0, True),
]

_ALTURA_LINHA = 6.0
_ALTURA_CABECALHO = 7.0


def _dec(valor: Any) -> Decimal:
    """Converte para ``Decimal`` aceitando ``str`` no formato brasileiro."""
    if valor is None or valor == "":
        return Decimal("0")
    if isinstance(valor, str):
        valor = valor.strip().replace("R$", "").replace(".", "").replace(",", ".")
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return Decimal("0")


def _moeda(valor: Decimal) -> str:
    """Formata no padrão brasileiro (1.234,56)."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normaliza_itens(itens: list[dict[str, Any]] | None) -> tuple[list[dict[str, Any]], Decimal]:
    """Normaliza os itens do contexto e devolve ``(itens, total)``.

    Cada item resultante tem ``descricao``, ``quantidade``, ``valor_unitario`` e
    ``total`` já calculados: quando só há ``valor``, ele é o total da linha;
    quando há ``valor_unitario``, o total é ``quantidade * valor_unitario``.
    """
    normalizados: list[dict[str, Any]] = []
    total = Decimal("0")
    for item in itens or []:
        quantidade = _dec(item.get("quantidade", 1)) or Decimal("1")
        if item.get("valor_unitario") not in (None, ""):
            unitario = _dec(item["valor_unitario"])
            linha = quantidade * unitario
        else:
            linha = _dec(item.get("valor"))
            unitario = linha / quantidade if quantidade else linha
        total += linha
        normalizados.append(
            {
                "descricao": str(item.get("descricao", "")),
                "quantidade": quantidade,
                "valor_unitario": unitario,
                "total": linha,
            }
        )
    return normalizados, total


# ---------------------------------------------------------------- cabeçalho --


def cabecalho_fatura(tela, info, titulo: str = "FATURA") -> None:
    """Título da fatura e identificação do beneficiário."""
    canvas, mm, x_ = tela.canvas, tela.mm, tela.x_
    y_topo = tela.y_()
    tela.texto(x_(0), y_topo - 5.0 * mm, titulo, fonte="Helvetica-Bold", tam=13, cor=tela.marca)
    tela.texto(
        0,
        y_topo - 5.0 * mm,
        f"Vencimento {info.vencimento}",
        fonte="Helvetica-Bold",
        tam=10,
        dir_x=x_(_LARGURA),
    )
    tela.texto(x_(0), y_topo - 10.4 * mm, info.beneficiario_nome, fonte="Helvetica-Bold", tam=9)
    partes = [p for p in (info.beneficiario_documento, info.beneficiario_endereco) if p]
    rodape = " · ".join(partes)
    if rodape:
        tela.texto(x_(0), y_topo - 14.6 * mm, rodape, tam=7.5, cor=tela.rotulo)
    canvas.setStrokeColor(tela.borda)
    canvas.setLineWidth(0.5)
    canvas.line(x_(0), y_topo - 17.6 * mm, x_(_LARGURA), y_topo - 17.6 * mm)
    tela.avanca(21.0)


# -------------------------------------------------------- blocos declarativos --


def _larguras(colunas: list[str], larguras: list[float] | None) -> list[float]:
    """Larguras em mm: as informadas ou uma divisão que privilegia a 1ª coluna."""
    if larguras:
        return [float(w) for w in larguras]
    if len(colunas) == 1:
        return [_LARGURA]
    resto = 30.0
    primeira = _LARGURA - resto * (len(colunas) - 1)
    return [primeira] + [resto] * (len(colunas) - 1)


def bloco_tabela(tela, bloco: dict[str, Any]) -> None:
    """Tabela genérica: ``colunas``, ``linhas`` e ``alinhamento`` (``l``/``r`` por coluna)."""
    canvas, mm, x_ = tela.canvas, tela.mm, tela.x_
    colunas = [str(c) for c in bloco.get("colunas") or []]
    linhas = bloco.get("linhas") or []
    larguras = _larguras(colunas, bloco.get("larguras"))
    alinhamento = str(bloco.get("alinhamento") or "").ljust(len(colunas), "l")

    if colunas:
        y_topo = tela.y_()
        if tela.moderno:
            canvas.setFillColor(tela.destaque_bg)
            canvas.rect(
                x_(0),
                y_topo - _ALTURA_CABECALHO * mm,
                _LARGURA * mm,
                _ALTURA_CABECALHO * mm,
                stroke=0,
                fill=1,
            )
        canvas.setStrokeColor(tela.borda)
        canvas.setLineWidth(0.5)
        canvas.rect(
            x_(0),
            y_topo - _ALTURA_CABECALHO * mm,
            _LARGURA * mm,
            _ALTURA_CABECALHO * mm,
            stroke=1,
            fill=0,
        )
        x = 0.0
        for i, rotulo in enumerate(colunas):
            y_rot = y_topo - 4.8 * mm
            if alinhamento[i] == "r":
                tela.texto(
                    0,
                    y_rot,
                    tela.rot_fmt(rotulo),
                    tam=6.5,
                    cor=tela.rotulo,
                    dir_x=x_(x + larguras[i] - 1.5),
                )
            else:
                tela.texto(x_(x + 1.5), y_rot, tela.rot_fmt(rotulo), tam=6.5, cor=tela.rotulo)
            x += larguras[i]
        tela.avanca(_ALTURA_CABECALHO)

    for linha in linhas:
        y_linha = tela.y_()
        canvas.setStrokeColor(tela.borda)
        canvas.setLineWidth(0.3)
        canvas.line(x_(0), y_linha - _ALTURA_LINHA * mm, x_(_LARGURA), y_linha - _ALTURA_LINHA * mm)
        x = 0.0
        for i, valor in enumerate(linha[: len(larguras)]):
            y_val = y_linha - 4.2 * mm
            if alinhamento[i] == "r":
                tela.texto(0, y_val, str(valor), tam=8, dir_x=x_(x + larguras[i] - 1.5))
            else:
                tela.texto(x_(x + 1.5), y_val, str(valor), tam=8)
            x += larguras[i]
        tela.avanca(_ALTURA_LINHA)


def bloco_campos(tela, bloco: dict[str, Any]) -> None:
    """Pares rótulo/valor em colunas (``itens`` = lista de ``(rótulo, valor)``)."""
    itens = list(bloco.get("itens") or [])
    if not itens:
        return
    mm = tela.mm
    por_linha = int(bloco.get("colunas") or 3)
    largura = _LARGURA / por_linha
    for inicio in range(0, len(itens), por_linha):
        faixa = itens[inicio : inicio + por_linha]
        y_topo = tela.y_()
        for i, par in enumerate(faixa):
            rotulo, valor = (par if isinstance(par, (list, tuple)) else (par, ""))[:2]
            x = i * largura
            tela.texto(
                tela.x_(x), y_topo - 3.0 * mm, tela.rot_fmt(str(rotulo)), tam=6.5, cor=tela.rotulo
            )
            tela.texto(tela.x_(x), y_topo - 7.4 * mm, str(valor), tam=8.5)
        tela.avanca(10.0)


def bloco_texto(tela, bloco: dict[str, Any]) -> None:
    """Texto livre com marcação inline do ReportLab (``<b>``, ``<i>``, ``<font>``, ``<br/>``)."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    conteudo = str(bloco.get("conteudo") or "")
    if not conteudo:
        return
    tam = float(bloco.get("tamanho") or 8.5)
    estilo = ParagraphStyle(
        "fatura-texto", fontName="Helvetica", fontSize=tam, leading=tam * 1.35, textColor=tela.black
    )
    paragrafo = Paragraph(conteudo, estilo)
    largura_pt = _LARGURA * tela.mm
    _w, altura_pt = paragrafo.wrap(largura_pt, 1000)
    altura_mm = altura_pt / tela.mm
    tela.avanca(2.0)  # respiro em relação ao bloco anterior
    paragrafo.drawOn(tela.canvas, tela.x_(0), tela.y_() - altura_pt)
    tela.avanca(altura_mm + 2.0)


def bloco_total(tela, bloco: dict[str, Any]) -> None:
    """Linha de total (rótulo à esquerda do valor, ambos em negrito)."""
    mm, x_ = tela.mm, tela.x_
    y = tela.y_()
    rotulo = str(bloco.get("rotulo") or "Total")
    tela.texto(0, y - 5.0 * mm, rotulo, fonte="Helvetica-Bold", tam=9, dir_x=x_(_LARGURA - 36.0))
    tela.texto(
        0,
        y - 5.0 * mm,
        _moeda(_dec(bloco.get("valor"))),
        fonte="Helvetica-Bold",
        tam=10,
        dir_x=x_(_LARGURA - 1.5),
    )
    tela.avanca(9.0)


def bloco_separador(tela, bloco: dict[str, Any]) -> None:
    """Linha horizontal fina."""
    tela.avanca(1.5)
    tela.canvas.setStrokeColor(tela.borda)
    tela.canvas.setLineWidth(0.5)
    tela.canvas.line(tela.x_(0), tela.y_(), tela.x_(_LARGURA), tela.y_())
    tela.avanca(2.5)


def bloco_espaco(tela, bloco: dict[str, Any]) -> None:
    """Espaço vertical em mm (``altura``, padrão 4)."""
    tela.avanca(float(bloco.get("altura") or 4.0))


#: blocos aceitos em ``contexto["fatura"]["blocos"]``
BLOCOS = {
    "tabela": bloco_tabela,
    "campos": bloco_campos,
    "texto": bloco_texto,
    "total": bloco_total,
    "separador": bloco_separador,
    "espaco": bloco_espaco,
}


# ------------------------------------------------------------------- corpos --


def tabela_itens(tela, itens: list[dict[str, Any]], total: Decimal) -> None:
    """Tabela do nível 1 (``itens``), com a linha de total ao final."""
    bloco_tabela(
        tela,
        {
            "colunas": [c for c, _w, _d in _COLUNAS],
            "larguras": [w for _c, w, _d in _COLUNAS],
            "alinhamento": "".join("r" if d else "l" for _c, _w, d in _COLUNAS),
            "linhas": [
                [
                    item["descricao"],
                    f"{item['quantidade']:g}".replace(".", ","),
                    _moeda(item["valor_unitario"]),
                    _moeda(item["total"]),
                ]
                for item in itens
            ],
        },
    )
    bloco_total(tela, {"rotulo": "Total da fatura", "valor": total})


def desenha_corpo(tela, info, contexto) -> bool:
    """Desenha o corpo da fatura. Devolve ``True`` se algo foi desenhado.

    Precedência: ``fatura.desenhar`` (callable) > ``fatura.blocos`` > ``itens``.
    """
    fatura = contexto.get("fatura") or {}

    # nível 3 — liberdade total
    desenhar = fatura.get("desenhar")
    if callable(desenhar):
        desenhar(tela, info)
        return True

    # nível 2 — blocos declarativos
    blocos = fatura.get("blocos")
    if blocos:
        cabecalho_fatura(tela, info, str(fatura.get("titulo") or "FATURA"))
        for bloco in blocos:
            tipo = str(bloco.get("tipo") or "").lower()
            desenhador = BLOCOS.get(tipo)
            if desenhador is None:
                raise ValueError(
                    f"bloco de fatura inválido: {tipo!r} (use um de: {', '.join(sorted(BLOCOS))})"
                )
            desenhador(tela, bloco)
        return True

    # nível 1 — itens
    itens, total = normaliza_itens(contexto.get("itens"))
    if itens:
        cabecalho_fatura(tela, info, str(fatura.get("titulo") or "FATURA"))
        tabela_itens(tela, itens, total)
        return True
    return False


def desenha(tela, info, contexto) -> None:
    """Página da fatura: corpo (livre) + boleto do modelo escolhido."""
    from . import modelo_boleto

    desenha_corpo(tela, info, contexto)
    modelo_boleto("moderno" if tela.moderno else "classico").desenha(tela, info, contexto)
