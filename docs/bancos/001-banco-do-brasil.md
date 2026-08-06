---
description: >-
  Boleto Banco do Brasil (001) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (11, 12, 15, 16, 17, 18, 31, 51). Remessa e retorno CNAB 400 e 240. Suporta PIX/Bolepix.
---

# Banco do Brasil (001)

**Manuais oficiais de referência:** *Especificação de Boleto de Cobrança* (BB, jan/2016) ·
*CNAB 240 — Cobrança* (BB, ago/2017) · *Layout FEBRABAN 240 posições*. Fontes e portal em
[`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/banco_do_brasil.py`](../../pycobranca/bancos/banco_do_brasil.py) ·
Dígito do banco: **9** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("001")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Convênios 4/6/7; no convênio 7 o nosso número tem 17 dígitos (convênio + sequencial, sem DV).

## Campo livre (posições 20–44 do código de barras)

| Convênio | Layout do campo livre (25) | Sequencial |
|:--------:|-----------------------------|:----------:|
| **7 dígitos** (padrão atual) | `000000` + convênio(7) + sequencial(10) + carteira(2) | 10 |
| **6 dígitos** | convênio(6) + sequencial(5) + agência(4) + conta(8) + carteira(2) | 5 |
| **4 dígitos** | convênio(4) + sequencial(7) + agência(4) + conta(8) + carteira(2) | 7 |

No convênio de 7 dígitos o **nosso número tem 17 posições** (convênio + sequencial), sem DV no
campo livre.

## Dígitos verificadores

- **Nosso número:** no convênio de 7 dígitos (17 posições) **não há DV** embutido no campo livre;
  nos convênios de 4/6 dígitos o sequencial também entra sem DV no campo livre.
- O **DV geral do código de barras** (posição 5) é o módulo 11 padrão sobre as 43 posições —
  calculado igual para todos os bancos.

## Carteiras suportadas

`11, 12, 15, 16, 17, 18, 31, 51`.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Convênio | 4, 6 ou 7 dígitos |
| Nosso número | máximo conforme convênio: conv7→10, conv6→5, conv4→7 |
| Agência | até 4 dígitos (só convênios 4 e 6) |
| Conta | até 8 dígitos (só convênios 4 e 6) |
| Carteira | conjunto: 11, 12, 15, 16, 17, 18, 31, 51 |

## Formatos de exibição

- Nosso número (convênio 7): `convênio + sequencial` → `12345670000000123`.

## Exemplo validado (por vetores de referência ✓)

Entrada: convênio `1234567`, nosso número `123`, carteira `18`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      0000001234567000000012318
Código de barras: 00199153900000127500000001234567000000012318
Linha digitável:  00190.00009 01234.567004 00000.123182 9 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/banco_brasil.py`](../../pycobranca/cnab/cnab400/banco_brasil.py) ·
fixture: [`tests/fixtures/remessa_banco_brasil_cnab400.rem`](../../tests/fixtures/remessa_banco_brasil_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | info da conta (agência + **DV agência** + conta 8 + **DV conta** + `000000`) · empresa(30) · `001` + `BANCODOBRASIL` · data (DDMMAA) · sequencial de remessa(7) + convênio líder(7) |
| Detalhe (tipo 7) | tipo/CPF-CNPJ da empresa · agência + DV + conta 8 + DV · convênio(7) · uso da empresa(25) · convênio(7) + nosso número(10) · variação da carteira(3) · carteira(2) · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `001` · espécie · aceite · emissão · instruções(2+2) · mora/desconto/IOF/abatimento · sacado (doc/nome 37/endereço 40/bairro 12/CEP/cidade 15/UF) · dias de protesto |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

**DVs (módulo 11):** agência com mapa `{10: "X"}`; conta com mapa `{10: "X"}`.

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/banco_brasil.py`](../../pycobranca/cnab/cnab240/banco_brasil.py) ·
fixture: [`tests/fixtures/remessa_banco_brasil_cnab240.rem`](../../tests/fixtures/remessa_banco_brasil_cnab240.rem)

Estrutura em lotes (registros de 240 posições, CRLF, maiúsculas sem acentos). Versão do
layout de arquivo `083`, de lote `042`. `data_geracao_fixa`/`hora_geracao_fixa` tornam a
geração determinística.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `001` · CPF/CNPJ · código do convênio (convênio 9 + `0014` + carteira 2 + variação 3) · info da conta (agência 5 + DV + conta 12 + DV) · empresa(30) · `BANCO DO BRASIL S.A.` · data + hora + sequencial(6) · versão `083` |
| Header de Lote (1) | tipo de operação `R`/serviço `01` · convênio do lote (igual ao do arquivo) · info da conta · empresa(30) · mensagens(40+40) · versão `042` |
| Segmento P | ocorrência · agência 5 + DV · conta 12 + DV · **identificador do título** (convênio + nosso número com DV) · carteira `7` · vencimento (DDMMAAAA) · valor(15) · espécie `02` · emissão · mora/desconto/IOF/abatimento · protesto |
| Segmento Q | dados do sacado (tipo/doc 15/nome 40/endereço 40/bairro 15/CEP/cidade 15/UF) · avalista |
| Trailers de Lote (5) e de Arquivo (9) | contadores de registros/lotes |

**Nosso número (módulo 11 BB por convênio):** convênio de 7 dígitos → 10 posições sem DV;
convênios de 4/6 dígitos → 7/5 posições + DV `{10: "X"}`. **DV agência/conta** módulo 11
`{10: "X"}`.
