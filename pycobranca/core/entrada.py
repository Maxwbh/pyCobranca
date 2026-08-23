"""Tipo da entrada dos leitores de arquivo (retorno CNAB e extrato OFX).

Os dois aceitam a mesma coisa — caminho, ``bytes`` ou um objeto com ``.read()``,
que é o que chega de um upload HTTP sem passar por arquivo temporário. O alias
existe para que a anotação diga isso ao verificador de tipos: o pacote distribui
``py.typed``, e uma anotação estreita demais faz o consumidor ver erro num uso
que funciona.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = ["FonteDeArquivo", "Legivel"]


@runtime_checkable
class Legivel(Protocol):
    """Qualquer objeto com ``.read()`` — arquivo aberto, ``BytesIO``, upload."""

    def read(self) -> bytes | str: ...


#: caminho, conteúdo em bytes ou objeto legível
FonteDeArquivo = str | Path | bytes | bytearray | Legivel
