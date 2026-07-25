# 13 — OFX (extrato bancário e conciliação)

O módulo [`pycobranca.ofx`](../pycobranca/ofx/) lê o **extrato bancário OFX** e concilia as
transações com os boletos emitidos. Complementa o retorno CNAB: enquanto o retorno traz o que o
banco processou dos títulos registrados, o OFX traz o **extrato da conta** — útil para conferir
recebimentos que chegaram por boleto.

## Recursos

- **OFX v1 (SGML)** e **v2 (XML)** — os campos-folha são lidos por um tokenizador tolerante que
  atende os dois formatos.
- **Encoding**: normaliza Latin‑1 → UTF‑8 (padrão dos bancos brasileiros).
- **Extração de nosso número** do campo `memo`, por banco (Sicoob, Itaú, BB, Bradesco, Caixa) e um
  padrão genérico.
- **Conciliação** contra os nossos números emitidos, com a lista de **pendentes**.
- **Python puro**, sem dependências novas.

## Ler um extrato

```python
from pycobranca.ofx import Extrato

extrato = Extrato.ler("extrato.ofx")  # caminho, bytes ou objeto com .read()

extrato.org  # "ITAU"
extrato.fid  # "341"
extrato.agencia  # "1234"  (BRANCHID)
extrato.conta_numero  # "56789-0"
extrato.saldo_valor  # Decimal("5230.75")
extrato.periodo  # (date(2025, 2, 5), date(2025, 2, 10))

for t in extrato.transacoes:
    # tipo: "CREDIT" | "DEBIT" (derivado do sinal do valor); valor sempre positivo
    print(t.tipo, t.data, t.valor, t.nosso_numero_extraido, t.memo)
```

`Extrato.ler(..., somente_creditos=True)` mantém apenas os recebimentos. As propriedades
`extrato.creditos` e `extrato.debitos` filtram sem reparsear.

### Serialização

`extrato.to_dict()` devolve uma estrutura **JSON-friendly** (banco, conta, período, saldo,
transações e resumo com totais/somatórios), pronta para consumo via REST. O contrato é verificado
por testes contra os schemas **`ExtratoOFX`** e **`TransacaoOFX`** de
[`contrato_rest.json`](../pycobranca/contracts/contrato_rest.json).

## Conciliar com os boletos emitidos

```python
from pycobranca.ofx import Extrato, concilia

extrato = Extrato.ler("extrato.ofx")
resultado = concilia(extrato, ["12345678", "0000087654"])  # nossos números emitidos

resultado.conciliadas  # [(Transacao, nosso_numero), ...]
resultado.nao_conciliadas  # transações sem correspondência
resultado.pendentes  # nossos números esperados que não apareceram no extrato
resultado.to_dict()  # visão JSON-friendly
```

A correspondência considera o nosso número extraído do memo (comparação exata ou **sem zeros à
esquerda**) e, como fallback, a presença do nosso número no texto do memo. Por padrão só os
**créditos** entram na conciliação (`somente_creditos=True`).

## Onde a lógica vive

Todo o processamento de OFX (parse, extração de nosso número e conciliação) vive **no pacote**, sem
dependência de HTTP. A lógica é testada uma vez e reaproveitada por qualquer consumidor — um script,
um SDK ou um serviço REST — que apenas chama `Extrato.ler(...)`/`concilia(...)` e serializa com
`to_dict()`.
