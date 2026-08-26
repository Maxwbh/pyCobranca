---
description: >-
  Boleto Banestes (021) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (11, 13). Somente emissão de boleto — este banco não tem remessa CNAB.
---

# Banestes (021)

**Manuais oficiais de referência:** *Layout de Cobrança Banestes*. Fontes e portal em
[`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/banestes.py`](../../pycobranca/bancos/banestes.py) ·
Dígito do banco: **3** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("021")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DV duplo no nosso número (módulo 11 aplicado duas vezes) e dígito duplo no campo livre.

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–8   | 8 | Nosso número |
| 9–18  | 10 | Conta |
| 19    | 1 | Dígito da conta |
| 20    | 1 | Variação (1ª posição; padrão `2`) |
| 21–23 | 3 | `021` (constante) |
| 24–25 | 2 | Dígito duplo (módulo 10 + módulo 11) do bloco 1–23 |

## Dígitos verificadores

- **DV do nosso número** (2 dígitos): módulo 11 aplicado duas vezes sobre o nosso número de
  8 posições. O 1º dígito é `modulo11_flex` do nosso número (fatores 9..2 cíclicos, direita→
  esquerda; resto `10`/`11` → `0`); o 2º é o mesmo módulo 11 aplicado a `nosso número + 1º dígito`.
- **Dígito duplo do campo livre** (2 dígitos, posições 24–25): `duplo_digito` do bloco das
  posições 1–23. O 1º dígito é módulo 10; o 2º é módulo 11 (fatores 2..7) e, quando resulta em `1`,
  incrementa o 1º dígito (`9→0`) e recalcula; o DV final é `11 - d2` (0 permanece 0).

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Conta | 1–10 dígitos |
| Dígito da conta | 1 dígito — entra no campo livre em 1 posição |
| Nosso número | 1–8 dígitos |
| Variação | 1 posição no campo livre, `2` quando ausente (o excedente é cortado) |
| Carteira | conjunto: 11, 13 |

## Formatos de exibição

- Nosso número: `nosso_numero-DVduplo` → `12345678-97`
- Agência/conta: `138 / 12345670`

## Exemplo (saída da engine)

Entrada: agência `0138`, conta `0001234567`, dígito da conta `0`, variação `2`, carteira `11`,
nosso número `12345678`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      1234567800012345670202199
Código de barras: 02195153900000127501234567800012345670202199
Linha digitável:  02191.23452 67800.012345 56702.021991 5 15390000012750
```
