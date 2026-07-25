# Banrisul (041)

**Manuais oficiais de referência:** *Layout Cobrança CNAB 400 posições* · *Layout Cobrança
CNAB 240 posições* (Banrisul). Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) —
os PDFs não são redistribuídos, apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/banrisul.py`](../../pycobranca/bancos/banrisul.py) ·
DV do nosso número: **dígito duplo** (módulo 10 + módulo 11) com regra de recálculo.

**Logo empacotado:** disponível via `logo_do_banco("041")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

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
