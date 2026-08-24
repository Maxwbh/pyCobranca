"""O README aponta para dois destinos com exigências opostas.

No GitHub ele é lido dentro de uma branch, e caminho relativo resolve contra o
commit atual — a imagem aparece antes de a mudança chegar à ``main``, que é
quando se quer olhar para ela. No PyPI ele é o ``long_description``, renderizado
fora do repositório, onde caminho relativo não resolve e a imagem some.

O acordo: o arquivo fica relativo, e ``tools/_backend_readme.py`` converte para
absoluto no empacotamento. Estes testes prendem as duas pontas — que o arquivo
não volte a ter URL fixada em ``main``, e que a conversão cubra o que o PyPI
precisa.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"


def _carrega_modulo():
    origem = RAIZ / "tools" / "_readme_urls.py"
    spec = importlib.util.spec_from_file_location("_readme_urls", origem)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


urls = _carrega_modulo()
TEXTO = README.read_text(encoding="utf-8")

#: Todo alvo de ``<img src>``, ``![](...)`` e ``[](...)`` do README.
ALVOS = [m[2] for m in urls.IMG_HTML.finditer(TEXTO)] + [
    m[3] for m in urls.MARKDOWN.finditer(TEXTO)
]
RELATIVOS = [a for a in ALVOS if not urls.NAO_E_CAMINHO.match(a)]


def test_o_readme_nao_tem_url_fixada_numa_branch() -> None:
    """A regressão que este arranjo existe para impedir.

    Uma URL ``.../main/...`` no arquivo faz a imagem sumir em toda branch que
    ainda não foi promovida — e some justamente na revisão, que é onde se olha.

    Só conteúdo **fixado numa ref** é proibido. Páginas do repositório que não
    têm ref — ``/stargazers``, ``/issues``, ``/releases`` — são URL absoluta
    legítima e continuam permitidas.
    """
    fixadas = re.findall(
        r"raw\.githubusercontent\.com/Maxwbh/pyCobranca/\S+"
        r"|github\.com/Maxwbh/pyCobranca/(?:blob|tree|raw)/\S+",
        TEXTO,
    )
    assert fixadas == [], f"conteúdo do repositório fixado numa ref: {fixadas}"


def test_todo_caminho_relativo_existe_no_repositorio() -> None:
    """O backend é permissivo com alvo inexistente; a cobrança é aqui.

    Sem isto, um caminho errado atravessaria o build em silêncio e viraria link
    morto na página do PyPI.
    """
    ausentes = [a for a in RELATIVOS if not (RAIZ / a.split("#", 1)[0]).exists()]
    assert ausentes == [], f"caminhos que não existem: {ausentes}"


def test_o_readme_referencia_as_cinco_capturas() -> None:
    """As capturas do README são a vitrine do projeto: some uma e ninguém nota."""
    capturas = {a for a in RELATIVOS if a.startswith("docs/images/screenshots/")}
    assert capturas == {
        f"docs/images/screenshots/{n}.png"
        for n in ("boleto-moderno", "boleto-pix", "boleto-logo", "boleto-tema", "carne")
    }


def test_conversao_nao_deixa_caminho_relativo() -> None:
    """O que o PyPI recebe não pode ter caminho relativo sobrando."""
    convertido = urls.para_absoluto(TEXTO, RAIZ)
    restantes = [
        m[2] for m in urls.IMG_HTML.finditer(convertido) if not urls.NAO_E_CAMINHO.match(m[2])
    ] + [m[3] for m in urls.MARKDOWN.finditer(convertido) if not urls.NAO_E_CAMINHO.match(m[3])]
    assert restantes == [], f"ficaram relativos após a conversão: {restantes}"


def test_imagem_vira_raw_e_link_vira_blob() -> None:
    """Cada tipo de alvo tem a URL que o GitHub serve para ele.

    Imagem por ``blob`` sai como página HTML, não como bytes: o ``<img>`` quebra.
    """
    convertido = urls.para_absoluto(TEXTO, RAIZ)
    for captura in ("boleto-moderno", "boleto-tema"):
        assert f"{urls.RAW}/docs/images/screenshots/{captura}.png" in convertido
    assert f"{urls.BLOB}/LICENSE" in convertido
    assert f"{urls.TREE}/examples" in convertido  # diretório usa tree, não blob


@pytest.mark.parametrize(
    "alvo",
    ["https://pypi.org/project/pycobranca/", "mailto:maxwbh@gmail.com", "#instalacao", "//exemplo"],
)
def test_url_externa_e_ancora_ficam_intactas(alvo: str) -> None:
    """Converter o que não é caminho do repositório quebraria o link."""
    texto = f"[x]({alvo})"
    assert urls.para_absoluto(texto, RAIZ) == texto


def test_diretorio_de_trabalho_nao_muda_com_o_build() -> None:
    """O README convertido é do pacote; o arquivo em disco tem de voltar ao que era."""
    antes = README.read_bytes()
    with urls.readme_publicavel(RAIZ):  # explícito: não depender do cwd do pytest
        durante = README.read_bytes()
    assert README.read_bytes() == antes, "o README não foi restaurado após o build"
    assert durante != antes, "o README não chegou a ser convertido"
