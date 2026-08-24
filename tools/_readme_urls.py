"""Converte os caminhos relativos do README nas URLs absolutas que o PyPI exige.

O README serve a dois destinos com exigências **opostas**:

- **no GitHub**, ele é lido dentro de uma branch. Caminho relativo resolve contra
  o commit atual, então a imagem aparece em qualquer branch — inclusive antes de
  a mudança chegar à ``main``, que é quando se quer olhar para ela.
- **no PyPI**, ele é o ``long_description``. A página é renderizada **fora do
  contexto do repositório**: não há branch nem árvore de arquivos. Caminho
  relativo não resolve, e as imagens simplesmente somem.

Fixar tudo em ``.../main/...`` atende o PyPI e quebra o primeiro caso: a captura
só aparece depois de promovida, que é tarde para validar. Fixar em relativo
atende o primeiro e apaga as imagens da página do pacote.

O acordo é converter **no empacotamento**: o arquivo fica relativo no
repositório, e ``_backend_readme`` aplica isto ao construir o sdist e o wheel.

Este módulo é texto puro de propósito — não importa ``setuptools``, para que a
suíte de testes possa cobri-lo sem depender do ambiente de build.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from pathlib import Path

#: Ref do repositório para onde as URLs absolutas apontam.
#:
#: ``main`` mantém o comportamento que a página do PyPI já tinha. Trocar por uma
#: tag (``v1.1.1``) congela os assets da versão publicada, ao custo de a tag
#: precisar existir antes de a página ser renderizada.
REF = "main"

RAW = f"https://raw.githubusercontent.com/Maxwbh/pyCobranca/{REF}"
BLOB = f"https://github.com/Maxwbh/pyCobranca/blob/{REF}"
TREE = f"https://github.com/Maxwbh/pyCobranca/tree/{REF}"

#: ``<img src="...">`` e ``[texto](...)`` / ``![texto](...)``.
IMG_HTML = re.compile(r'(<img\s[^>]*?\bsrc=")([^"]+)(")', re.IGNORECASE)
MARKDOWN = re.compile(r"(!?)(\[[^\]]*\]\()([^)\s]+)(\))")

#: Esquemas e âncoras que não são caminho do repositório.
NAO_E_CAMINHO = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.IGNORECASE)


def _absoluta(alvo: str, raiz: Path, *, imagem: bool) -> str:
    """Converte um caminho relativo do repositório na URL absoluta equivalente.

    Imagem vai para ``raw`` — por ``blob`` o GitHub devolve página HTML, não os
    bytes, e o ``<img>`` quebra. Link para diretório vai para ``tree``; para
    arquivo, ``blob``.

    Um alvo que não existe em disco é devolvido intacto: o empacotamento é
    permissivo, e quem cobra a existência é ``tests/test_readme_urls.py``.
    Falhar aqui transformaria um link errado numa falha de build.
    """
    if NAO_E_CAMINHO.match(alvo):
        return alvo
    caminho = raiz / alvo.split("#", 1)[0]
    if not caminho.exists():
        return alvo
    if imagem:
        return f"{RAW}/{alvo}"
    return f"{TREE}/{alvo}" if caminho.is_dir() else f"{BLOB}/{alvo}"


def para_absoluto(texto: str, raiz: Path) -> str:
    """Reescreve os caminhos relativos do README como URLs absolutas."""

    def _img(m: re.Match[str]) -> str:
        return f"{m[1]}{_absoluta(m[2], raiz, imagem=True)}{m[3]}"

    def _md(m: re.Match[str]) -> str:
        return f"{m[1]}{m[2]}{_absoluta(m[3], raiz, imagem=bool(m[1]))}{m[4]}"

    return MARKDOWN.sub(_md, IMG_HTML.sub(_img, texto))


@contextmanager
def readme_publicavel(raiz: Path | None = None):
    """Deixa o README absoluto durante o build e o restaura ao sair.

    O que vai para o pacote é a versão convertida; a árvore de trabalho volta ao
    que era, para o build não aparecer como alteração pendente no ``git status``.
    """
    raiz = Path.cwd() if raiz is None else raiz
    readme = raiz / "README.md"
    if not readme.is_file():
        yield
        return
    original = readme.read_bytes()
    convertido = para_absoluto(original.decode("utf-8"), raiz).encode("utf-8")
    if convertido == original:
        yield
        return
    readme.write_bytes(convertido)
    try:
        yield
    finally:
        readme.write_bytes(original)
