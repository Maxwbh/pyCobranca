"""O que a distribuição leva — conferido construindo o pacote de verdade.

Quem instala a biblioteca usa ``pycobranca/`` e mais nada. O wheel já sai limpo,
porque o setuptools só empacota o que ``packages`` declara — mas o **sdist leva o
repositório quase inteiro por padrão**, e é assim que ``tests/`` viajava: 38
arquivos, 302 KB, quase tudo fixture ``.rem``/``.RET``.

Um sdist gordo **não quebra instalação nenhuma**, e é justamente por isso que
passa despercebido: o pacote continua funcionando, só carrega o que ninguém
pediu. Sem esta conferência, a regressão volta na primeira mudança de
``MANIFEST.in`` e só aparece depois de publicada.

O teste constrói as distribuições de verdade, uma vez por sessão. Custa alguns
segundos; conferir o ``MANIFEST.in`` por leitura custaria menos e provaria menos
— o que vale é o que o ``python -m build`` produz.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: Não pertencem a nenhuma distribuição. Os dois primeiros são os que de fato
#: viajavam; os demais entram como prevenção, porque o padrão do sdist é
#: incluir, não excluir.
PROIBIDOS = ("tests", "docs", "examples", "site", ".github")

#: Precisam viajar no sdist: ``tools/`` carrega o backend declarado em
#: ``backend-path``, e sem ele o wheel não constrói a partir do sdist. Um prune
#: generoso demais quebraria isso em silêncio.
ESPERADOS_NO_SDIST = ("pycobranca", "tools", "pyproject.toml", "README.md", "LICENSE")


@pytest.fixture(scope="session")
def distribuicoes(tmp_path_factory) -> list[Path]:
    if shutil.which("git") is None or not (RAIZ / "pyproject.toml").exists():
        pytest.skip("fora da árvore do repositório")
    try:
        import build  # noqa: F401
    except ImportError:
        pytest.skip("o pacote `build` não está instalado (extra de desenvolvimento)")

    destino = tmp_path_factory.mktemp("dist")
    resultado = subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(destino)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        pytest.fail(
            f"`python -m build` falhou:\n{resultado.stdout[-2000:]}\n{resultado.stderr[-2000:]}"
        )
    return sorted(destino.glob("*.tar.gz")) + sorted(destino.glob("*.whl"))


def _conteudo(caminho: Path) -> list[str]:
    """Caminhos internos, já sem o diretório-raiz que o sdist acrescenta."""
    if caminho.suffix == ".whl":
        with zipfile.ZipFile(caminho) as z:
            return [n for n in z.namelist() if n]
    with tarfile.open(caminho) as t:
        return [n.split("/", 1)[1] for n in t.getnames() if "/" in n and n.split("/", 1)[1]]


def test_build_produz_as_duas_distribuicoes(distribuicoes) -> None:
    sufixos = {c.suffix for c in distribuicoes}
    assert sufixos == {".gz", ".whl"}, f"esperado sdist e wheel, veio {sorted(sufixos)}"


def test_nenhuma_distribuicao_leva_testes_ou_documentacao(distribuicoes) -> None:
    achados = [
        f"{caminho.name}: leva {proibido}/ "
        f"({sum(1 for n in _conteudo(caminho) if n.startswith(proibido + '/'))} arquivos)"
        for caminho in distribuicoes
        for proibido in PROIBIDOS
        if any(n.startswith(proibido + "/") for n in _conteudo(caminho))
    ]
    assert achados == [], "\n".join(achados)


def test_o_sdist_leva_o_que_precisa_para_construir_o_wheel(distribuicoes) -> None:
    """Prune generoso demais quebra o sdist sem quebrar o wheel — e em silêncio."""
    sdist = next(c for c in distribuicoes if c.suffix == ".gz")
    nomes = _conteudo(sdist)
    faltando = [
        esperado
        for esperado in ESPERADOS_NO_SDIST
        if not any(n == esperado or n.startswith(esperado + "/") for n in nomes)
    ]
    assert faltando == [], f"{sdist.name}: falta {faltando}"


def test_o_wheel_leva_so_o_pacote(distribuicoes) -> None:
    wheel = next(c for c in distribuicoes if c.suffix == ".whl")
    topos = {n.split("/")[0] for n in _conteudo(wheel)}
    assert topos == {"pycobranca", f"pycobranca-{_versao()}.dist-info"}, sorted(topos)


def _versao() -> str:
    import pycobranca

    return pycobranca.__version__
