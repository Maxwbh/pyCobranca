# Sicredi (748)

**Manuais oficiais de referência:** *Manual CNAB 240 — Cobrança Sicredi* (ago/2019) ·
*Manual CNAB 400 — Cobrança Sicredi* (ago/2019). Fontes e portal em
[`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/sicredi.py`](../../pycobranca/bancos/sicredi.py) ·
Ano + byte identificador no nosso número.

**Logo empacotado:** disponível via `logo_do_banco("748")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

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
