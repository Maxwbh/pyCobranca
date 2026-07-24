"""Regressão contra retornos CNAB **reais** de terceiros (fixtures externos).

Arquivos de retorno de bancos reais (Caixa 240, HSBC 400, Sicredi 400) extraídos
do projeto laravel-boleto (MIT) — ver ``externos/NOTICE.md``. Servem como prova
independente de que o parser e o validador estrutural funcionam sobre dados que
**não geramos**, cobrindo bancos com pouca amostra de retorno própria.

Reaproveita o validador de ``test_retorno_estrutura.py`` (estrutura FEBRABAN +
cross-check do parser: sem trailer vazado, contagem batendo com os registros de
detalhe/segmentos T, e ``nosso_numero`` presente na linha de origem).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_retorno_estrutura import _valida_estrutura_240, _valida_estrutura_400

from pycobranca.cnab.retorno import Retorno

EXTERNOS = Path(__file__).parent / "fixtures" / "retorno" / "externos"

# (arquivo, layout, código do banco esperado)
CASOS = [
    ("caixa_cnab240.ret", "240", "104"),
    ("hsbc_cnab400.ret", "400", "399"),
    ("sicredi_cnab400.ret", "400", "748"),
]


def _linhas(caminho: Path) -> list[str]:
    bruto = caminho.read_bytes().decode("latin-1")
    sep = "\r\n" if "\r\n" in bruto else "\n"
    return [linha for linha in bruto.split(sep) if linha.strip()]


@pytest.mark.parametrize(("arquivo", "layout", "banco"), CASOS)
def test_retorno_externo_real(arquivo: str, layout: str, banco: str) -> None:
    caminho = EXTERNOS / arquivo
    linhas = _linhas(caminho)
    retorno = Retorno.ler(caminho)
    registros = retorno.registros

    assert retorno.codigo_banco == banco, f"{arquivo}: banco {retorno.codigo_banco} ≠ {banco}"
    assert registros, f"{arquivo}: nenhum registro lido"
    assert all(r.codigo_registro != "9" for r in registros), f"{arquivo}: trailer vazou"

    if layout == "400":
        detalhes = _valida_estrutura_400(linhas)
        assert len(registros) == len(detalhes), (
            f"{arquivo}: {len(registros)} registros ≠ {len(detalhes)} linhas de detalhe"
        )
        for i, reg in enumerate(registros):
            nn = (reg.nosso_numero or "").strip()
            if nn:
                assert nn in detalhes[i], f"{arquivo}: nosso_numero {nn!r} ausente na linha {i}"
    else:
        _valida_estrutura_240(linhas)
        segmentos_t = sum(1 for ln in linhas if ln[7] == "3" and ln[13:14] == "T")
        segmentos_u = sum(1 for ln in linhas if ln[7] == "3" and ln[13:14] == "U")
        assert len(registros) == segmentos_t, (
            f"{arquivo}: {len(registros)} registros ≠ {segmentos_t} segmentos T"
        )
        assert segmentos_t == segmentos_u, f"{arquivo}: T ({segmentos_t}) ≠ U ({segmentos_u})"
        bruto = "".join(linhas)
        for reg in registros:
            nn = (reg.nosso_numero or "").strip()
            if nn:
                assert nn in bruto, f"{arquivo}: nosso_numero {nn!r} ausente no arquivo"
