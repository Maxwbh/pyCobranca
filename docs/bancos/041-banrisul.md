# Banrisul (041)

**Manuais oficiais de referência:** *Layout Cobrança CNAB 400 posições* · *Layout Cobrança
CNAB 240 posições* (Banrisul). Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) —
os PDFs não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/banrisul.py`](../../pycobranca/bancos/banrisul.py) ·
Dígito do banco: **8** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("041")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Campo livre com dígito duplo (módulo 10 + módulo 11, com regra de recálculo).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1 | Indicador do produto (carteira; `2` se ausente) |
| 2     | 1 | `1` (fixo) |
| 3–6   | 4 | Agência |
| 7–13  | 7 | Convênio (código do cedente) |
| 14–21 | 8 | Nosso número |
| 22–23 | 2 | `40` (constante) |
| 24–25 | 2 | Dígito duplo (módulo 10 + módulo 11) |

## Dígitos verificadores

- **Dígito duplo do campo livre** — calculado sobre as 23 posições anteriores: o **1º dígito**
  por módulo 10; o **2º** por módulo 11 (fatores `2..7`). Quando o 2º resulta em `1`, incrementa
  o 1º (`9→0`) e recalcula; DV final `11 - d2` (0 permanece 0).

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Convênio | 1–7 dígitos |
| Nosso número | 1–8 dígitos |
| Carteira | conjunto: 1, 2 |

## Formatos de exibição

- Nosso número: `nosso número(8)-dígito duplo` → `12345678-25`
- Agência/conta: `agência / convênio.dígito` → `0123 / 123456.7.0`

## Exemplo (saída da engine)

Entrada: agência `0123`, convênio `1234567`, carteira `2`, nosso número `12345678`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      2101231234567123456784094
Código de barras: 04198153900000127502101231234567123456784094
Linha digitável:  04192.10125 31234.567126 34567.840946 8 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/banrisul.py`](../../pycobranca/cnab/cnab400/banrisul.py) ·
fixture: [`tests/fixtures/remessa_banrisul_cnab400.rem`](../../tests/fixtures/remessa_banrisul_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA`) | código do cedente/convênio(13) · empresa(30) · `041` + `BANRISUL` · data (DDMMAA) |
| Detalhe (tipo 1) | código do cedente(13) · uso da empresa(25) · nosso número(8) + **dígito duplo(2)** · carteira · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `041` · espécie `08` · aceite `N` · emissão · 1ª instrução (`18` quando há multa) · tipo de mora · valor de mora(12) · desconto/IOF/abatimento · sacado (doc/nome 35/endereço 40) · percentual de multa(3) · CEP · cidade(15)/UF · dias de protesto · sequencial(6) |
| Trailer (tipo 9) | 26 brancos + total dos títulos(13) + brancos + sequencial(6) |

**Dígito duplo do nosso número:** primeiro dígito por módulo 10; segundo por módulo 11
(fatores 2..7). Quando o 2º resulta em `1`, incrementa o 1º (`9→0`) e recalcula; DV final
`11 - d2` (0 permanece 0). Cálculo de dígito duplo (módulo 10 + módulo 11).

**Tipo de mora `3`** (isento) → tipo em branco e valor de mora em brancos.
