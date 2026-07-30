# Santander (033)

**Manuais oficiais de referência:** *H7800 — Layout de Cobrança 353/400 posições* (v2.33,
jun/2024) · *H7815 — Layout Cobrança CNAB 240 (Multibanco)* · *Layout de Código de Barras*
(v34, set/2021). Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são
redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/santander.py`](../../pycobranca/bancos/santander.py) ·
Dígito do banco: **7** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("033")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

Campo livre com IOS e código do cedente; DV do nosso número por módulo 11 (pesos 2..9,
resultado > 9 vira 0).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1  | `9` (fixo) |
| 2–8   | 7  | Código do cedente (convênio) |
| 9–20  | 12 | Nosso número (com zeros à esquerda) |
| 21    | 1  | DV do nosso número |
| 22    | 1  | `0` (IOS — seguros) |
| 23–25 | 3  | Carteira |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 (pesos 2..9): `DV = 11 - (soma % 11)`; resultados
  **maiores que 9 viram 0**. Zeros à esquerda não alteram o DV (o cálculo sobre 7 dígitos chega
  ao mesmo resultado).

## Carteiras suportadas

`101` (rápida com registro), `102` (sem registro), `121`.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Código do cedente | 1–7 dígitos (`convenio` ou, na falta, `conta`) |
| Nosso número | 1–12 dígitos |
| Carteira | conjunto: 101, 102, 121 |

## Formatos de exibição

- Nosso número: `nnnnnnnnnnnn-DV` → `000001234567-9`

O layout oficial do Santander define o nosso número impresso com **13 posições (12 dígitos +
DV)**: `000001234567-9`. O vetor de referência omite os zeros à esquerda (`1234567-9`) — diferença
**apenas cosmética**; o código de barras é idêntico nos dois sistemas. A PyCobrança segue o
manual oficial.

## Exemplo validado (por vetores de referência ✓)

Entrada: código do cedente `3300123`, carteira `101`, nosso número `1234567`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      9330012300000123456790101
Código de barras: 03396153900000127509330012300000123456790101
Linha digitável:  03399.33004 12300.000127 34567.901011 6 15390000012750
```

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/santander.py`](../../pycobranca/cnab/cnab400/santander.py) ·
fixture: [`tests/fixtures/remessa_santander_cnab400.rem`](../../tests/fixtures/remessa_santander_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | código de transmissão(20) · empresa(30) · `033` + `SANTANDER` · data (DDMMAA) · 16 zeros · complemento · `058` + `000001` |
| Detalhe (tipo 1) | tipo/CPF-CNPJ da empresa · código de transmissão(20) · uso da empresa(25) · nosso número(8) · 2º desconto · **código/percentual de multa** · data da multa · código da carteira · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `033` · espécie · aceite · emissão · instruções · mora/desconto/IOF/abatimento · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 15/UF) · avalista(30) · complemento de conta (padrão novo) · dias de protesto |
| Trailer (tipo 9) | sequencial(6) + total dos títulos(13) + zeros + sequencial(6) |

Código de transmissão preenchido à esquerda com zeros (20). Conta “padrão novo” (>8 dígitos)
preenche o identificador de movimento (`I` + dígito + DV).

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/santander.py`](../../pycobranca/cnab/cnab240/santander.py) ·
fixture: [`tests/fixtures/remessa_santander_cnab240.rem`](../../tests/fixtures/remessa_santander_cnab240.rem)

Estrutura em lotes (versão de arquivo `040`, de lote `030`). Header de arquivo e segmentos
P/Q são customizados.

> **Quirk documentado:** o **segmento P é emitido com 241 posições** (mantida a paridade byte
> a byte com os vetores de referência — o desvio do padrão FEBRABAN de 240 vem do layout do banco).
> Por isso `tamanho_registro=None` e a garantia passa a ser a comparação com a fixture.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `033` · CPF/CNPJ(15) · código de transmissão(15) · empresa(30) · `BANCO SANTANDER` · data + sequencial · versão `040`; densidade e hora em brancos |
| Header de Lote (1) | serviço `01` · código de transmissão no convênio do lote · empresa · versão `030` |
| Segmento P (**241**) | ocorrência · agência 4 + **DV agência** · conta 9 + dígito (duas vezes) · **identificador do título** (nosso número + DV mód. 11 fatores 2..9, 13 pos.) · vencimento (DDMMAAAA) · valor(15) · espécie `02` · mora/desconto/IOF/abatimento · protesto · baixa |
| Segmento Q | dados do sacado + avalista |
| Trailers de Lote (5) e de Arquivo (9) | contadores |

**DV agência:** módulo 11 com mapa `{10: "X", 11: "X"}`. **DV do título:** módulo 11
fatores 2..9, `{10: 0, 11: 0}`.
