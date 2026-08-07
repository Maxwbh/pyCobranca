"""A documentação não pode ensinar API que não existe.

A página do CNAB documentou por um tempo `from pycobranca.cnab.remessa import
Remessa` — módulo que nunca existiu — enquanto as 26 classes reais de remessa
não apareciam em lugar nenhum. Quem copiava o exemplo recebia
``ModuleNotFoundError`` na página principal do subsistema.

Estes testes leem os blocos ```python de ``docs/`` e conferem que tudo que eles
importam de ``pycobranca`` resolve de verdade. Blocos que ilustram API de outro
projeto não importam do pacote e por isso não entram na varredura.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

BLOCO_PYTHON = re.compile(r"```python\n(.*?)```", re.S)
IMPORT_FROM = re.compile(r"^\s*from\s+(pycobranca[\w.]*)\s+import\s+([^\n#]+)", re.M)
IMPORT_MOD = re.compile(r"^\s*import\s+(pycobranca[\w.]*)", re.M)


def _paginas() -> list[Path]:
    return sorted(p for p in DOCS.rglob("*.md") if p.name != "changelog.md")


def _importacoes() -> list[tuple[str, str, str]]:
    """(página, módulo, nome) para cada símbolo importado de pycobranca."""
    achados: list[tuple[str, str, str]] = []
    for pagina in _paginas():
        for bloco in BLOCO_PYTHON.findall(pagina.read_text(encoding="utf-8")):
            for modulo, nomes in IMPORT_FROM.findall(bloco):
                for nome in re.split(r"[,\s()]+", nomes):
                    nome = nome.strip().rstrip(",")
                    if nome and nome != "as":
                        achados.append((pagina.name, modulo, nome))
            for modulo in IMPORT_MOD.findall(bloco):
                achados.append((pagina.name, modulo, ""))
    return achados


def test_ha_blocos_para_conferir() -> None:
    """Guarda contra o teste passar por não ter encontrado nada."""
    assert len(_importacoes()) >= 20


@pytest.mark.parametrize(
    ("pagina", "modulo", "nome"),
    _importacoes(),
    ids=lambda v: v if isinstance(v, str) else str(v),
)
def test_import_da_documentacao_resolve(pagina: str, modulo: str, nome: str) -> None:
    try:
        alvo = importlib.import_module(modulo)
    except ModuleNotFoundError as exc:  # pragma: no cover - só falha quando a doc erra
        pytest.fail(f"{pagina}: `{modulo}` não existe no pacote ({exc})")
    if nome:
        assert hasattr(alvo, nome), f"{pagina}: `{modulo}.{nome}` não existe"
