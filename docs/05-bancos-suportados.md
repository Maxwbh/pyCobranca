---
description: >-
  Matriz dos 19 bancos da PyCobrança: boleto, PIX/Bolepix, remessa CNAB 400 e 240
  e parsing de retorno, banco a banco.
---

# 05 — Bancos Suportados

Os **19 bancos** abaixo emitem boleto: campo livre, dígitos verificadores, código de barras,
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
| 077 | Banco Inter | ✅ | — | ✅ | — | ✅ |
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

Totais: **19** com boleto, **7** com PIX, **13** com remessa 400, **7** com remessa 240,
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

### Ausências que são permanentes

Nem toda ausência é lacuna. A PyCobrança compõe o título **inteiramente offline**, a partir do que
o chamador já tem. Quando alguma posição do código de barras depende de uma resposta do banco — o
nosso número atribuído no processamento da remessa, um número devolvido por API —, aquela
modalidade **não é implementável aqui**, e nenhum manual muda isso: falta o dado, não o algoritmo.

O corte costuma ser **por carteira, não por banco**. A mesma instituição pode ter uma carteira em
que o cliente numera a partir de uma faixa recebida antes — essa entra — e outra em que o banco
numera depois de receber o arquivo, que não entra. Quando um banco assim for implementado, só a
carteira componível aparece em `carteiras`; a outra é **recusada na validação**, porque aceitá-la
geraria um título com um nosso número que o banco nunca emitiu.

É também por aí que se explica o **Inter sem remessa 240**: não é lacuna, é que o produto de
cobrança do banco não tem esse layout — o manual oferece CNAB 400 ou API, e o CNAB 240 que o
Inter publica é de *pagamentos*, produto diferente.

O mesmo raciocínio exclui os emissores exclusivamente por API, em que o boleto nasce da resposta
de um endpoint. Integrar com eles é trabalho de cliente HTTP, não de composição de código de
barras — e a PyCobrança não é um cliente HTTP ([00 — Visão geral](00-visao-geral.md)).

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
