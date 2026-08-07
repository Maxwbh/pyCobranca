"""Ler um retorno CNAB (400 ou 240) e traduzir as ocorrências.

    python examples/05_retorno_cnab.py

O layout e o banco são detectados pelo próprio arquivo.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal

from _comum import DADOS, titulo

from pycobranca.cnab.retorno import Retorno


def reais(centavos: str | None) -> str:
    """Os valores do retorno vêm como string em centavos, sem separador."""
    return f"{Decimal(centavos or '0') / 100:.2f}"


def main() -> None:
    retorno = Retorno.ler(DADOS / "retorno-itau.ret")

    titulo(f"Retorno CNAB {retorno.layout} — banco {retorno.codigo_banco}")
    print(f"Registros: {len(retorno.registros)}")

    for registro in retorno.registros[:5]:
        print(
            f"  {registro.nosso_numero:>12}  ocorrência {registro.codigo_ocorrencia}"
            f"  R$ {reais(registro.valor_recebido):>10}"
            f"  {retorno.descricao_ocorrencia(registro)}"
        )
    if len(retorno.registros) > 5:
        print(f"  ... e mais {len(retorno.registros) - 5} registro(s)")

    titulo("Resumo por ocorrência")
    contagem = Counter(
        (r.codigo_ocorrencia, retorno.descricao_ocorrencia(r)) for r in retorno.registros
    )
    for (codigo, descricao), quantidade in sorted(contagem.items()):
        print(f"  {codigo}  {descricao:<40} {quantidade:>3}x")


if __name__ == "__main__":
    main()
