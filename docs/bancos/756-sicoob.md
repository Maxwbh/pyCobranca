# Sicoob (756)

**Manual oficial de referência:** *Manual de Layout Sicoob — Cobrança* (CNAB 400 e CNAB 240).
Fontes e portal (validador CNAB Sicoob) em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs
não são redistribuídos, apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/sicoob.py`](../../pycobranca/bancos/sicoob.py) ·
DV do nosso número com fatores fixos 3-1-9-7 (esquerda→direita).

**Logo empacotado:** disponível via `logo_do_banco("756")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/sicoob.py`](../../pycobranca/cnab/cnab400/sicoob.py) ·
fixture: [`tests/fixtures/remessa_sicoob_cnab400.rem`](../../tests/fixtures/remessa_sicoob_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | info da conta (agência + **DV agência** + convênio 9) · empresa(30) · `756` + `BANCOOBCED` · data (DDMMAA) · sequencial(7) |
| Detalhe (tipo 1) | tipo/CPF-CNPJ da empresa · agência + DV + conta + dígito · uso da empresa(25) · nosso número(12) + parcela(2) · modalidade da carteira + carteira(2) · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `756` + agência + DV · espécie · emissão · valor de mora(6)/multa(6) · distribuição do boleto · desconto/IOF/abatimento · sacado (doc/nome 40/endereço 37/bairro 15/CEP/cidade 15/UF) · sequencial(6) |
| Trailer (tipo 9) | `9` + 393 zeros + sequencial(6) |

**DV da agência:** módulo 11, mapa `{10: "0"}`.

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/sicoob.py`](../../pycobranca/cnab/cnab240/sicoob.py) ·
fixture: [`tests/fixtures/remessa_sicoob_cnab240.rem`](../../tests/fixtures/remessa_sicoob_cnab240.rem)

Estrutura em lotes (registros de 240 posições, CRLF, maiúsculas sem acentos). Versão do
layout de arquivo `081`, de lote `040`. `forma_cadastramento` = `0`.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `756` · CPF/CNPJ · convênio em brancos(20) · info da conta (agência 5 + **DV agência** + conta 12 + **DV conta**) · empresa(30) · `SICOOB` · data + hora + sequencial · versão `081` |
| Header de Lote (1) | serviço `01` · convênio do lote em brancos · info da conta · empresa · versão `040` |
| Segmento P | ocorrência · agência 5 + DV · conta 12 + DV · **nosso número(10) + parcela + modalidade + tipo de formulário** · vencimento (DDMMAAAA) · valor(15) · mora/desconto/IOF/abatimento · protesto |
| Segmento Q | dados do sacado (tipo/doc 15/nome 40/endereço 40/bairro 15/CEP/cidade 15/UF) · avalista |
| Segmento R | multa e data da multa (variante Sicoob, sempre emitido) |
| Trailer de Lote (5) | contadores + totais de títulos/valores |
| Trailer de Arquivo (9) | contadores de lotes/registros (variante Sicoob com `0*6` + brancos) |

**DVs (módulo 11):** agência `{10: "0"}`; conta `{10: "0"}`.
