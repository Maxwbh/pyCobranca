# Sicredi (748)

**Manuais oficiais de referência:** *Manual CNAB 240 — Cobrança Sicredi* (ago/2019) ·
*Manual CNAB 400 — Cobrança Sicredi* (ago/2019). Fontes e portal em
[`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/sicredi.py`](../../pycobranca/bancos/sicredi.py) ·
Dígito do banco: **X** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("748")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Nosso número com ano (AA) e byte identificador (1=agência, 2-9=beneficiário).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1 | Carteira |
| 2     | 1 | `1` (fixo) |
| 3–4   | 2 | Ano (2 últimos dígitos da data do documento) |
| 5     | 1 | Byte de identificação (1=agência, 2–9=beneficiário) |
| 6–10  | 5 | Nosso número |
| 11    | 1 | DV do nosso número (módulo 11) |
| 12–15 | 4 | Agência |
| 16–17 | 2 | Posto |
| 18–22 | 5 | Convênio (código do beneficiário) |
| 23–24 | 2 | `10` (constante) |
| 25    | 1 | DV do campo livre (módulo 11) |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 sobre `agência(4) + posto(2) + convênio(5) + ano(2) +
  byte(1) + nosso número(5)` (pesos `9..2` cíclicos, direita→esquerda), `DV = soma % 11`;
  resultados **10 e 11 viram 0**.
- **DV do campo livre** — módulo 11 sobre as 24 primeiras posições do campo livre, mesmos
  parâmetros.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Posto | até 2 dígitos (opcional) |
| Convênio | 1–5 dígitos |
| Nosso número | 1–5 dígitos |
| Carteira | conjunto: 1, 3 |

## Formatos de exibição

- Nosso número: `AA/Bnnnnn-DV` (AA = ano, B = byte identificador) → `26/212345-8`
- Agência/conta: `agência(4).posto(2).convênio(5)` → `0165.07.12345`

## Exemplo (saída da engine)

Entrada: agência `0123`, posto `04`, convênio `12345`, byte identificador `2`, nosso número
`12345`, carteira `1`, data do documento e vencimento 15/08/2026, R$ 127,50.

```
Campo livre:      1126212345001230412345109
Código de barras: 74891153900000127501126212345001230412345109
Linha digitável:  74891.12628 12345.001239 04123.451090 1 15390000012750
```

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/sicredi.py`](../../pycobranca/cnab/cnab240/sicredi.py) ·
fixture: [`tests/fixtures/remessa_sicredi_cnab240.rem`](../../tests/fixtures/remessa_sicredi_cnab240.rem)

Estrutura em lotes (registros de 240 posições, CRLF, maiúsculas sem acentos). Versão do
layout de arquivo `081`, de lote `040`. Densidade `01600`, espécie `03`,
`forma_cadastramento` = `1`, `tipo_documento` = `1`.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `748` · CPF/CNPJ · convênio em brancos(20) · info da conta (agência 5 + DV branco + conta 12 + dígito) · empresa(30) · `SICREDI` · data + hora + sequencial · versão `081` |
| Header de Lote (1) | serviço `01` · convênio do lote em brancos · info da conta · empresa · versão `040` |
| Segmento P | ocorrência · agência 5 · conta 12 + dígito · **nosso número** (ljust 20) · vencimento (DDMMAAAA) · valor(15) · espécie `03` · mora/desconto (`1`)/IOF/abatimento · protesto · baixa (`1` / `060`) |
| Segmento Q | dados do sacado (tipo/doc 15/nome 40/endereço 40/bairro 15/CEP/cidade 15/UF) · avalista |
| Segmento R | multa e data da multa |
| Trailer de Lote (5) | contadores (complemento com 4 blocos de 23 zeros) |
| Trailer de Arquivo (9) | contadores de lotes/registros (variante Sicredi com `0*6` + brancos) |

**Observações:** `data_mora` usa **vencimento + 1 dia**; código de desconto e de baixa fixos em
`1`; agência sem DV (branco). O CNAB 240 da **Unicred (136)** herda este mesmo layout — ver
[`136-unicred.md`](136-unicred.md).
