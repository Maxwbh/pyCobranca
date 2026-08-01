"""Ler um extrato OFX e conciliar contra os boletos emitidos.

    python examples/06_ofx_conciliacao.py

Fecha o ciclo emissão -> remessa -> retorno -> extrato: o nosso número é
extraído do memo de cada transação e casado com os títulos emitidos.
"""

from __future__ import annotations

from _comum import DADOS, titulo

from pycobranca.ofx import Extrato, concilia


def main() -> None:
    extrato = Extrato.ler(DADOS / "extrato.ofx")  # OFX v1 (SGML) ou v2 (XML)

    titulo(f"Extrato {extrato.org} — ag. {extrato.agencia} c/c {extrato.conta_numero}")
    print(f"Saldo: R$ {extrato.saldo_valor} em {extrato.saldo_data}")
    print(f"Transações: {len(extrato.transacoes)} ({len(extrato.creditos)} crédito(s))")

    for transacao in extrato.creditos:
        print(
            f"  {transacao.data}  R$ {transacao.valor:>9}"
            f"  nosso nº {transacao.nosso_numero_extraido or '—'}  {transacao.memo}"
        )

    titulo("Conciliação")
    emitidos = ["12345678", "87654321"]  # nossos números que esperamos receber
    resultado = concilia(extrato, emitidos)

    for transacao, nosso_numero in resultado.conciliadas:
        print(f"  ✓ {nosso_numero} conciliado com R$ {transacao.valor} em {transacao.data}")
    for nosso_numero in resultado.pendentes:
        print(f"  … {nosso_numero} ainda pendente (sem crédito no extrato)")
    for transacao in resultado.nao_conciliadas:
        print(f"  ? crédito sem título correspondente: R$ {transacao.valor} — {transacao.memo}")


if __name__ == "__main__":
    main()
