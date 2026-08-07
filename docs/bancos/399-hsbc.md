---
description: >-
  Boleto HSBC (399) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (CNR, CSB). Somente emissão de boleto — este banco não tem remessa CNAB.
---

# HSBC (399)

**Manuais oficiais de referência:** *Layout de Cobrança HSBC* (carteiras CNR e CSB). Fontes e
portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas
citados.

**Implementação:** [`pycobranca/bancos/hsbc.py`](../../pycobranca/bancos/hsbc.py) ·
Dígito do banco: **9** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("399")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Legado. Carteira CNR usa data juliana no campo livre; carteira CSB é o layout padrão.

## Campo livre (posições 20–44 do código de barras)

**Carteira CNR** (com data juliana):

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–7   | 7 | Conta |
| 8–20  | 13 | Nosso número |
| 21–24 | 4 | Data juliana do vencimento (dias do ano + último dígito do ano) |
| 25    | 1 | `2` (constante) |

**Carteira CSB** (layout padrão): nosso número(13) + agência(4) + conta(7) + `001`.

## Dígitos verificadores

- **Carteira CNR** — o nosso número exibido carrega dois dígitos calculados em
  `nosso_numero_formatado()`: o 1º é `modulo11_flex` do nosso número de 13 posições (fatores 9..2
  cíclicos, direita→esquerda; resto `10` → `0`), seguido da constante `4`; o 2º é o módulo 11
  (mesmo mapa `10 → 0`) da soma de `parte1 + conta + data (DDMMAA)`.
- **Carteira CSB** — o nosso número não recebe dígito adicional (13 posições diretas).

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Conta | 1–7 dígitos |
| Nosso número | 1–13 dígitos |
| Carteira | conjunto: CNR, CSB |

## Formatos de exibição

- Nosso número (CNR): `1234567890123046`
- Agência/conta: `1234 / 1234567`

## Exemplo (saída da engine)

Entrada: carteira `CNR`, agência `1234`, conta `1234567`, nosso número `1234567890123`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      1234567123456789012322762
Código de barras: 39999153900000127501234567123456789012322762
Linha digitável:  39991.23452 67123.456781 90123.227622 9 15390000012750
```
