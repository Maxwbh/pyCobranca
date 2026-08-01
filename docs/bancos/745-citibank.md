---
description: >-
  Boleto Citibank (745) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (3). Remessa e retorno CNAB 400.
---

# Citibank (745)

**Manual oficial de referência:** *Layout de Cobrança CNAB 400 — Citibank*. Sem manual público
localizado — layout portado por **paridade byte a byte** com os vetores de referência; ver
[`fontes-oficiais.md`](fontes-oficiais.md).

**Implementação:** [`pycobranca/bancos/citibank.py`](../../pycobranca/bancos/citibank.py) ·
Dígito do banco: **5** · PIX: —

## Resumo

Campo livre com portfólio e convênio sem o 1º dígito.

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1  | Carteira |
| 2–4   | 3  | Portfolio |
| 5–13  | 9  | Convênio (10 dígitos, sem o 1º) |
| 14–24 | 11 | Nosso número |
| 25    | 1  | DV do nosso número (módulo 11) |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 sobre o nosso número com 11 posições, fatores `2..9`
  (cíclicos, direita→esquerda), `DV = 11 - (soma % 11)`; resultados **10 e 11 viram 0**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Portfolio | até 3 dígitos (opcional) |
| Convênio | 1–10 dígitos |
| Nosso número | 1–11 dígitos |
| Carteira | conjunto: 3 |

## Formatos de exibição

- Nosso número: `nosso_numero(11).DV` → `12345678901.0`
- Agência/conta: `agência(4) / convênio(10)` → `0001 / 1234567890`

## Exemplo (saída da engine)

Entrada: agência `0001`, portfolio `123`, convênio `1234567890`, nosso número `12345678901`,
carteira `3`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      3123234567890123456789010
Código de barras: 74591153900000127503123234567890123456789010
Linha digitável:  74593.12323 34567.890123 34567.890107 1 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/citibank.py`](../../pycobranca/cnab/cnab400/citibank.py) ·
fixture: [`tests/fixtures/remessa_citibank_cnab400.rem`](../../tests/fixtures/remessa_citibank_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | portfólio(20) · empresa(30) · `745` + `CITIBANK` · data (DDMMAA) · complemento `01600BPI` |
| Detalhe (tipo 1) | tipo/CPF-CNPJ da empresa · portfólio(20) · uso da empresa(25) · espécie · nosso número(12) · 2º desconto (data/valor) · carteira · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `745` · espécie `07` · aceite · emissão · mora/desconto/IOF/abatimento · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 15/UF) · avalista(40) · `9` · sequencial(6) |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

**Portfólio:** informado no campo `portfolio`, alinhado à direita em 20 posições. Carteira
padrão `1` (portfólio 20). O identificador do detalhe usa `01`/`02` conforme CPF/CNPJ do cedente.
