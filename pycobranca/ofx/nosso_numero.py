"""Extração do nosso número do campo ``memo`` de uma transação OFX.

O banco é identificado pelo ORG/FID do arquivo OFX; cada banco tem um padrão
típico de dígitos no histórico (memo). Sem correspondência de banco, usa um
padrão genérico.
"""

from __future__ import annotations

import re

__all__ = ["extrair_nosso_numero"]

#: (regex do identificador do banco, regex do nosso número no memo). Ordem importa.
_PADROES: tuple[tuple[re.Pattern[str], re.Pattern[str]], ...] = (
    (re.compile(r"sicoob|756", re.I), re.compile(r"(\d{7,12})")),
    (re.compile(r"itau|ita|341", re.I), re.compile(r"(\d{8})")),
    (re.compile(r"brasil|001", re.I), re.compile(r"(\d{10,17})")),
    (re.compile(r"bradesco|237", re.I), re.compile(r"(\d{11})")),
    (re.compile(r"caixa|104", re.I), re.compile(r"(\d{14,17})")),
)
_GENERICO = re.compile(r"(\d{7,17})")


def extrair_nosso_numero(memo: str | None, banco_org: str | None) -> str | None:
    """Retorna o nosso número extraído do ``memo`` ou ``None``.

    :param memo: campo ``MEMO`` da transação OFX.
    :param banco_org: identificador do banco (ORG ou FID do OFX).
    """
    if not memo or not memo.strip():
        return None
    ident = str(banco_org or "")
    for id_re, num_re in _PADROES:
        if id_re.search(ident):
            m = num_re.search(memo)
            return m.group(1) if m else None
    m = _GENERICO.search(memo)
    return m.group(1) if m else None
