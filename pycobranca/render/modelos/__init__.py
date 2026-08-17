"""Catálogo dos documentos renderizáveis — um módulo por modelo.

Modelos disponíveis:

- :mod:`~pycobranca.render.modelos.boleto_classico` — Boleto Clássico.
- :mod:`~pycobranca.render.modelos.boleto_moderno` — Boleto Moderno (chips, faixa de marca, PIX).
- :mod:`~pycobranca.render.modelos.carne` — Carnê (3 parcelas por A4).
- :mod:`~pycobranca.render.modelos.fatura` — Fatura (demonstrativo de itens + boleto).

**Contrato de um modelo de boleto** (para registrar um novo):

1. crie ``modelos/<nome>.py`` expondo

   - ``MODERNO: bool`` — paleta usada pela :class:`~pycobranca.render.tela.Tela`
     (``True`` = cinza/teal, ``False`` = bordas pretas);
   - ``desenha(tela, info, contexto) -> None`` — desenha a página inteira, na
     ordem desejada, com os blocos de :mod:`pycobranca.render.blocos` e os do
     próprio modelo;

2. registre-o em :data:`MODELOS_BOLETO` abaixo.

Nada mais precisa mudar: :func:`pycobranca.render.desenha_boleto` despacha pelo
registro e :func:`pycobranca.render.render_boleto_pdf` cuida do canvas.
"""

from __future__ import annotations

from types import ModuleType

from . import boleto_classico, boleto_moderno, fatura
from .carne import render_carne_pdf

#: registro dos modelos de boleto aceitos por ``modelo=`` nas funções públicas
MODELOS_BOLETO: dict[str, ModuleType] = {
    "classico": boleto_classico,
    "moderno": boleto_moderno,
}

#: modelo da fatura (boleto + demonstrativo de itens)
MODELO_FATURA: ModuleType = fatura

__all__ = ["MODELOS_BOLETO", "MODELO_FATURA", "modelo_boleto", "render_carne_pdf"]


def modelo_boleto(nome: str) -> ModuleType:
    """Devolve o módulo do modelo de boleto ``nome``.

    Raises:
        ValueError: se o modelo não estiver registrado em :data:`MODELOS_BOLETO`.
    """
    try:
        return MODELOS_BOLETO[nome]
    except KeyError:
        raise ValueError(f"modelo inválido: {nome!r} (use 'classico' ou 'moderno')") from None
