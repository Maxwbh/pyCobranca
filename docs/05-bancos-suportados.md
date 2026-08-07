---
description: >-
  Matriz dos 18 bancos da PyCobrança: boleto, PIX/Bolepix, remessa CNAB 400 e 240
  e parsing de retorno, banco a banco.
---

# 05 — Bancos Suportados

Os **18 bancos** abaixo emitem boleto: campo livre, dígitos verificadores, código de barras,
linha digitável e PDF. Todos validados contra vetores de referência — ver
[`docs/bancos/`](bancos/README.md).

CNAB e PIX variam por banco, e a matriz mostra exatamente onde.

## Legenda

- ✅ implementado e coberto por teste
- — não implementado
- **PIX** = Bolepix (QR no boleto e segmento PIX na remessa)
- **Retorno** = o banco tem layout de retorno próprio; sem ele o parser recorre a um layout
  genérico, que lê o arquivo mas pode divergir em campos específicos do banco

| Código | Banco | Boleto | PIX | Remessa 400 | Remessa 240 | Retorno |
|:------:|-------|:------:|:---:|:-----------:|:-----------:|:-------:|
| 001 | Banco do Brasil | ✅ | ✅ | ✅ | ✅ | ✅ |
| 004 | Banco do Nordeste | ✅ | — | ✅ | — | ✅ |
| 021 | Banestes | ✅ | — | — | — | — |
| 033 | Santander | ✅ | ✅ | ✅ | ✅ | ✅ |
| 041 | Banrisul | ✅ | — | ✅ | — | ✅ |
| 070 | BRB | ✅ | — | ✅ | — | ✅ |
| 085 | Ailos | ✅ | — | — | ✅ | ✅ |
| 097 | CrediSIS | ✅ | — | ✅ | — | ✅ |
| 104 | Caixa Econômica Federal | ✅ | ✅ | — | ✅ | ✅ |
| 136 | Unicred | ✅ | — | ✅ | ✅ | ✅ |
| 237 | Bradesco | ✅ | ✅ | ✅ | — | ✅ |
| 336 | C6 Bank | ✅ | ✅ | ✅ | — | ✅ |
| 341 | Itaú | ✅ | ✅ | ✅ | — | ✅ |
| 399 | HSBC | ✅ | — | — | — | — |
| 422 | Safra | ✅ | — | — | — | — |
| 745 | Citibank | ✅ | — | ✅ | — | — |
| 748 | Sicredi | ✅ | — | — | ✅ | ✅ |
| 756 | Sicoob | ✅ | ✅ | ✅ | ✅ | ✅ |

Totais: **18** com boleto, **7** com PIX, **12** com remessa 400, **7** com remessa 240,
**15** com layout de retorno próprio.

Cada banco tem uma página com carteiras, formato do nosso número, composição do campo livre e
fontes oficiais: [`docs/bancos/`](bancos/README.md).

## Sobre as lacunas

Um traço na matriz significa que o layout ainda não foi portado, não que o banco não aceite
aquele meio. Banestes, HSBC e Safra emitem boleto mas ainda não têm CNAB; Citibank tem remessa
400 sem layout de retorno próprio.

O critério para fechar uma lacuna é o mesmo de sempre: manual oficial do banco e arquivo de
referência para comparação byte a byte. Sem os dois, o layout não entra — ver
[17 — Compatibilidade](17-compatibilidade.md).

## Contrato por banco (`BancoBase`)

Cada banco declara:

| Atributo/método | Descrição |
|-----------------|-----------|
| `codigo` | Código FEBRABAN (3 dígitos). |
| `nome` | Nome de exibição. |
| `digito_banco` | Dígito verificador do código do banco. |
| `carteiras` | Carteiras suportadas. |
| `suporta_pix` | Capacidade de Bolepix. |
| `campo_livre()` | As 25 posições do código de barras específicas do banco. |
| `nosso_numero_formatado()` | Formatação do nosso número. |
| `agencia_conta_formatado()` | Formatação de agência/conta. |
| `validar()` | Regras de validação específicas. |

## Como adicionar um banco

O passo a passo está em [15 — Criando um banco](15-novo-banco.md); o resumo:

1. Criar `pycobranca/bancos/<banco>.py` herdando de `BancoBase`.
2. Declarar `codigo`, `nome`, `digito_banco`, `carteiras`, `suporta_pix`.
3. Implementar `campo_livre()`, `nosso_numero_formatado()`, `agencia_conta_formatado()` e
   `validar()`.
4. O `__init_subclass__` de `BancoBase` registra o banco automaticamente.
5. Adicionar testes com **valores conhecidos** de linha digitável e código de barras.
6. Havendo CNAB, criar o layout em `pycobranca/cnab/cnab400/` e/ou `pycobranca/cnab/cnab240/`,
   com fixture de comparação byte a byte.
7. Atualizar esta matriz e a página do banco em `docs/bancos/`.
