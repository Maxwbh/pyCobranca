# Safra (422)

**Manuais oficiais de referência:** *Layout de Cobrança Safra*. Fontes e portal em
[`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/safra.py`](../../pycobranca/bancos/safra.py) ·
Dígito do banco: **7** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("422")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DV do nosso número calculado da esquerda para a direita (mapa 10→0, 11→1).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1 | `7` (constante) |
| 2–5   | 4 | Agência |
| 6     | 1 | Dígito da agência |
| 7–14  | 8 | Conta |
| 15    | 1 | Dígito da conta |
| 16–23 | 8 | Nosso número |
| 24    | 1 | DV do nosso número |
| 25    | 1 | `2` (constante) |

## Dígitos verificadores

- **DV do nosso número**: módulo 11 sobre o nosso número de 8 posições, percorrido **da esquerda
  para a direita** (`da_direita=False`), fatores 9..2 cíclicos. O DV é `11 - (soma % 11)`, com o
  mapa final `10 → 0` e `11 → 1`.

Os dígitos de agência e conta (`digito_agencia`/`digito_conta`) são informados pelo beneficiário e
são obrigatórios para montar o campo livre.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Conta | 1–8 dígitos |
| Nosso número | 1–8 dígitos |
| Carteira | conjunto: 1, 2 |

## Formatos de exibição

- Nosso número: `nosso_numero-DV` → `12345678-9`
- Agência/conta: `01234 / 000123456`

## Exemplo (saída da engine)

Entrada: agência `0123`, dígito da agência `4`, conta `00012345`, dígito da conta `6`, carteira `1`,
nosso número `12345678`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      7012340001234561234567892
Código de barras: 42291153900000127507012340001234561234567892
Linha digitável:  42297.01232 40001.234562 12345.678929 1 15390000012750
```
