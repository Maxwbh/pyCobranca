"""Validação independente do retorno CNAB (estrutura FEBRABAN + cross-check do parser).

Espelha o validador de remessa (``test_cnab_estrutura.py``), agora do lado da
leitura. Para cada arquivo ``.RET`` de referência:

1. **Estrutura FEBRABAN** (lida posição a posição, sem o parser): sequência
   header → detalhe → trailer; código do banco constante (240); tipos de
   registro válidos.
2. **Cross-check do parser**: o que ``Retorno.ler`` extrai é confrontado com uma
   releitura independente do arquivo bruto — o parser **não** pode vazar o
   trailer como registro; a contagem de registros bate com os registros de
   detalhe contados à parte; e cada ``nosso_numero`` extraído está de fato
   presente na linha de origem.

Os arquivos de retorno reais chegam com linhas de largura irregular (não
preenchidas até 240); por isso o 240 não checa largura fixa, só a estrutura.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

from pycobranca.cnab.retorno import Retorno

FIXTURES = Path(__file__).parent / "fixtures" / "retorno"
ARQUIVOS = sorted(Path(p).name for p in glob.glob(str(FIXTURES / "*.RET")))


def _linhas(nome: str) -> list[str]:
    bruto = (FIXTURES / nome).read_bytes().decode("latin-1")
    sep = "\r\n" if "\r\n" in bruto else "\n"
    return [linha for linha in bruto.split(sep) if linha.strip()]


def _valida_estrutura_400(linhas: list[str]) -> list[str]:
    assert len(linhas) >= 3, "retorno 400 precisa de header, ≥1 detalhe e trailer"
    assert linhas[0][0] == "0", "primeiro registro deve ser o header (tipo 0)"
    assert linhas[-1][0] == "9", "último registro deve ser o trailer (tipo 9)"
    assert all(len(linha) == 400 for linha in linhas), "todo registro do 400 tem 400 posições"
    assert [linha[0] for linha in linhas].count("0") == 1, "deve haver exatamente um header"
    assert [linha[0] for linha in linhas].count("9") == 1, "deve haver exatamente um trailer"
    return [linha for linha in linhas if linha[0] not in "09"]  # detalhes


def _valida_estrutura_240(linhas: list[str]) -> None:
    # Identifica header/trailer pelo TIPO de registro (pos 7), não pelo número do
    # lote: arquivos reais variam o lote (ex.: Santander usa 9692, não 9999).
    banco = linhas[0][:3]
    assert banco.isdigit(), f"código do banco não numérico: {banco!r}"
    assert all(linha[:3] == banco for linha in linhas), "código do banco deve ser constante"
    assert linhas[0][7] == "0", "primeiro registro deve ser o header de arquivo (tipo 0)"
    assert linhas[-1][7] == "9", "último registro deve ser o trailer de arquivo (tipo 9)"
    for linha in linhas[1:-1]:
        assert linha[7] in "135", f"registro de lote com tipo inesperado: {linha[7]!r}"


@pytest.mark.parametrize("nome", ARQUIVOS)
def test_retorno_estrutura_e_parser(nome: str) -> None:
    linhas = _linhas(nome)
    retorno = Retorno.ler(FIXTURES / nome)
    registros = retorno.registros

    # 1) o parser nunca pode devolver o trailer (registro de controle) como título
    assert all(r.codigo_registro != "9" for r in registros), (
        f"{nome}: parser vazou o trailer (tipo 9) como registro"
    )

    if "CNAB400" in nome:
        detalhes = _valida_estrutura_400(linhas)
        # 2) contagem: um registro por linha de detalhe (header e trailer fora)
        assert len(registros) == len(detalhes), (
            f"{nome}: {len(registros)} registros ≠ {len(detalhes)} linhas de detalhe"
        )
        # 3) cross-check posicional: o valor extraído vem da linha correta
        for i, reg in enumerate(registros):
            nn = (reg.nosso_numero or "").strip()
            if nn:
                assert nn in detalhes[i], (
                    f"{nome}: nosso_numero {nn!r} do registro {i} não está na linha de origem"
                )
    else:  # CNAB 240
        _valida_estrutura_240(linhas)
        segmentos_t = sum(1 for ln in linhas if ln[7] == "3" and ln[13:14] == "T")
        segmentos_u = sum(1 for ln in linhas if ln[7] == "3" and ln[13:14] == "U")
        # 2) cada registro combina um segmento T (dados) + um U (valores)
        assert len(registros) == segmentos_t, (
            f"{nome}: {len(registros)} registros ≠ {segmentos_t} segmentos T"
        )
        assert segmentos_t == segmentos_u, (
            f"{nome}: {segmentos_t} segmentos T ≠ {segmentos_u} segmentos U"
        )
        # 3) o nosso_numero extraído está presente no arquivo bruto
        bruto = "".join(linhas)
        for reg in registros:
            nn = (reg.nosso_numero or "").strip()
            if nn:
                assert nn in bruto, f"{nome}: nosso_numero {nn!r} ausente no arquivo bruto"


def test_ha_fixtures_retorno() -> None:
    assert ARQUIVOS, "nenhum fixture de retorno encontrado"
