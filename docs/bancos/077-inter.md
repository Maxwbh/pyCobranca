---
description: >-
  Boleto Banco Inter (077) em Python: campo livre posição a posição, DV do nosso número, carteira 110 e por que a 112 não é suportada.
---

# Banco Inter (077)

**Manual oficial de referência:** *Manual CNAB400 — Emissão boletos de cobrança* (Inter, v2.2,
26/08/2024), seções 6, 7.1.3 e 7.3. Fontes em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs
não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/inter.py`](../../pycobranca/bancos/inter.py) ·
Dígito do banco: **9** · PIX: — (ver abaixo)

## Resumo

Banco digital de agência única (`0001`). O nosso número tem **11 posições** (10 dígitos + DV) e o
DV sai de um módulo 10 que inclui agência e carteira.

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–4   | 4  | Agência sem DV — `0001` |
| 5–7   | 3  | Carteira |
| 8–14  | 7  | Número da operação |
| 15–25 | 11 | Nosso número **com DV** |

O **número da operação** é o identificador do cliente junto ao Inter, obtido uma vez e fixo daí em
diante. Na PyCobrança ele entra em `convenio`, o campo que a biblioteca já usa para o
código do cedente-beneficiário nos demais bancos.

## Dígito verificador do nosso número

Módulo 10 sobre `agência(4) + carteira(3) + nosso número sem DV(10)` — 17 dígitos, pesos 2 e 1 da
direita para a esquerda, produtos maiores que 9 somados algarismo a algarismo.

É o mesmo módulo 10 da FEBRABAN que a biblioteca já implementa em `pycobranca.core.dv.modulo10`.
O exemplo resolvido do manual (seção 7.3) confere:

```
0001 + 110 + 0004309540  ->  00011100004309540
soma 29 · resto 9 · DV = 10 - 9 = 1  ->  nosso número 0004309540-1
```

## Só a carteira 110

O Inter tem duas modalidades com modelos **opostos** de atribuição do nosso número:

| Carteira | Quem numera | Suportada |
|:--:|---|:--:|
| **110** | o **cliente**, de uma faixa que o Inter entrega antes | ✅ |
| 112 | o **banco**, depois de receber a remessa | — |

Na 112, o nosso número **só existe no arquivo retorno**. Antes disso não há código de barras a
montar, e nenhum algoritmo supre isso: falta o dado, não a regra. Aceitá-la produziria um título
que imprime, passa em conferência estrutural e carrega um nosso número que o Inter nunca emitiu.

Por isso a 112 é **recusada em `validar()`** — ver
[ausências permanentes](../05-bancos-suportados.md#ausencias-que-sao-permanentes).

!!! info "A 110 depende de enquadramento"
    O manual (seção 6) registra que a 112 é a modalidade automática de toda conta, e que a 110
    exige perfil de relacionamento Inter Empresas, solicitado ao advisor da conta ou à central de
    atendimento. Sem a faixa de nossos números não há o que compor.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à
esquerda. Violações vêm em `BoletoInvalido.erros` — ver o
[contrato de erros](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 0–4 dígitos — **opcional**; omitida, assume `0001` |
| Número da operação (`convenio`) | 1–7 dígitos |
| Nosso número | 1–10 dígitos (o DV é calculado, não informado) |
| Carteira | conjunto: `110` |

## Formatos de exibição

- Nosso número: `nosso_numero-DV` → `0004309540-1`
- Agência/conta: `0001 / 123456`

## Exemplo

Entrada: agência `0001`, conta `123456`, carteira `110`, número da operação `1234567`,
nosso número `0004309540`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      0001110123456700043095401
Código de barras: 07796153900000127500001110123456700043095401
Linha digitável:  07790.00116 10123.456708 00430.954016 6 15390000012750
```

## Sobre a evidência

!!! warning "Sem vetor cruzado — a procedência aqui é diferente"
    Os demais bancos têm a saída conferida contra uma implementação de produção independente. O
    Inter **não existe em nenhuma implementação aberta conhecida**, então esse cruzamento não
    existe para ele.

    O que sustenta esta implementação: o **DV do nosso número conferido contra o exemplo resolvido
    do manual** (única verificação com número esperado vindo do banco), as **posições do campo
    livre conferidas uma a uma** contra a tabela da seção 7.1.3, e a montagem do código de barras
    validada pelo **verificador FEBRABAN independente**, que não usa nada do núcleo.

    O código de barras congelado nos testes é **guarda de regressão, não paridade externa**: ele
    prende a saída de hoje, e prenderia igual se estivesse errada. **Um boleto real do Inter na
    carteira 110 fecha essa lacuna** — se você tiver um, [abra uma
    issue](https://github.com/Maxwbh/pyCobranca/issues).

## Remessa CNAB 400 — implementada

**Implementação:** [`pycobranca/cnab/cnab400/inter.py`](../../pycobranca/cnab/cnab400/inter.py) ·
fixture: [`tests/fixtures/remessa_inter_cnab400.rem`](../../tests/fixtures/remessa_inter_cnab400.rem)

Registros de 400 posições (header, N detalhes tipo 1, trailer), conforme a seção 4 do manual.

**Nome do arquivo:** `CI400_001_???????.REM`, onde as sete posições são o **mesmo** sequencial
gravado no header (111–117) — o manual (seção 3.1) condiciona o upload a essa igualdade. Como a
biblioteca gera o conteúdo e o chamador nomeia o arquivo, é fácil os dois divergirem; use
`remessa.nome_arquivo()`, que deriva o nome do mesmo campo.

Três diferenças em relação ao layout comum dos demais bancos:

| Onde | O que muda |
|---|---|
| Header, posições 27–46 | **brancos** — o Inter não identifica a conta no header |
| Trailer, posições 2–7 | **quantidade de boletos** (o trailer genérico leva brancos ali) |
| Detalhe, item 13 | na carteira **112** o nosso número vai **zerado**: quem numera é o banco |

!!! danger "Nosso número na remessa: 10 ou 11 dígitos, nunca preenchido com zero"
    A faixa que o Inter reserva vem com **10 dígitos, sem DV**. As 11 posições do item 13 pedem
    número **+ DV** — completar com zero à esquerda vira `0` + número: o dígito some, o valor
    desloca uma casa, e o banco recusa com *"dígito verificador inválido para o nosso número"*,
    um dos erros mais relatados na comunidade do Inter.

    O detalhe cruel: as 11 posições continuam **numéricas**, então o arquivo **passa** num
    validador de layout e só quebra no processamento. A biblioteca aceita as duas formas —
    calcula o DV quando recebe 10 dígitos, usa como veio quando recebe 11 — e **recusa qualquer
    outro tamanho**, porque aí não há como saber se falta ou sobra dígito.

    Pelo mesmo motivo, `digito_conta` é **obrigatório**: o item 06 é obrigatório no manual, e
    assumir `0` gravaria a identidade de outra conta num arquivo estruturalmente válido.

**Encargos suportados:** multa e juros em **valor fixo ou percentual**, escolhidos por um código
próprio (itens 9–12 e 25–28), e desconto em valor fixo ou percentual do nominal (itens 29–32) —
cada um com data limite obrigatória. O layout **não tem** campo de IOF nem de abatimento.

O `tipo_mora` da biblioteca segue a FEBRABAN, onde `3` é isento; o Inter usa `0` para "sem
juros". A tradução é explícita em `_codigo_mora` — sem ela, o padrão cairia num código que o
Inter não define.

!!! success "Validado pelo validador de layout do próprio Inter"
    Um arquivo gerado pela PyCobrança com **quatro títulos** foi submetido ao
    [validador de layout](https://developers.inter.co/docs/cnab/validador) do portal do
    desenvolvedor do Inter, no modo **CNAB Inter Cobrança 400**, e passou:
    *"Arquivo validado com sucesso — todos os campos foram preenchidos corretamente"*.

    Os quatro casos foram escolhidos para o validador ter o que conferir: nosso número informado
    **com** e **sem** DV, um título com **multa, juros e desconto** juntos, e um pagador **CNPJ**
    (tipo de inscrição `02`).

    Esta é a verificação mais forte que a remessa tem: quem conferiu foi a ferramenta do próprio
    banco que recebe o arquivo, não uma releitura nossa do manual.

    **O que ela cobre:** conformidade de layout — presença, posição, tamanho e formato de cada
    campo nos três registros. **O que ela não cobre:** que a agência, a conta e o número da
    operação existam de fato (os do teste são fictícios), nem o código de barras do boleto, que é
    outro artefato e tem a sua própria camada de verificação.

    A fixture em `tests/fixtures/` continua sendo **guarda de regressão** — ela prende a saída
    validada de hoje para que uma mudança acidental apareça. E
    `test_remessa_inter_posicoes_do_manual` segue afirmando cada campo na posição documentada:
    é o que localiza *qual* campo quebrou quando algo quebrar.

## PIX / Bolepix — não há no layout de cobrança

`suporta_pix = False`, e não por omissão: o *Manual CNAB400* do Inter **não menciona PIX, QR Code
nem BR Code uma única vez**. Não existe segmento PIX na remessa de cobrança do banco, que é a
origem do Bolepix nos sete bancos onde a biblioteca o emite.

Isso descreve o **produto de cobrança por arquivo**, não o banco: o Inter opera Pix normalmente, e
oferece cobrança com QR pela **API**, que é caminho de integração online — fora do escopo desta
biblioteca ([ausências permanentes](../05-bancos-suportados.md#ausencias-que-sao-permanentes)).

## Retorno CNAB 400 — implementado

**Layout:** `LAYOUTS_400["077"]` em
[`pycobranca/cnab/retorno/cnab400.py`](../../pycobranca/cnab/retorno/cnab400.py) ·
fixture: [`tests/fixtures/retorno_inter_cnab400.ret`](../../tests/fixtures/retorno_inter_cnab400.ret)

O retorno do Inter (manual, seção 5.2) fica **bem distante do layout comum**, e é aí que mora o
risco:

| Campo | Inter | Maioria dos bancos |
|---|:--:|:--:|
| Código de ocorrência | **90–91** | 109–110 |
| Data da ocorrência | **92–97** | 111–116 |
| Vencimento | **119–124** | 147–152 |
| Valor do título | **125–137** | 153–165 |

Sem a entrada `077`, o parser cairia no layout de reserva e leria o *"seu número"* como código de
ocorrência — **sem erro e sem aviso**, com o arquivo inteiro parecendo válido.
`test_sem_o_layout_proprio_o_inter_seria_lido_errado` mede exatamente isso: lê a mesma fixture
pelos dois caminhos e afirma que os resultados divergem.

### Códigos de ocorrência próprios

O Inter usa quatro, e um deles **colide de frente** com a FEBRABAN:

| Código | Inter | Padrão FEBRABAN |
|:--:|---|---|
| 02 | Em aberto | Entrada confirmada |
| 03 | Erro | Entrada rejeitada |
| 06 | Pago | Liquidação normal |
| **07** | **Cancelado** | **Liquidação por conta/parcial** |

Os três primeiros são equivalentes na prática; o `07` inverte o sentido. Descrever título
cancelado como parcialmente liquidado erra a conciliação em silêncio. Por isso existe
`OCORRENCIAS_400_POR_BANCO`, consultado antes do mapa padrão — `descreve_ocorrencia` aceita o
banco, e `Retorno.descricao_ocorrencia` o repassa sozinho.

O motivo da rejeição vem em texto livre nas posições **241–380**, quando a ocorrência é `03`.

!!! warning "A fixture do retorno foi montada a partir do manual"
    Não há arquivo de retorno real do Inter aqui: a fixture foi construída posição a posição
    conforme a seção 5.2. Ela prova o **mapeamento**, não o arquivo que o banco de fato emite —
    diferente da remessa, que passou pelo validador do próprio Inter. Um retorno real fecharia
    essa lacuna.

## CNAB 240 — não existe para cobrança no Inter

Não é lacuna: o manual de cobrança não menciona 240 nenhuma vez, e a apresentação diz que as
opções são *"a troca de arquivos com layout CNAB400, ou a integração via API"*.

O Inter **publica** um manual CNAB 240 — mas de **pagamentos**, produto diferente. A confusão é
natural, porque *"remessa e retorno"* é **padrão de transporte, não produto**: os dois usam o
mesmo par de arquivos, e o que muda é a direção do dinheiro.

| Produto | Remessa (você → banco) | Retorno (banco → você) |
|---|---|---|
| **Cobrança** (400) | registre estes títulos que vou **receber** | fulano pagou; este foi cancelado |
| **Pagamentos** (240) | execute estes pagamentos que vou **fazer** | esta TED saiu; este boleto foi quitado |

Ver "Remessa e Retorno" num índice, portanto, não diz de qual produto se trata. O que decide são
os segmentos: o manual de pagamentos traz **A, B, J e O** (transferir via TED/Pix, pagar boleto,
pagar tributo) e tem **zero ocorrências de Segmento P, Q, R** e de **"Nosso Número"** — os campos
que só existem quando há um título *seu* a receber. Pagamentos é dinheiro **saindo**; esta
biblioteca trata do que **entra**.
