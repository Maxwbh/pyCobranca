---
description: >-
  Boleto Banco do Nordeste (004) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (21, 31, 41, 51). Remessa e retorno CNAB 400.
---

# Banco do Nordeste (004)

**Manuais oficiais de referência:** *Cobrança Eletrônica BNB* · *Padrão BNB — CNAB 400*.
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação:** [`pycobranca/bancos/banco_nordeste.py`](../../pycobranca/bancos/banco_nordeste.py) ·
Dígito do banco: **3** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("004")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DV do nosso número por módulo 11 (fatores 2..8).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–4   | 4 | Agência |
| 5–11  | 7 | Conta |
| 12    | 1 | Dígito da conta |
| 13–19 | 7 | Nosso número |
| 20    | 1 | DV do nosso número (módulo 11) |
| 21–22 | 2 | Carteira |
| 23–25 | 3 | `000` |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 sobre o nosso número com 7 posições, fatores `2..8`
  (cíclicos, direita→esquerda), `DV = 11 - (soma % 11)`; resultados **10 e 11 viram 0**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Conta | 1–7 dígitos |
| Dígito da conta | 1 dígito — entra no campo livre em 1 posição |
| Nosso número | 1–7 dígitos |
| Carteira | conjunto: 21, 31, 41, 51 |

## Formatos de exibição

- Nosso número: `nosso número(7)-DV` → `0000123-6`
- Agência/conta: `agência(4)/conta(7)-dígito` → `0123/0012345-6`

## Exemplo (saída da engine)

Entrada: agência `0123`, conta `0012345`, dígito da conta `6`, carteira `21`, nosso número
`1234567`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      0123001234561234567921000
Código de barras: 00494153900000127500123001234561234567921000
Linha digitável:  00490.12305 01234.561239 45679.210000 4 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/banco_nordeste.py`](../../pycobranca/cnab/cnab400/banco_nordeste.py) ·
fixture: [`tests/fixtures/remessa_banco_nordeste_cnab400.rem`](../../tests/fixtures/remessa_banco_nordeste_cnab400.rem)

> **Correção de um registro anterior.** Esta página dizia que o detalhe tinha **401 posições**
> porque *o layout do banco somava um caractere* ao padrão FEBRABAN, e que por isso
> `tamanho_registro` ficava em `None`. Não era o layout: o nosso número tem **7 posições** aqui, e
> um valor de 8 dígitos atravessava para a posição seguinte, porque `rjust` preenche e não corta.
> A fixture não pegava — vem da implementação de referência, que estoura igual. Hoje o nosso número
> maior que o campo é **recusado**, os três registros saem em 400, e a conferência de tamanho está
> ligada.

Estrutura do arquivo (CRLF, maiúsculas sem acentos):

| Registro | Tam. | Conteúdo principal |
|----------|:----:|--------------------|
| Header (`01REMESSA01COBRANCA`) | 400 | info da conta (agência 4 + `00` + conta 7 + dígito) · empresa(30) · `004` + `B.DO NORDESTE` · data (DDMMAA) |
| Detalhe (tipo 1) | 400 | agência + `00` + conta + dígito · 2 dígitos do percentual de multa · uso da empresa(25) · nosso número(7) + **DV** · código da carteira · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `004` · espécie `01` · aceite · emissão · mora/desconto/IOF/abatimento · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 15/UF) · avalista(40) · `99` + `0` · sequencial(6) |
| Trailer (tipo 9) | 400 | 393 brancos + sequencial(6) |

**DV do nosso número:** módulo 11 sobre o nosso número com 7 posições, fatores
`2..8`, bloco `11 - (soma % 11)`, mapa `{1: 0, 10: 0, 11: 0}`.

**Código da carteira:** carteira `51` → `I`; caso contrário, mapeado por emissão do boleto
(`1`/`2`) e carteira (`21`/`41`) → `1`/`2`/`4`/`5`.
