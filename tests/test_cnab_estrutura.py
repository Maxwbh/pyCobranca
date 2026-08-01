"""Validação estrutural independente das remessas CNAB (padrão FEBRABAN).

Lê cada arquivo de remessa gerado, **posição a posição**, e confere as mesmas
invariantes que um sistema de intake bancário — ou um validador online como o
ValidaCNAB/Toolspace — verifica ao **aceitar** o arquivo, **sem reusar o código
gerador** da PyCobrança. É o "outro sistema" olhando para a nossa saída.

Os arquivos ``.rem`` são byte a byte idênticos à saída de ``gera_arquivo()``
(garantido por ``test_cnab_remessa.py``/``test_cnab_remessa_pix.py``), então
validar os fixtures valida transitivamente o gerador.

Regras verificadas (FEBRABAN):

- **CNAB 400** — sequência header (tipo 0) → detalhes → trailer (tipo 9);
  header e trailer com 400 posições (detalhes podem ter o comprimento próprio do
  banco); numeração sequencial nas 6 últimas posições, 1..N, com o trailer == N.
- **CNAB 240** — código do banco constante; header de arquivo (lote ``0000``,
  tipo 0) e trailer de arquivo (lote ``9999``, tipo 9); lotes bem-formados
  (header 1 → segmentos 3 → trailer 5) com segmentos válidos e sequencial do
  detalhe 1..M; **quantidade de registros do lote** (trailer de lote) e
  **quantidade de lotes/registros do arquivo** (trailer de arquivo) batendo com
  os registros físicos — regra em que a contagem do arquivo inclui **todos** os
  tipos 0/1/3/5/9 (inclusive os segmentos Y do PIX).
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
ARQUIVOS = sorted(Path(p).name for p in glob.glob(str(FIXTURES / "remessa_*.rem")))

_SEGMENTOS_VALIDOS = set("PQRSTUWYZ")

#: Bancos com layout proprietário (fora do padrão FEBRABAN) — validados à parte.
_PROPRIETARIOS = {"remessa_banco_brasilia_cnab400.rem"}  # BRB usa o formato DCB
_FEBRABAN = [nome for nome in ARQUIVOS if nome not in _PROPRIETARIOS]


def _linhas(nome: str) -> list[str]:
    bruto = (FIXTURES / nome).read_bytes().decode("latin-1")
    return [linha for linha in bruto.split("\r\n") if linha]


def _valida_400(linhas: list[str]) -> None:
    assert len(linhas) >= 3, "arquivo 400 precisa de header, ≥1 detalhe e trailer"
    assert linhas[0][0] == "0", "primeiro registro deve ser o header (tipo 0)"
    assert linhas[-1][0] == "9", "último registro deve ser o trailer (tipo 9)"
    assert all(linha[0] != "9" for linha in linhas[:-1]), "trailer (9) só pode aparecer no fim"
    assert len(linhas[0]) == 400, f"header com {len(linhas[0])} posições (esperado 400)"
    assert len(linhas[-1]) == 400, f"trailer com {len(linhas[-1])} posições (esperado 400)"
    assert all(len(linha) >= 400 for linha in linhas), "todo registro tem ao menos 400 posições"
    for i, linha in enumerate(linhas):
        seq = linha[-6:]
        assert seq.isdigit(), f"sequencial não numérico na linha {i + 1}: {seq!r}"
        assert int(seq) == i + 1, f"sequencial fora de ordem na linha {i + 1}: {seq}"
    assert int(linhas[-1][-6:]) == len(linhas), "sequencial do trailer ≠ total de registros"


def _valida_240(linhas: list[str]) -> None:
    assert len(linhas) >= 5, "arquivo 240 precisa de header arq, lote (≥3) e trailer arq"
    banco = linhas[0][:3]
    assert banco.isdigit(), f"código do banco não numérico: {banco!r}"
    assert all(linha[:3] == banco for linha in linhas), "código do banco deve ser constante"

    assert linhas[0][3:7] == "0000" and linhas[0][7] == "0", "header de arquivo malformado"
    assert linhas[-1][3:7] == "9999" and linhas[-1][7] == "9", "trailer de arquivo malformado"
    assert len(linhas[0]) == 240, f"header de arquivo com {len(linhas[0])} posições (≠ 240)"
    assert len(linhas[-1]) == 240, f"trailer de arquivo com {len(linhas[-1])} posições (≠ 240)"

    lotes: dict[str, list[str]] = {}
    for linha in linhas[1:-1]:
        lotes.setdefault(linha[3:7], []).append(linha)
    assert lotes, "arquivo sem lotes"
    numeros = sorted(lotes)
    assert numeros == [f"{i + 1:04d}" for i in range(len(numeros))], (
        f"numeração de lotes inválida: {numeros}"
    )

    for nro, regs in lotes.items():
        assert regs[0][7] == "1", f"lote {nro}: primeiro registro deve ser header de lote (tipo 1)"
        assert regs[-1][7] == "5", f"lote {nro}: último registro deve ser trailer de lote (tipo 5)"
        assert len(regs[0]) == 240, f"lote {nro}: header de lote com {len(regs[0])} posições"
        assert len(regs[-1]) == 240, f"lote {nro}: trailer de lote com {len(regs[-1])} posições"

        detalhes = regs[1:-1]
        assert detalhes, f"lote {nro} sem segmentos de detalhe"
        for seq_esperado, reg in enumerate(detalhes, start=1):
            assert reg[7] == "3", f"lote {nro}: registro de detalhe deve ser tipo 3"
            assert reg[13] in _SEGMENTOS_VALIDOS, f"lote {nro}: segmento inválido {reg[13]!r}"
            assert len(reg) >= 240, f"lote {nro}: detalhe com {len(reg)} posições (< 240)"
            seq = reg[8:13]
            assert seq.isdigit() and int(seq) == seq_esperado, (
                f"lote {nro}: sequencial do detalhe fora de ordem: {seq!r}"
            )

        qtd_lote = regs[-1][17:23]
        assert qtd_lote.isdigit() and int(qtd_lote) == len(regs), (
            f"lote {nro}: qtd de registros no trailer de lote ({qtd_lote}) ≠ {len(regs)} reais"
        )

    trailer = linhas[-1]
    qtd_lotes = trailer[17:23]
    qtd_reg = trailer[23:29]
    assert qtd_lotes.isdigit() and int(qtd_lotes) == len(lotes), (
        f"qtd de lotes no trailer de arquivo ({qtd_lotes}) ≠ {len(lotes)} reais"
    )
    assert qtd_reg.isdigit() and int(qtd_reg) == len(linhas), (
        f"qtd de registros no trailer de arquivo ({qtd_reg}) ≠ {len(linhas)} físicos"
    )


def test_ha_fixtures() -> None:
    assert ARQUIVOS, "nenhum fixture de remessa encontrado"


@pytest.mark.parametrize("nome", _FEBRABAN)
def test_remessa_estrutura_febraban(nome: str) -> None:
    linhas = _linhas(nome)
    if "cnab400" in nome:
        _valida_400(linhas)
    else:
        _valida_240(linhas)


def test_brb_usa_formato_dcb_proprietario() -> None:
    """BRB (Banco de Brasília) usa o layout DCB, fora do padrão FEBRABAN 400.

    Documenta e trava a exceção: header ``DCB`` (não tipo ``0``) e trailer ``9``.
    """
    linhas = _linhas("remessa_banco_brasilia_cnab400.rem")
    assert linhas[0].startswith("DCB"), "header do BRB deve começar com DCB"
    assert linhas[-1][0] == "9", "trailer do BRB deve ser tipo 9"
