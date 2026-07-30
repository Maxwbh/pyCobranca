# Ailos (085)

**Manual oficial de referência:** *Manual Técnico de Cobrança Bancária — 240 Posições* (Ailos).
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/ailos.py`](../../pycobranca/bancos/ailos.py) ·
Conta com DV (7+1) + nosso número 9.

**Logo empacotado:** disponível via `logo_do_banco("085")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Conta com dígito verificador (7+1) e nosso número de 9 dígitos.

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–6   | 6 | Convênio |
| 7–13  | 7 | Conta |
| 14    | 1 | DV da conta (módulo 11) |
| 15–23 | 9 | Nosso número |
| 24–25 | 2 | Carteira |

## Dígitos verificadores

- **DV da conta** — módulo 11 sobre a conta com 7 posições (pesos `9..2` cíclicos,
  direita→esquerda), `DV = soma % 11`; resultado **10 vira 0**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Convênio | 1–6 dígitos |
| Conta | 1–7 dígitos |
| Nosso número | 1–9 dígitos |
| Carteira | conjunto: 01, 1 |

## Formatos de exibição

- Nosso número: `conta(7) + DV da conta + nosso número(9)` (via `nosso_numero_formatado()`)
- Agência/conta: `agência / conta` (formato padrão da base)

## Exemplo (saída da engine)

Entrada: convênio `123456`, conta `0012345`, nosso número `123456789`, carteira `01`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      1234560012345512345678901
Código de barras: 08596153900000127501234560012345512345678901
Linha digitável:  08591.23457 60012.345512 23456.789017 6 15390000012750
```

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/ailos.py`](../../pycobranca/cnab/cnab240/ailos.py) ·
fixture: [`tests/fixtures/remessa_ailos_cnab240.rem`](../../tests/fixtures/remessa_ailos_cnab240.rem)

Estrutura em lotes (registros de 240 posições, CRLF, maiúsculas sem acentos). Versão do
layout de arquivo `087`, de lote `045`. `forma_cadastramento` = `0`, `tipo_documento` = `1`.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `085` · CPF/CNPJ · convênio(6, ljust 20) · info da conta (agência 5 + DV + conta 12 + **DV conta**) · empresa(30) · `AILOS` · data + hora + sequencial · versão `087` |
| Header de Lote (1) | serviço `01` · convênio do lote · info da conta · empresa · versão `045` |
| Segmento P | ocorrência · agência 5 + DV · conta 12 + DV · **nosso número ajustado** (conta + DV conta + nosso número 9) · vencimento (DDMMAAAA) · valor(15) · mora/desconto/IOF/abatimento · uso da empresa (documento, 25) · protesto · baixa (`2` / branco) |
| Segmento Q | dados do sacado (tipo/doc 15/nome 40/endereço 40/bairro 15/CEP/cidade 15/UF) · avalista |
| Segmento R | **emitido somente quando há multa** (`codigo_multa ≠ 0`) — multa e data da multa |
| Trailers de Lote (5) e de Arquivo (9) | contadores; trailer de lote inclui totais de títulos/valores |

**DV da conta:** módulo 11 sobre a conta de 7 posições, mapa `{10: 0}`.

**Segmento R condicional:** `total_segmentos()` conta 2 registros por pagamento sem multa e 3
com multa; `monta_segmento_r` retorna `None` quando não há multa, mantendo a contagem correta.
