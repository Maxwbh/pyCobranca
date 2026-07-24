# Ailos (085)

**Manual oficial de referência:** *Manual Técnico de Cobrança Bancária — 240 Posições* (Ailos).
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/ailos.py`](../../pycobranca/bancos/ailos.py) ·
Conta com DV (7+1) + nosso número 9.

**Logo empacotado:** disponível via `logo_do_banco("085")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

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
