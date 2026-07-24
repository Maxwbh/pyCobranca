# Bradesco (237)

**Manuais oficiais de referência:** *Especificação de Boleto de Cobrança* (Bradesco, ago/2015) ·
*Layout CNAB 240 posições* · *Layout CNAB 400 posições* (layout do boleto e DV do nosso número).
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação:** [`pycobranca/bancos/bradesco.py`](../../pycobranca/bancos/bradesco.py) ·
Dígito do banco: **2** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("237")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Campo livre (25 posições)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–4   | 4  | Agência |
| 5–6   | 2  | Carteira |
| 7–17  | 11 | Nosso número |
| 18–24 | 7  | Conta |
| 25    | 1  | `0` |

## DV do nosso número — módulo 11 **base 7**

Sobre `carteira(2) + nosso número(11)`, pesos cíclicos 2..7 da direita para a esquerda:

| Resto | DV |
|:-----:|:--:|
| 0 | `0` |
| 1 | `P` |
| demais | `11 - resto` |

## Carteiras suportadas

`03, 06, 09, 19, 21, 22, 25, 26`.

## Formatos de exibição

- Nosso número: `carteira/nosso_numero-DV` → `06/00000000002-9`.

## Exemplo validado (por vetores de referência ✓)

Entrada: agência `1234`, conta `56789`, carteira `06`, nosso número `2`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      1234060000000000200567890
Código de barras: 23799153900000127501234060000000000200567890
Linha digitável:  23791.23405 60000.000004 02005.678905 9 15390000012750
DV nosso número:  "0600000000002" → soma 46 → resto 2 → DV 9
```


## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/bradesco.py`](../../pycobranca/cnab/cnab400/bradesco.py) ·
fixture: [`tests/fixtures/remessa_bradesco_cnab400.rem`](../../tests/fixtures/remessa_bradesco_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header | código da empresa(20) · empresa(30) · `237` + `BRADESCO` · data · `MX` + sequencial de remessa(7) |
| Detalhe (tipo 1) | identificação da empresa (`0`+carteira 3+agência 5+conta 7+DV) · nº controle(25) · multa · nosso número(11) + **DV base 7** (`P`/`0`) · condição de emissão `2`/`N` · ocorrência · nº documento(10) · vencimento · valor(13) · espécie `01` · emissão · mora/desconto/IOF/abatimento · sacado (doc/nome 40/**endereço composto com cidade/UF** 40) · CEP (5+3) |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

A geração é **byte a byte idêntica** aos vetores de referência para os mesmos dados (fixture congelada).
