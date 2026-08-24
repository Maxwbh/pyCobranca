---
description: >-
  Boleto Itaú (341) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (104, 109, 112, 115, 175, 177, 188). Remessa e retorno CNAB 400. Suporta PIX/Bolepix.
---

# Itaú (341)

**Manuais oficiais de referência:** *Especificação de Boleto de Cobrança* (Itaú, mar/2015) ·
*Layout Cobrança CNAB 400 bytes* · *Layout Cobrança CNAB 240* (cálculo de DAC e campo livre).
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação:** [`pycobranca/bancos/itau.py`](../../pycobranca/bancos/itau.py) ·
Dígito do banco: **7** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("341")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DACs por módulo 10 (um para agência/conta/carteira/nosso número e outro para agência/conta).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–3   | 3 | Carteira |
| 4–11  | 8 | Nosso número |
| 12    | 1 | DAC [agência/conta/carteira/nosso número] (módulo 10) |
| 13–16 | 4 | Agência |
| 17–21 | 5 | Conta |
| 22    | 1 | DAC [agência/conta] (módulo 10) |
| 23–25 | 3 | `000` |

## Dígitos verificadores

- **DAC conta**: módulo 10 de `agência(4) + conta(5)`.
- **DAC nosso número**: módulo 10, e **a composição muda conforme a carteira**.

O manual (*Cobrança CNAB 400*, jan/2017, nota 23) manda usar
`agência(4) + conta(5) + carteira(3) + nosso número(8)`, *"exceto as carteiras escriturais e na
modalidade direta as carteiras 126, 131, 145, 150 e 168, cujo DAC do 'Nosso Número' é composto
apenas dos campos: Carteira e Nosso Número"*.

| Carteira | Modalidade (nota 5 do manual) | Composição do DAC |
|:--:|---|---|
| 104 | Escritural eletrônica – carnê | `carteira + nosso número` |
| **112** | **Escritural eletrônica – simples** | `carteira + nosso número` |
| 115 | Escritural eletrônica – simples, faixa livre | `carteira + nosso número` |
| 188 | Escritural eletrônica – cobrança inteligente (B2B) | `carteira + nosso número` |
| 109 | Direta eletrônica sem emissão – simples | `agência + conta + carteira + nosso número` |
| 175, 177 | não constam na tabela do manual de 2017 | `agência + conta + carteira + nosso número` |

!!! warning "Corrigido na 1.1.1"
    Até a 1.1.0 a composição longa era aplicada às sete carteiras. Nas quatro escriturais isso
    produzia um código de barras **estruturalmente válido com o dígito errado** — o boleto imprime
    e o banco recusa ou credita em outro título. Reportado na
    [issue #40](https://github.com/Maxwbh/pyCobranca/issues/40), com conferência contra boletos
    emitidos pelo próprio Itaú.

O manual se contradiz num número: a nota 23 lista `145` e o anexo 4 lista `146`. Nenhuma das duas
está entre as carteiras aceitas aqui; ambas ficam na composição curta até que um vetor de
referência decida.

## Carteiras suportadas

`104, 109, 112, 115, 175, 177, 188`. As carteiras de nosso número com 15 posições
(107, 122, 142, 143, 196 e 198) têm código de barras próprio — fora do escopo atual.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Conta | 1–5 dígitos |
| Nosso número | 1–8 dígitos |
| Carteira | conjunto: 104, 109, 112, 115, 175, 177, 188 |

## Formatos de exibição

- Nosso número: `carteira/nosso_numero-DAC` → `109/12345678-0`
- Agência/conta: `0057 / 12345-7`

## Exemplo validado (por vetores de referência ✓)

Entrada: agência `0057`, conta `12345`, carteira `109`, nosso número `12345678`,
R$ 127,50, vencimento 15/08/2026.

```
Campo livre:     1091234567800057123457000
Código de barras: 34195153900000127501091234567800057123457000
Linha digitável:  34191.09123 34567.800056 71234.570001 5 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/itau.py`](../../pycobranca/cnab/cnab400/itau.py) ·
fixture: [`tests/fixtures/remessa_itau_cnab400.rem`](../../tests/fixtures/remessa_itau_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | agência + `00` + conta + DAC · empresa(30) · `341` + `BANCO ITAU SA` · data (DDMMAA) |
| Detalhe (tipo 1) | tipo/CPF-CNPJ da empresa · agência/conta/DAC · uso da empresa(25) · nosso número(8) · carteira · código da carteira (`I`/`U`/`1`/`E`) · ocorrência · nº documento(10) · vencimento · valor(13) · espécie · aceite · emissão · instruções · mora/desconto/IOF/abatimento · sacado (doc/nome 30/endereço 40/bairro 12/CEP/cidade 15/UF) · avalista(30) · prazo de instrução |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

A geração é **byte a byte idêntica** aos vetores de referência para os mesmos dados (fixture congelada).
