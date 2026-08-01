---
description: >-
  Boleto Unicred (136) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (21). Remessa e retorno CNAB 400 e 240.
---

# Unicred (136)

**Manual oficial de referência:** *Manual de Cobrança Unicred* (leiautes CNAB 240 e CNAB 400).
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/unicred.py`](../../pycobranca/bancos/unicred.py) ·
Conta 9 + DV informado.

**Logo empacotado:** disponível via `logo_do_banco("136")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Conta de 9 dígitos com DV informado; DV do nosso número por módulo 11.

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–4   | 4  | Agência |
| 5–13  | 9  | Conta |
| 14    | 1  | Dígito da conta |
| 15–24 | 10 | Nosso número |
| 25    | 1  | DV do nosso número (módulo 11) |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 sobre o nosso número com 10 posições (pesos `9..2`
  cíclicos, direita→esquerda), `DV = soma % 11`; resultados **10 e 11 viram 0**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Conta | 1–9 dígitos |
| Nosso número | 1–10 dígitos |
| Carteira | conjunto: 21 |

## Formatos de exibição

- Nosso número: `nosso número(10)-DV` (DV por módulo 11, mapa `{10: 0, 11: 0}`) via
  `nosso_numero_formatado()`
- Agência/conta: `agência(4) / conta(9)-dígito`

## Exemplo (saída da engine)

Entrada: agência `0123`, conta `001234567`, dígito da conta `8`, nosso número `1234567890`,
carteira `21`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      0123001234567812345678900
Código de barras: 13693153900000127500123001234567812345678900
Linha digitável:  13690.12305 01234.567814 23456.789009 3 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/unicred.py`](../../pycobranca/cnab/cnab400/unicred.py) ·
fixture: [`tests/fixtures/remessa_unicred_cnab400.rem`](../../tests/fixtures/remessa_unicred_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | código do beneficiário(20) · empresa(30) · `136` + `UNICRED` · data (DDMMAA) · `000` + sequencial(7) |
| Detalhe (tipo 1) | agência(5) + **DV agência** · conta(12) + **DV conta** · carteira(3) · `136` · código/percentual de multa · tipo de mora · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · desconto · emissão · protesto/dias · valor de mora(13) · data/valor de desconto · **nosso número(10) + DV** · abatimento(13) · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 20/UF) · avalista(38) · sequencial(6) |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

**DVs (módulo 11):** agência `{10: "X"}`; conta de 5 posições `{10: 0}`; nosso
número de 10 posições `{10: 0, 11: 0}`.

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/unicred.py`](../../pycobranca/cnab/cnab240/unicred.py) ·
fixture: [`tests/fixtures/remessa_unicred_cnab240.rem`](../../tests/fixtures/remessa_unicred_cnab240.rem)

O CNAB 240 da Unicred **reaproveita integralmente o layout do Sicredi** (mesma cooperativa de
tecnologia) — a classe
`RemessaUnicred240` herda de `RemessaSicredi240` sem alterações. Consulte
[`748-sicredi.md`](748-sicredi.md) para a composição de header de arquivo/lote, segmentos
P/Q/R e trailers (versão de arquivo `081`, de lote `040`, espécie `03`).
