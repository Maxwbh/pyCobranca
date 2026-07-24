"""Logos de bancos empacotados — conveniência opcional para o logo do boleto.

Os arquivos em ``pycobranca/render/logos/NNN.png`` (nomeados pelo código FEBRABAN)
alimentam a capacidade **opt-in** de logo do cabeçalho (ver ``banco.logo`` em
:mod:`pycobranca.render.reportlab`). São um atalho — o boleto continua aceitando
qualquer logo fornecido pelo chamador.

**Marcas registradas.** As imagens são de propriedade dos respectivos bancos e
aqui aparecem apenas para identificar o emissor no boleto. Origem dos arquivos e
atribuição em ``pycobranca/render/logos/NOTICE.md``. Use-as apenas quando você
tiver o direito de exibir a marca (p.ex. cobrança legítima pela instituição).
"""

from __future__ import annotations

from importlib.resources import files

__all__ = ["logo_do_banco", "bancos_com_logo"]

_DIR = "logos"


def _normaliza(codigo: str | int) -> str:
    """Normaliza o código do banco para 3 dígitos (aceita ``33``, ``"33"``, ``"033"``)."""
    return str(codigo).strip().zfill(3)


def logo_do_banco(codigo: str | int) -> bytes | None:
    """Retorna os bytes do logo empacotado do banco, ou ``None`` se não houver.

    Args:
        codigo: código FEBRABAN do banco (``"237"``, ``237`` ou ``"33"``).

    Returns:
        Bytes do PNG prontos para ``banco.logo``, ou ``None`` quando o banco não
        tem logo empacotado.

    Example:
        >>> from pycobranca.render import logo_do_banco, render_boleto_pdf
        >>> ctx = boleto.contexto_render()
        >>> ctx["banco"]["logo"] = logo_do_banco("237")
        >>> pdf = render_boleto_pdf(ctx)
    """
    recurso = files(__package__).joinpath(_DIR, f"{_normaliza(codigo)}.png")
    if not recurso.is_file():
        return None
    return recurso.read_bytes()


def bancos_com_logo() -> tuple[str, ...]:
    """Códigos FEBRABAN (3 dígitos) que têm logo empacotado, em ordem."""
    raiz = files(__package__).joinpath(_DIR)
    return tuple(sorted(p.name[:-4] for p in raiz.iterdir() if p.name.endswith(".png")))
