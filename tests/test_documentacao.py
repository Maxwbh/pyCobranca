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


# --------------------------------------------------------------------------- #
# Contagens e listas mantidas à mão
# --------------------------------------------------------------------------- #
#
# Nada disso é estilo. Um banco novo entra no registro e a documentação continua
# anunciando o número antigo — a home dos docs ficou dizendo "18 bancos" enquanto
# o README dizia 19, e uma página de roadmap seguiu listando o Inter como fora de
# escopo depois de ele ter entrado. Quem lê a documentação não tem como saber
# qual dos dois números é o verdadeiro.


def _bancos():
    from pycobranca.bancos import Bancos

    return sorted(Bancos.todos(), key=lambda b: b.codigo)


def test_todo_banco_do_registro_tem_pagina_propria() -> None:
    """Banco sem página é banco que ninguém sabe usar."""
    faltando = [
        f"{banco.codigo} {banco.nome}"
        for banco in _bancos()
        if not list(DOCS.glob(f"bancos/{banco.codigo}-*.md"))
    ]
    assert faltando == [], f"sem página em docs/bancos/: {faltando}"


def test_nenhuma_pagina_anuncia_um_numero_de_bancos_desatualizado() -> None:
    """Varre o texto por "N bancos" e recusa o que contradiz o registro.

    Só entram as frases sobre a biblioteca inteira. "CNAB 400 para 14 bancos" é um
    recorte legítimo e fica de fora — a expressão exigida aqui é a que o leitor lê
    como o tamanho do catálogo.
    """
    total = len(_bancos())
    # "para 18 bancos", "os 18 bancos", "dos 18 bancos", "nos **18 bancos**"
    # "N bancos", "N classes de boleto", "N códigos aceitos" — as três formas que
    # a documentação usou para dizer a mesma coisa, e as três derivaram.
    frase = re.compile(
        r"(?:para|os|dos|nos|em|registro d[oa]s?|as)\s+\**(\d+)\**\s+"
        r"(?:bancos|c[óo]digos|classes de boleto)\b",
        re.I,
    )
    # linhas que recortam o catálogo em vez de medi-lo
    recorte = re.compile(r"\d+\s+dos\s+\d+\s+bancos|CNAB\s*(?:400|240)|remessa|retorno|PIX", re.I)
    erradas = []
    for pagina in _paginas():
        for linha in pagina.read_text(encoding="utf-8").splitlines():
            if recorte.search(linha):
                continue
            for numero in frase.findall(linha):
                if int(numero) != total:
                    erradas.append(f"{pagina.name}: {linha.strip()[:90]}")
    assert erradas == [], f"contagem de bancos divergente (registro tem {total}):\n" + "\n".join(
        erradas
    )


def test_a_documentacao_nao_oferece_carteira_que_o_banco_recusa() -> None:
    """Carteira anunciada e recusada é promessa que sempre falha.

    Foi o caso da ``CSB`` do HSBC: documentada como suportada, com um campo livre
    de 27 posições onde cabem 25. A retirada dela do código só vale se a
    documentação parar de oferecê-la.
    """
    from pycobranca.exceptions import PyCobrancaError

    retiradas = {"399": {"CSB"}}
    oferecidas = []
    for banco in _bancos():
        for carteira in retiradas.get(banco.codigo, set()):
            for pagina in DOCS.glob(f"bancos/{banco.codigo}-*.md"):
                texto = pagina.read_text(encoding="utf-8")
                if re.search(rf"carteiras? (?:aceitas?|suportadas?)[^\n]*{carteira}", texto, re.I):
                    oferecidas.append(f"{pagina.name}: oferece {carteira}")
            assert carteira not in banco.carteiras, (
                f"{banco.codigo}: {carteira} voltou para `carteiras` — "
                "atualize esta lista ou a documentação"
            )
    assert oferecidas == [], oferecidas
    assert PyCobrancaError  # importado para o teste falhar cedo se a hierarquia sumir


def test_a_pagina_do_banco_lista_todo_campo_com_regra_declarada() -> None:
    """A tabela "Validação de campos" tem de espelhar ``regras_campos``.

    Não é zelo de formatação. As regras que faltavam nessas tabelas eram
    justamente as de uma posição — ``digito_conta``, ``digito_agencia``,
    ``byte_idt``, a variação e a parcela do Sicoob —, que entram no campo livre e
    quebram o boleto inteiro quando estouram. Quem lê a página para saber o que
    precisa preencher não via nenhuma delas.

    Serve o rótulo amigável (``_ROTULOS_CAMPOS``, que é o que a mensagem de erro
    usa) **ou** o nome cru do atributo: o Inter chama o convênio de "número da
    operação", como o manual dele, e escreve ``(`convenio`)`` ao lado — nomeia o
    campo, que é o que importa.
    """
    from pycobranca.bancos.base import _ROTULOS_CAMPOS

    secao = re.compile(r"^## Validação de campos.*?(?=^## )", re.M | re.S)
    faltando = []
    for banco in _bancos():
        for pagina in DOCS.glob(f"bancos/{banco.codigo}-*.md"):
            achou = secao.search(pagina.read_text(encoding="utf-8"))
            if not achou:
                continue
            tabela = achou.group(0).lower()
            for campo in banco.regras_campos:
                rotulo = _ROTULOS_CAMPOS.get(campo, campo).lower()
                if rotulo not in tabela and campo not in tabela:
                    faltando.append(f"{pagina.name}: sem linha para {campo!r} ({rotulo!r})")
    assert faltando == [], "\n".join(faltando)
