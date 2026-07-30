"""Conciliação: casa as transações de um extrato OFX com os nossos números
esperados (de boletos emitidos ou do retorno CNAB), fechando o ciclo
emissão → retorno → extrato.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .parser import Extrato, Transacao

__all__ = ["Conciliacao", "concilia"]


def _norm(valor: str) -> str:
    return str(valor).lstrip("0") or "0"


@dataclass
class Conciliacao:
    """Resultado da conciliação de um extrato contra nossos números esperados."""

    conciliadas: list[tuple[Transacao, str]] = field(default_factory=list)
    nao_conciliadas: list[Transacao] = field(default_factory=list)
    pendentes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "conciliadas": [
                {"nosso_numero": nn, "transacao": t.to_dict()} for t, nn in self.conciliadas
            ],
            "nao_conciliadas": [t.to_dict() for t in self.nao_conciliadas],
            "pendentes": list(self.pendentes),
            "resumo": {
                "total_conciliadas": len(self.conciliadas),
                "total_nao_conciliadas": len(self.nao_conciliadas),
                "total_pendentes": len(self.pendentes),
            },
        }


def concilia(
    extrato: Extrato,
    nossos_numeros: Iterable[str],
    *,
    somente_creditos: bool = True,
) -> Conciliacao:
    """Casa as transações de ``extrato`` com ``nossos_numeros``.

    Uma transação casa quando o nosso número extraído do memo bate com um
    esperado (comparação exata ou sem zeros à esquerda) ou quando um esperado
    aparece no texto do memo. Por padrão considera apenas créditos
    (recebimentos).

    :returns: :class:`Conciliacao` com as casadas, as não casadas e os nossos
        números esperados que não apareceram no extrato (``pendentes``).
    """
    esperados = {str(n) for n in nossos_numeros if str(n).strip()}
    por_norma = {_norm(n): n for n in esperados}
    transacoes = extrato.creditos if somente_creditos else list(extrato.transacoes)

    conciliadas: list[tuple[Transacao, str]] = []
    nao: list[Transacao] = []
    vistos: set[str] = set()

    for t in transacoes:
        casado: str | None = None
        nn = t.nosso_numero_extraido
        if nn and nn in esperados:
            casado = nn
        elif nn and _norm(nn) in por_norma:
            casado = por_norma[_norm(nn)]
        else:
            for e in esperados:
                if e and e in (t.memo or ""):
                    casado = e
                    break
        if casado is not None:
            conciliadas.append((t, casado))
            vistos.add(casado)
        else:
            nao.append(t)

    pendentes = sorted(esperados - vistos)
    return Conciliacao(conciliadas=conciliadas, nao_conciliadas=nao, pendentes=pendentes)
