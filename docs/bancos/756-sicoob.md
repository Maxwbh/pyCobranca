---
description: >-
  Boleto Sicoob (756) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (1, 3, 9, 09). Remessa e retorno CNAB 400 e 240. Suporta PIX/Bolepix.
---

# Sicoob (756)

**Manual oficial de referência:** *Manual de Layout Sicoob — Cobrança* (CNAB 400 e CNAB 240).
Fontes e portal (validador CNAB Sicoob) em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs
não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/sicoob.py`](../../pycobranca/bancos/sicoob.py) ·
Dígito do banco: **0** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("756")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DV do nosso número com fatores fixos 3-1-9-7 (da esquerda para a direita).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1 | Carteira |
| 2–5   | 4 | Agência |
| 6–7   | 2 | Variação (`01` se ausente) |
| 8–14  | 7 | Convênio (ou número do contrato na carteira 9) |
| 15–21 | 7 | Nosso número |
| 22    | 1 | DV do nosso número (módulo 11, fatores 3-1-9-7) |
| 23–25 | 3 | Quantidade de parcelas (`001` se ausente) |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 sobre `agência(4) + identificador(10) + nosso número(7)`,
  fatores fixos `3, 1, 9, 7` aplicados da **esquerda para a direita**, `DV = 11 - (soma % 11)`;
  resultados **10 e 11 viram 0**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Convênio | até 7 dígitos (opcional) |
| Número do contrato | até 7 dígitos (opcional) |
| Nosso número | 1–7 dígitos |
| Carteira | conjunto: 1, 3, 9, 09 |

## Formatos de exibição

- Nosso número: `nosso_numero(7)DV` → `12345673`
- Agência/conta: `agência / conta` (formato base de `BancoBase`)

## Exemplo (saída da engine)

Entrada: agência `1234`, convênio `1234567`, variação `01`, nosso número `1234567`, carteira
`1`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      1123401123456712345673001
Código de barras: 75692153900000127501123401123456712345673001
Linha digitável:  75691.12340 01123.456715 23456.730011 2 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/sicoob.py`](../../pycobranca/cnab/cnab400/sicoob.py) ·
fixture: [`tests/fixtures/remessa_sicoob_cnab400.rem`](../../tests/fixtures/remessa_sicoob_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | info da conta (agência + **DV agência** + convênio 9) · empresa(30) · `756` + `BANCOOBCED` · data (DDMMAA) · sequencial(7) |
| Detalhe (tipo 1) | tipo/CPF-CNPJ da empresa · agência + DV + conta + dígito · uso da empresa(25) · nosso número(12) + parcela(2) · modalidade da carteira + carteira(2) · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `756` + agência + DV · espécie · emissão · valor de mora(6)/multa(6) · distribuição do boleto · desconto/IOF/abatimento · sacado (doc/nome 40/endereço 37/bairro 15/CEP/cidade 15/UF) · sequencial(6) |
| Trailer (tipo 9) | `9` + 393 zeros + sequencial(6) |

**DV da agência:** módulo 11, mapa `{10: "0"}`.

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/sicoob.py`](../../pycobranca/cnab/cnab240/sicoob.py) ·
fixture: [`tests/fixtures/remessa_sicoob_cnab240.rem`](../../tests/fixtures/remessa_sicoob_cnab240.rem)

Estrutura em lotes (registros de 240 posições, CRLF, maiúsculas sem acentos). Versão do
layout de arquivo `081`, de lote `040`. `forma_cadastramento` = `0`.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `756` · CPF/CNPJ · convênio em brancos(20) · info da conta (agência 5 + **DV agência** + conta 12 + **DV conta**) · empresa(30) · `SICOOB` · data + hora + sequencial · versão `081` |
| Header de Lote (1) | serviço `01` · convênio do lote em brancos · info da conta · empresa · versão `040` |
| Segmento P | ocorrência · agência 5 + DV · conta 12 + DV · **nosso número(10) + parcela + modalidade + tipo de formulário** · vencimento (DDMMAAAA) · valor(15) · mora/desconto/IOF/abatimento · protesto |
| Segmento Q | dados do sacado (tipo/doc 15/nome 40/endereço 40/bairro 15/CEP/cidade 15/UF) · avalista |
| Segmento R | multa e data da multa (variante Sicoob, sempre emitido) |
| Trailer de Lote (5) | contadores + totais de títulos/valores |
| Trailer de Arquivo (9) | contadores de lotes/registros (variante Sicoob com `0*6` + brancos) |

**DVs (módulo 11):** agência `{10: "0"}`; conta `{10: "0"}`.
