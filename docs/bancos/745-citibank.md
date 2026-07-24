# Citibank (745)

**Manual oficial de referência:** *Layout de Cobrança CNAB 400 — Citibank*. Sem manual público
localizado — layout portado por **paridade byte a byte** com os vetores de referência; ver
[`fontes-oficiais.md`](fontes-oficiais.md).

**Implementação (boleto):** [`pycobranca/bancos/citibank.py`](../../pycobranca/bancos/citibank.py) ·
Portfólio + convênio sem o 1º dígito.

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/citibank.py`](../../pycobranca/cnab/cnab400/citibank.py) ·
fixture: [`tests/fixtures/remessa_citibank_cnab400.rem`](../../tests/fixtures/remessa_citibank_cnab400.rem)

Estrutura do arquivo (registros de 400 posições, CRLF, maiúsculas sem acentos):

| Registro | Conteúdo principal |
|----------|--------------------|
| Header (`01REMESSA01COBRANCA`) | portfólio(20) · empresa(30) · `745` + `CITIBANK` · data (DDMMAA) · complemento `01600BPI` |
| Detalhe (tipo 1) | tipo/CPF-CNPJ da empresa · portfólio(20) · uso da empresa(25) · espécie · nosso número(12) · 2º desconto (data/valor) · carteira · ocorrência · nº documento(10) · vencimento (DDMMAA) · valor(13) · `745` · espécie `07` · aceite · emissão · mora/desconto/IOF/abatimento · sacado (doc/nome 40/endereço 40/bairro 12/CEP/cidade 15/UF) · avalista(40) · `9` · sequencial(6) |
| Trailer (tipo 9) | 393 brancos + sequencial(6) |

**Portfólio:** informado no campo `portfolio`, alinhado à direita em 20 posições. Carteira
padrão `1` (portfólio 20). O identificador do detalhe usa `01`/`02` conforme CPF/CNPJ do cedente.
