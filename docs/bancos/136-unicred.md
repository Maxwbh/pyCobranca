# Unicred (136)

**Manual oficial de referência:** *Manual de Cobrança Unicred* (leiautes CNAB 240 e CNAB 400).
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/unicred.py`](../../pycobranca/bancos/unicred.py) ·
Conta 9 + DV informado.

**Logo empacotado:** disponível via `logo_do_banco("136")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/unicred.py`](../../pycobranca/cnab/cnab400/unicred.py) ·
fixture: [`tests/fixtures/remessa_unicred_cnab400.rem`](../../tests/fixtures/remessa_unicred_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | código do beneficiário(20) · empresa(30) · `136` + `UNICRED` · data (DDMMAA) · `000` + sequencial(7) |
| Detalhe (tipo 1) | agência(5) + **DV agência** · conta(12) + **DV conta** · carteira(3) · `136` · código/percentual de multa · tipo de mora · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · desconto · emissão · protesto/dias · valor de mora(13) · data/valor de desconto · **nosso número(10) + DV** · abatimento(13) · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 20/UF) · avalista(38) · sequencial(6) |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

**DVs (módulo 11):** agência `{10: "X"}`; conta de 5 posições `{10: 0}`; nosso
número de 10 posições `{10: 0, 11: 0}`.

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/unicred.py`](../../pycobranca/cnab/cnab240/unicred.py) ·
fixture: [`tests/fixtures/remessa_unicred_cnab240.rem`](../../tests/fixtures/remessa_unicred_cnab240.rem)

O CNAB 240 da Unicred **reaproveita integralmente o layout do Sicredi** (mesma cooperativa de
tecnologia) — a classe
`RemessaUnicred240` herda de `RemessaSicredi240` sem alterações. Consulte
[`748-sicredi.md`](748-sicredi.md) para a composição de header de arquivo/lote, segmentos
P/Q/R e trailers (versão de arquivo `081`, de lote `040`, espécie `03`).
