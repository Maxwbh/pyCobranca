---
description: >-
  Boleto Sicoob (756) em Python: campo livre posição a posição, dígitos verificadores, nosso número e carteiras aceitas (1, 3, 9, 09). Remessa e retorno CNAB 400 e 240. Suporta PIX/Bolepix.
---

# Sicoob (756)

**Manual oficial de referência:** *Manual de Layout Sicoob — Cobrança* (CNAB 400 e CNAB 240).
Fontes e portal (validador CNAB Sicoob) em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs
não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/sicoob.py`](../../pycobranca/bancos/sicoob.py) ·
Dígito do banco: **0** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("756")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DV do nosso número com fatores fixos 3-1-9-7 (da esquerda para a direita).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1 | Carteira — o dígito **significativo** (`09` grava `9`, não `0`) |
| 2–5   | 4 | Agência |
| 6–7   | 2 | Variação (`01` se ausente) |
| 8–14  | 7 | Convênio (ou número do contrato na carteira 9) |
| 15–21 | 7 | Nosso número |
| 22    | 1 | DV do nosso número (módulo 11, fatores 3-1-9-7) |
| 23–25 | 3 | Quantidade de parcelas (`001` se ausente) |

## Dígitos verificadores

- **DV do nosso número** — módulo 11 sobre `agência(4) + identificador(10) + nosso número(7)`,
  fatores fixos `3, 1, 9, 7` aplicados da **esquerda para a direita**, `DV = 11 - (soma % 11)`;
  resultados **10 e 11 viram 0**.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Convênio | até 7 dígitos (opcional) |
| Número do contrato | até 7 dígitos (opcional) |
| Variação (modalidade) | até 2 dígitos, `01` quando ausente |
| Quantidade de parcelas | até 3 dígitos, `001` quando ausente |
| Nosso número | 1–7 dígitos |
| Carteira | conjunto: 1, 3, 9, 09 — `9` e `09` são a **mesma** carteira e geram o mesmo boleto |

## Formatos de exibição

- Nosso número: `nosso_numero(7)DV` → `12345673`
- Agência/conta: `agência / conta` (formato base de `BancoBase`)

## Exemplo (saída da engine)

Entrada: agência `1234`, convênio `1234567`, variação `01`, nosso número `1234567`, carteira
`1`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      1123401123456712345673001
Código de barras: 75692153900000127501123401123456712345673001
Linha digitável:  75691.12340 01123.456715 23456.730011 2 15390000012750
```

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

## Remessa CNAB 400 — auditada contra o layout oficial

As **54 posições** do registro de detalhe são conferidas uma a uma contra a aba
*03.Remessa - CNAB400* do `Layout_Cobranca_CNAB400.xls` (portal do banco, 19/05/2025), em
`test_remessa_sicoob_posicoes_do_layout_oficial` — um caso de teste por campo, com a máscara
que a planilha declara. A auditoria encontrou dois problemas que a paridade byte a byte **não
pegava**, porque a implementação de referência os reproduzia igual:

**1. As posições 111–120 são `X(10)`, e levavam zeros à esquerda.**

O campo é *Seu Número*, alfanumérico. Preencher com zero um valor que tem letras produz outro
valor: `DOC0001` virava `000DOC0001` — e é `000DOC0001` que o banco devolve no retorno. Quem
guardou `DOC0001` não reencontra o título ao conciliar por esse campo.

Valor só de dígitos continua alinhado à direita com zeros: ali as duas convenções coincidem, e
o comportamento anterior se mantém.

Por isso `remessa_sicoob_cnab400.rem` **deixou de ser vetor de paridade**. Onde manual e
implementação de referência discordam, vale o manual. A diferença é **só naquelas dez
posições** — 20 bytes nos dois registros de detalhe, nada mais se moveu.

**2. Não existe "tipo de formulário" no layout 400.**

O `RemessaSicoob400` aceitava `tipo_formulario` e nunca o gravava: quem o informava mudava
nada. É campo do **CNAB 240**, onde segue em uso. Foi removido — aceitar um parâmetro inerte é
pior que recusá-lo.

!!! note "`modalidade_carteira` aponta para o campo vizinho"
    Ela grava a posição **106**, que a planilha chama de *Tipo de Emissão* (`1` cooperativa,
    `2` cliente). Quem ocupa *Carteira/Modalidade* (107–108) é `carteira`. O nome ficou por
    compatibilidade; a documentação diz o que ele faz.

!!! warning "A planilha oficial tem um erro de posição"
    O campo 53 declara início **394**, fim **395** e tamanho **1** — os três não fecham entre
    si, e o campo 54 começa em 395. A transcrição segue o tamanho declarado (394–394), e um
    teste exige que a tabela cubra 1 a 400 sem buraco nem sobreposição.

## Retorno CNAB 400 — implementado

**Layout:** `LAYOUTS_400["756"]` em
[`pycobranca/cnab/retorno/cnab400.py`](../../pycobranca/cnab/retorno/cnab400.py) ·
fixture: [`tests/fixtures/retorno_sicoob_cnab400.ret`](../../tests/fixtures/retorno_sicoob_cnab400.ret)

Conforme a aba **04.Retorno - CNAB400** do `Layout_Cobranca_CNAB400.xls` publicado no portal do
banco (19/05/2025). Dois desvios grandes em relação ao layout de reserva:

| Campo | Sicoob | Layout de reserva (Itaú) |
|---|:--:|:--:|
| **Nosso número** | **063–073** + DV em **074** (12) | 063–070 (8) |
| **Data de crédito** | **176–181** | 296–301 |
| Carteira/modalidade | 107–108 (duas posições) | 108 (uma) |
| Valor da tarifa | 182–188 (sete) | 176–188 (treze) |
| Motivo | 081–082 (código de baixa/recusa) | 378–385 |

Sem a entrada `756`, o nosso número saía **truncado em oito posições** — três dígitos e o DV
perdidos — e a data de crédito vinha de 296–301, devolvendo zeros: indistinguível de *"ainda não
creditado"*. `test_sem_o_layout_proprio_o_sicoob_perdia_o_dv_e_a_data_de_credito` mede as duas.

!!! warning "Correção de um diagnóstico anterior"
    A documentação chegou a registrar que o Sicoob não teria CNAB 400 de cobrança, porque o
    **validador** do banco só oferece CNAB240. Era inferência a partir de uma ausência, não
    fonte: o portal publica o layout 400 com data de 2025. O validador não aceitar o 400 e o
    layout continuar publicado são fatos compatíveis — e só o segundo diz o que o banco emite.

!!! note "A fixture foi montada a partir do XLS"
    Não há arquivo de retorno 400 real do Sicoob aqui. A fixture prova o **mapeamento**, não o
    arquivo que o banco emite. Um retorno real fecharia essa lacuna.
