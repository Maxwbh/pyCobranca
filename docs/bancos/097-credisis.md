# CrediSIS (097)

**Manual oficial de referência:** *Layout de Cobrança CNAB 400 — CrediSIS*. Sem manual público
localizado — layout portado por **paridade byte a byte** com os vetores de referência; ver
[`fontes-oficiais.md`](fontes-oficiais.md).

**Implementação (boleto):** [`pycobranca/bancos/credisis.py`](../../pycobranca/bancos/credisis.py) ·
DV do documento do cedente no campo livre.

## Resumo

Campo livre com o DV do documento do cedente.

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–8   | 8 | `00000097` (zeros + código do banco) |
| 9     | 1 | DV do documento do cedente (módulo 11) |
| 10–13 | 4 | Agência |
| 14–19 | 6 | Convênio |
| 20–25 | 6 | Nosso número |

## Dígitos verificadores

- **DV do documento do cedente** — módulo 11 sobre o CPF/CNPJ do cedente (só dígitos), pesos
  `9..2` cíclicos (direita→esquerda), `DV = soma % 11`; resultados **0, 10 e 11 viram 1**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Convênio | 1–6 dígitos |
| Nosso número | 1–6 dígitos |
| Carteira | conjunto: 18 |

## Formatos de exibição

- Nosso número: `097 + DV do documento do cedente + agência(4) + convênio(6) + nosso número(6)`
  (via `nosso_numero_formatado()`)
- Agência/conta: `agência / conta` (formato padrão da base)

## Exemplo (saída da engine)

Entrada: documento do cedente `11.222.333/0001-81` (CNPJ válido), agência `0123`, convênio
`123456`, nosso número `123456`, carteira `18`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      0000009780123123456123456
Código de barras: 09791153900000127500000009780123123456123456
Linha digitável:  09790.00007 09780.123122 34561.234567 1 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/credisis.py`](../../pycobranca/cnab/cnab400/credisis.py) ·
fixture: [`tests/fixtures/remessa_credisis_cnab400.rem`](../../tests/fixtures/remessa_credisis_cnab400.rem)

> **Quirk documentado:** o **registro detalhe tem 402 posições** (header e trailer têm 400) —
> conforme o layout do banco. Mantida a paridade byte a byte; por isso
> `tamanho_registro=None`.

Estrutura do arquivo (CRLF, maiúsculas sem acentos):

| Registro | Tam. | Conteúdo principal |
|----------|:----:|--------------------|
| Header (`01REMESSA01COBRANCA`) | 400 | info da conta (agência 4 + espaço + conta 8 + dígito) · empresa(30) · `097` + `CENTRALCRED` · data (DDMMAA) · sequencial(7) |
| Detalhe (tipo 1) | **402** | tipo/CPF-CNPJ da empresa · agência(4) + conta(8) + dígito · uso da empresa(25) · **nosso número** (`0` + código do cedente 4 + nosso número 6) · nº documento(10) · vencimento (DDMMAA) · valor(13) · emissão · valor de mora(6) · percentual de multa(6) · desconto · sacado (doc/nome 40/endereço 37/bairro 15/CEP/cidade 15/UF) · avalista(25) · dias de protesto · sequencial(6) |
| Trailer (tipo 9) | 400 | 393 brancos + sequencial(6) |

**Nosso número:** `0` + código do cedente(4) + nosso número(6, zeros à esquerda).
