# Banco do Nordeste (004)

**Manuais oficiais de referência:** *Cobrança Eletrônica BNB* · *Padrão BNB — CNAB 400*.
Fontes e portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos,
apenas citados.

**Implementação (boleto):** [`pycobranca/bancos/banco_nordeste.py`](../../pycobranca/bancos/banco_nordeste.py) ·
DV do nosso número: módulo 11 (fatores 2..8).

**Logo empacotado:** disponível via `logo_do_banco("004")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/banco_nordeste.py`](../../pycobranca/cnab/cnab400/banco_nordeste.py) ·
fixture: [`tests/fixtures/remessa_banco_nordeste_cnab400.rem`](../../tests/fixtures/remessa_banco_nordeste_cnab400.rem)

> **Quirk documentado:** o **registro detalhe tem 401 posições** — o layout do banco soma um
> caractere a mais em relação ao padrão FEBRABAN de 400 (header e trailer têm 400). Mantida a
> paridade byte a byte com os vetores de referência; por isso `tamanho_registro=None` e a garantia passa a
> ser a comparação com a fixture.

Estrutura do arquivo (CRLF, maiúsculas sem acentos):

| Registro | Tam. | Conteúdo principal |
|----------|:----:|--------------------|
| Header (`01REMESSA01COBRANCA`) | 400 | info da conta (agência 4 + `00` + conta 7 + dígito) · empresa(30) · `004` + `B.DO NORDESTE` · data (DDMMAA) |
| Detalhe (tipo 1) | **401** | agência + `00` + conta + dígito · 2 dígitos do percentual de multa · uso da empresa(25) · nosso número(7) + **DV** · código da carteira · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `004` · espécie `01` · aceite · emissão · mora/desconto/IOF/abatimento · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 15/UF) · avalista(40) · `99` + `0` · sequencial(6) |
| Trailer (tipo 9) | 400 | 393 brancos + sequencial(6) |

**DV do nosso número:** módulo 11 sobre o nosso número com 7 posições, fatores
`2..8`, bloco `11 - (soma % 11)`, mapa `{1: 0, 10: 0, 11: 0}`.

**Código da carteira:** carteira `51` → `I`; caso contrário, mapeado por emissão do boleto
(`1`/`2`) e carteira (`21`/`41`) → `1`/`2`/`4`/`5`.
