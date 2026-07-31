"""Hook do MkDocs: corrige os links relativos escritos para o GitHub.

A documentação é escrita para ser lida **também** no GitHub, então usa links
relativos como ``../pycobranca/render/tela.py``. No site publicado esses
caminhos não existem — este hook reescreve:

- links que saem de ``docs/`` (código-fonte, ``pyproject.toml``, ``tests/``)
  para a URL do arquivo no repositório;
- links que continuam dentro de ``docs/`` para o caminho relativo correto a
  partir da página, deixando o MkDocs resolvê-los normalmente — inclusive os
  ``docs/...`` do CHANGELOG, que é copiado para dentro da documentação.
"""

from __future__ import annotations

import posixpath
import re

REPO = "https://github.com/Maxwbh/pyCobranca/blob/main/"

#: links markdown relativos: ``](../algo)`` (sobem de diretório) e ``](docs/algo)``
_PADRAO = re.compile(r"\]\(((?:\.\./|docs/)[^)\s]+?)(#[^)\s]*)?\)")


def on_page_markdown(markdown: str, page, config, files) -> str:
    base = posixpath.dirname(page.file.src_uri)  # "" para docs/x.md, "bancos" para docs/bancos/y.md

    def troca(casamento: re.Match[str]) -> str:
        alvo, ancora = casamento.group(1), casamento.group(2) or ""
        # `docs/...` só aparece em arquivos escritos para a raiz do repositório
        # (CHANGELOG); os demais são relativos à própria página.
        partida = "" if alvo.startswith("docs/") else posixpath.join("docs", base)
        destino = posixpath.normpath(posixpath.join(partida, alvo))
        if destino.startswith("docs/"):
            # continua dentro da documentação: refaz o caminho relativo à página
            relativo = posixpath.relpath(destino[len("docs/") :], base or ".")
            return f"]({relativo}{ancora})"
        return f"]({REPO}{destino}{ancora})"

    return _PADRAO.sub(troca, markdown)
