"""Dígitos verificadores usados na cobrança bancária (FEBRABAN).

- :func:`modulo10`: usado nos três campos da linha digitável e em DACs de
  agência/conta/nosso número de vários bancos (ex.: Itaú).
- :func:`modulo11_codigo_barras`: DV geral do código de barras (posição 5),
  com a regra FEBRABAN de colapsar 0/10/11 em 1.
"""

from __future__ import annotations

from ..exceptions import DadosInvalidos

__all__ = [
    "modulo10",
    "modulo11_codigo_barras",
    "modulo11_resto",
    "modulo11_flex",
    "duplo_digito",
]


def _apenas_digitos(sequencia: str) -> str:
    seq = "".join(ch for ch in str(sequencia) if ch.isdigit())
    if not seq:
        raise DadosInvalidos(f"sequência sem dígitos: {sequencia!r}")
    return seq


def modulo10(sequencia: str) -> int:
    """DV módulo 10 (pesos 2,1,2,1… da direita para a esquerda).

    Produtos maiores que 9 têm seus algarismos somados (equivalente a
    ``produto - 9``). DV = ``(10 - soma % 10) % 10``.
    """
    seq = _apenas_digitos(sequencia)
    soma = 0
    peso = 2
    for ch in reversed(seq):
        produto = int(ch) * peso
        soma += produto - 9 if produto > 9 else produto
        peso = 1 if peso == 2 else 2
    return (10 - soma % 10) % 10


def modulo11_resto(sequencia: str, *, peso_max: int = 9) -> int:
    """Resto da divisão por 11 com pesos cíclicos 2..``peso_max`` (direita→esquerda).

    Cada banco aplica sua própria regra de mapeamento sobre este resto (ex.:
    Bradesco usa base 7 e mapeia resto 1→"P"; Santander/Caixa usam base 9 e
    colapsam DV>9 em 0). Ver os módulos em :mod:`pycobranca.bancos`.
    """
    seq = _apenas_digitos(sequencia)
    soma = 0
    peso = 2
    for ch in reversed(seq):
        soma += int(ch) * peso
        peso = 2 if peso == peso_max else peso + 1
    return soma % 11


def modulo11_codigo_barras(sequencia: str) -> int:
    """DV módulo 11 do código de barras (pesos 2..9 cíclicos, direita→esquerda).

    Regra FEBRABAN: DV = ``11 - (soma % 11)``; resultados 0, 10 e 11 viram 1.
    Aplica-se às 43 posições do código de barras (sem o próprio DV).
    """
    seq = _apenas_digitos(sequencia)
    soma = 0
    peso = 2
    for ch in reversed(seq):
        soma += int(ch) * peso
        peso = 2 if peso == 9 else peso + 1
    dv = 11 - (soma % 11)
    return 1 if dv in (0, 10, 11) else dv


def modulo11_flex(
    sequencia: str,
    *,
    fatores: tuple[int, ...] = (9, 8, 7, 6, 5, 4, 3, 2),
    da_direita: bool = True,
    bloco=None,
    mapa: dict | None = None,
):
    """Módulo 11 com fatores e mapeamento configuráveis.

    Multiplica os dígitos pelos ``fatores`` (cíclicos), da direita para a
    esquerda por padrão (``da_direita=False`` = esquerda→direita). Sem
    ``bloco``, o valor é
    ``soma % 11``; com ``bloco``, é ``bloco(soma)``. O ``mapa`` traduz o
    valor final (ex.: ``{10: 0, 11: 0}`` ou ``{10: "X"}``).
    """
    seq = _apenas_digitos(sequencia)
    digitos = reversed(seq) if da_direita else iter(seq)
    soma = 0
    for i, ch in enumerate(digitos):
        soma += int(ch) * fatores[i % len(fatores)]
    valor = bloco(soma) if bloco else soma % 11
    mapa = mapa or {}
    return mapa.get(valor, valor)


def duplo_digito(sequencia: str) -> str:
    """Dígito duplo (módulo 10 + módulo 11) — Banrisul/Banestes/BRB.

    O segundo dígito usa
    módulo 11 com fatores 2..7 e, quando o resultado é 1, incrementa o
    primeiro dígito (9→0) e recalcula.
    """
    seq = _apenas_digitos(sequencia)

    def _digito2(seq_com_d1: str) -> int:
        return modulo11_flex(
            seq_com_d1,
            fatores=(2, 3, 4, 5, 6, 7),
            bloco=lambda total: total if total < 11 else total % 11,
        )

    d1 = modulo10(seq)
    d2 = _digito2(f"{seq}{d1}")
    while d2 == 1:
        d1 = 0 if d1 == 9 else d1 + 1
        d2 = _digito2(f"{seq}{d1}")
    if d2 != 0:
        d2 = 11 - d2
    return f"{d1}{d2}"
