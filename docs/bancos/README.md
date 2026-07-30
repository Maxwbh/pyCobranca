# Documentação por Banco

Cada banco tem sua pasta/arquivo com a
**especificação implementada** (campo livre posição a posição, dígitos verificadores, carteiras,
**regras de validação de campos** e formato de exibição), a **referência ao manual oficial** do
banco e o **exemplo validado** na validação por vetores de referência.

> **Validação e erros:** as regras de tamanho/conjunto por campo e o **contrato de erros**
> (`BoletoInvalido.erros`) estão consolidados em
> [`../14-validacao-campos.md`](../14-validacao-campos.md).

> Os PDFs/manuais oficiais de cada banco devem ser armazenados na pasta do respectivo banco
> (ex.: `docs/bancos/104-caixa/`). Os `.md` abaixo referenciam
> o documento oficial usado em cada regra. As URLs dos manuais oficiais estão consolidadas em
> [`fontes-oficiais.md`](fontes-oficiais.md).

| Banco | Documento | Manual oficial de referência |
|-------|-----------|------------------------------|
| 001 — Banco do Brasil | [001-banco-do-brasil.md](001-banco-do-brasil.md) | "Especificações Técnicas — Bloqueto de Cobrança" (BB) |
| 004 — Banco do Nordeste | [004-banco-do-nordeste.md](004-banco-do-nordeste.md) | "Layout de Cobrança CNAB 400 — Banco do Nordeste" |
| 021 — Banestes | [021-banestes.md](021-banestes.md) | "Layout de Cobrança Banestes" |
| 033 — Santander | [033-santander.md](033-santander.md) | "Layout de Cobrança — Santander" (ficha de compensação/CNAB) |
| 041 — Banrisul | [041-banrisul.md](041-banrisul.md) | "Layout de Cobrança CNAB 400 — Banrisul" |
| 070 — BRB (Banco de Brasília) | [070-brb.md](070-brb.md) | "Layout de Remessa DCB — BRB" |
| 085 — Ailos | [085-ailos.md](085-ailos.md) | "Manual de Cobrança CNAB 240 — Ailos" |
| 097 — CrediSIS | [097-credisis.md](097-credisis.md) | "Layout de Cobrança CNAB 400 — CrediSIS" |
| 104 — Caixa | [104-caixa.md](104-caixa.md) | "Especificações Técnicas Boleto de Cobrança CAIXA" (SIGCB) |
| 136 — Unicred | [136-unicred.md](136-unicred.md) | "Manual de Cobrança Unicred (CNAB 400/240)" |
| 237 — Bradesco | [237-bradesco.md](237-bradesco.md) | "Manual Técnico Cobrança Bradesco" (carteiras/nosso número) |
| 336 — C6 Bank | [336-c6.md](336-c6.md) | "Cobrança Bancária Padrão CNAB 400 Posições — C6" |
| 341 — Itaú | [341-itau.md](341-itau.md) | "Manual Técnico de Cobrança Itaú" (DAC/campo livre) |
| 399 — HSBC (legado) | [399-hsbc.md](399-hsbc.md) | "Layout de Cobrança HSBC" (carteiras CNR/CSB) |
| 422 — Safra | [422-safra.md](422-safra.md) | "Layout de Cobrança Safra" |
| 745 — Citibank | [745-citibank.md](745-citibank.md) | "Layout de Cobrança CNAB 400 — Citibank" |
| 748 — Sicredi | [748-sicredi.md](748-sicredi.md) | "Manual de Cobrança CNAB 240 — Sicredi" |
| 756 — Sicoob | [756-sicoob.md](756-sicoob.md) | "Manual de Cobrança Sicoob (CNAB 400/240)" |

## Todos os bancos suportados (18) — boleto validado por comparação cruzada

| Código | Banco | Particularidade principal |
|:------:|-------|---------------------------|
| 001 | Banco do Brasil | Convênios 4/6/7; nosso número 17 no convênio 7 |
| 004 | Banco do Nordeste | DV módulo 11 (fatores 2..8) |
| 021 | Banestes | DV duplo no nosso número; dígito duplo no campo livre |
| 033 | Santander | IOS + código do cedente; DV 2..9 (>9→0) |
| 041 | Banrisul | Dígito duplo (módulo 10+11) com regra de recálculo |
| 070 | BRB (Banco de Brasília) | Incremento(3) + dígito duplo |
| 085 | Ailos | Conta com DV (7+1) + nosso número 9 |
| 097 | CrediSIS | DV do documento do cedente no campo livre |
| 104 | Caixa | SIGCB: intercalação do nosso número 17 |
| 136 | Unicred | Conta 9 + DV informado |
| 237 | Bradesco | DV base 7 (restos 1→"P", 0→"0") |
| 336 | C6 Bank | Convênio 12 + indicador de layout por carteira |
| 341 | Itaú | DACs módulo 10 (agência/conta/carteira/nosso) |
| 399 | HSBC (legado) | CNR com data juliana; CSB |
| 422 | Safra | DV calculado da esquerda p/ direita (11→1) |
| 745 | Citibank | Portfólio + convênio sem 1º dígito |
| 748 | Sicredi | Ano + byte identificador no nosso número |
| 756 | Sicoob | DV com fatores fixos 3-1-9-7 (esq.→dir.) |

## Remessa CNAB — validada byte a byte

Todos os arquivos abaixo são gerados **byte a byte idênticos** aos vetores de referência para os mesmos
dados de entrada; as fixtures ficam congeladas em
[`tests/fixtures/`](../../tests/fixtures/) e são verificadas em
[`tests/test_cnab_remessa.py`](../../tests/test_cnab_remessa.py).

| Banco | CNAB 400 | CNAB 240 | Observação de layout |
|-------|:--------:|:--------:|----------------------|
| Banco do Brasil (001) | ✅ | ✅ | Convênio 4/6/7; nosso número com DV por tamanho do convênio |
| Banco do Nordeste (004) | ✅ | — | Detalhe com 401 posições (quirk do layout) |
| Santander (033) | ✅ | ✅ | 240: segmento P com 241 posições |
| Banrisul (041) | ✅ | — | Nosso número com dígito duplo (módulo 10+11) |
| Banco de Brasília/BRB (070) | ✅ | — | Formato **DCB** (não FEBRABAN): header 39, detalhe 402 |
| Ailos (085) | — | ✅ | Segmento R só quando há multa |
| CrediSIS (097) | ✅ | — | Detalhe com 402 posições (quirk do layout) |
| Caixa (104) | — | ✅ | Layout SIGCB |
| Unicred (136) | ✅ | ✅ | 240 reaproveita o layout Sicredi |
| Bradesco (237) | ✅ | — | DV do nosso número base 7 (restos 1→"P", 0→"0") |
| C6 (336) | ✅ | — | DV do nosso número módulo 11 base 7; carteiras 10/20 |
| Itaú (341) | ✅ | — | Código da carteira `I`/`U`/`1`/`E` |
| Citibank (745) | ✅ | — | Portfólio de 20 posições |
| Sicredi (748) | — | ✅ | — |
| Sicoob (756) | ✅ | ✅ | Trailer de cooperativa (totais por carteira) |

> Onde o registro diverge das 400/240 posições do padrão FEBRABAN (Banco do Nordeste, CrediSIS,
> BRB e o segmento P do Santander 240), a divergência vem **do layout de referência**; a PyCobrança
> mantém a paridade byte a byte e anota o desvio no código (`tamanho_registro=None`).

Além da paridade byte a byte, cada arquivo passa por um **validador estrutural FEBRABAN
independente** (`tests/test_cnab_estrutura.py`), que lê a remessa posição a posição — como o intake
de um banco faria — conferindo sequência de registros, larguras, numeração sequencial, ordem dos
segmentos e as contagens dos trailers de lote e de arquivo.

> **Correção arbitrada pela FEBRABAN (CNAB 240 com PIX):** a *quantidade de registros do arquivo*
> deve contar **todos** os registros físicos (tipos 0/1/3/5/9), inclusive os segmentos Y do PIX. O
> vetor de referência os omitia dessa contagem; a PyCobrança segue o Layout Padrão FEBRABAN 240, de
> modo que os arquivos `*_pix_cnab240.rem` divergem propositalmente da referência nesse campo.

## Retorno CNAB — parsing validado campo a campo

`Retorno.ler(caminho)` detecta o layout (240/400) e o banco (header) e devolve
`RegistroRetorno`. Parsing validado **campo a campo** contra vetores de referência para 11 arquivos `.RET`
(fixtures em [`tests/fixtures/retorno/`](../../tests/fixtures/retorno/),
testes em [`tests/test_cnab_retorno.py`](../../tests/test_cnab_retorno.py)):

- **CNAB 400**: Itaú (341), Bradesco (237), Banco do Brasil (001), Santander (033, com campos PIX),
  Banco do Nordeste (004), Banrisul (041), CrediSIS (097), C6 (336), Unicred (136) e BRB (070).
- **CNAB 240**: base/Caixa (104), Santander (033), Ailos (085), Sicredi (748) e Sicoob (756) —
  combinação dos segmentos **T** (dados gerais) e **U** (valores).

Além do campo a campo, um **validador independente** (`tests/test_retorno_estrutura.py`) relê cada
`.RET` posição a posição e confronta com a saída do parser: a contagem de registros bate com as
linhas de detalhe (400) e com os segmentos T (240), e cada `nosso_numero` extraído está de fato na
linha de origem.

> **Correção arbitrada pela FEBRABAN (retorno 400):** o **trailer** (tipo 9) é um registro de
> controle, não um título; ele deixou de aparecer em `registros` (antes vazava como um registro
> fantasma, com nosso número zerado e ocorrência vazia).

## Validação cruzada

**Os 18 bancos** foram validados gerando **os mesmos dados nos dois sistemas** (PyCobrança ×
implementação de referência independente): **código de barras e linha digitável idênticos em 18/18**.
Os vetores estão congelados em
[`tests/test_validacao_cruzada.py`](../../tests/test_validacao_cruzada.py).
Divergência encontrada e arbitrada durante o porte: o layout do **Ailos** (conta 7+DV e nosso
número 9, conforme o manual da cooperativa) — corrigido na PyCobrança.

Divergência conhecida (cosmética): exibição do nosso número do **Santander** — a PyCobrança
imprime as 13 posições do layout oficial (`000001234567-9`); o vetor de referência omite os zeros
(`1234567-9`). O código de barras é idêntico.
