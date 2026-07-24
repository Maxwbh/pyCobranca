# CrediSIS (097)

**Manual oficial de referência:** *Layout de Cobrança CNAB 400 — CrediSIS*. Sem manual público
localizado — layout portado por **paridade byte a byte** com os vetores de referência; ver
[`fontes-oficiais.md`](fontes-oficiais.md).

**Implementação (boleto):** [`pycobranca/bancos/credisis.py`](../../pycobranca/bancos/credisis.py) ·
DV do documento do cedente no campo livre.

## Remessa CNAB 400 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab400/credisis.py`](../../pycobranca/cnab/cnab400/credisis.py) ·
fixture: [`tests/fixtures/remessa_credisis_cnab400.rem`](../../tests/fixtures/remessa_credisis_cnab400.rem)

> **Quirk documentado:** o **registro detalhe tem 402 posições** (header e trailer têm 400) —
> conforme o layout do banco. Mantida a paridade byte a byte; por isso
> `tamanho_registro=None`.

Estrutura do arquivo (CRLF, maiúsculas sem acentos):

| Registro | Tam. | Conteúdo principal |
|----------|:----:|--------------------|
| Header (`01REMESSA01COBRANCA`) | 400 | info da conta (agência 4 + espaço + conta 8 + dígito) · empresa(30) · `097` + `CENTRALCRED` · data (DDMMAA) · sequencial(7) |
| Detalhe (tipo 1) | **402** | tipo/CPF-CNPJ da empresa · agência(4) + conta(8) + dígito · uso da empresa(25) · **nosso número** (`0` + código do cedente 4 + nosso número 6) · nº documento(10) · vencimento (DDMMAA) · valor(13) · emissão · valor de mora(6) · percentual de multa(6) · desconto · sacado (doc/nome 40/endereço 37/bairro 15/CEP/cidade 15/UF) · avalista(25) · dias de protesto · sequencial(6) |
| Trailer (tipo 9) | 400 | 393 brancos + sequencial(6) |

**Nosso número:** `0` + código do cedente(4) + nosso número(6, zeros à esquerda).
