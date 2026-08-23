---
description: >-
  Embutir a PyCobrança em outro sistema: estado e concorrência, numeração,
  formato da saída, contrato de erros, lotes e homologação bancária.
---

# 19 — Integração

Esta página responde ao que um sistema hospedeiro precisa saber antes de embutir a biblioteca:
de que ela cuida, do que ela **não** cuida, e onde ficam as responsabilidades que sobram.

## O que a biblioteca não faz

Nada disso é omissão — é fronteira deliberada, e cada item vira responsabilidade sua:

- **Não fala rede.** Não há cliente HTTP, nem chamada a API de banco. Ela transforma dados em
  arquivos e documentos, e só.
- **Não escreve em disco.** `gera_arquivo()` devolve `str`; `render_boleto_pdf()` devolve `bytes`.
  Onde isso é gravado, e com qual nome, é decisão do hospedeiro.
- **Não persiste estado.** Não há banco de dados, cache nem arquivo de controle. Nada é lembrado
  entre uma chamada e outra.
- **Não numera.** Nosso número e sequencial de remessa vêm de você — ver
  [Numeração](#numeracao).
- **Não agenda nem repete.** Não há fila, retentativa ou idempotência embutidas.

## Estado e concorrência

**O pacote não mantém estado global mutável.** Todo objeto (`Boleto`, `Pagamento`, `Remessa*`,
`Retorno`) carrega os próprios dados, e o registro de bancos é populado uma vez, na importação,
e depois só é lido.

Na prática:

- Criar e usar instâncias em paralelo é seguro; não é preciso *lock* nem processo dedicado.
- Não há vazamento entre requisições ou entre empresas — o que separa um contexto do outro são
  os objetos que você passa, não configuração global.
- Não reaproveite a **mesma instância** de `Remessa*` em duas gerações concorrentes: ela é um
  agregado de dados, não um serviço. Instancie por operação; custa pouco.

Multiempresa não exige nada especial: são objetos diferentes, com dados diferentes.

## Numeração {#numeracao}

Dois números são seus, e o banco rejeita arquivo quando eles saem errados.

**Nosso número** é campo obrigatório de `Pagamento` e do boleto, sem valor padrão útil. A
biblioteca calcula o dígito verificador e a formatação de cada banco, mas **não gera a
sequência** — ela não sabe qual foi o último título emitido. Persistir e avançar esse contador,
sem repetir e sem furo, é do sistema hospedeiro.

**Sequencial de remessa** identifica o arquivo dentro da conta. É o campo `sequencial_remessa`,
com valor padrão `"1"`:

```python
remessa = RemessaSicoob400(..., sequencial_remessa="42")
```

Dois cuidados:

- O padrão `"1"` é conveniência para teste. Em produção, mandar todo arquivo com `"1"` costuma
  fazer o banco recusar o segundo do dia por sequência duplicada.
- **Nem todo layout usa esse campo.** Ele aparece no header de Banco do Brasil, Bradesco, C6,
  CrediSIS, Sicoob e Unicred no CNAB 400, e na base do CNAB 240 (incluindo Santander). No Itaú
  400, por exemplo, o header não tem essa posição, e mudar o valor não altera o arquivo. Confira
  a página do banco antes de assumir que o campo tem efeito.

O **sequencial de registro** dentro do arquivo (linha 1, 2, 3… e o total no trailer) é calculado
pela biblioteca. Esse você não precisa controlar.

## Formato da saída

O arquivo CNAB sai pronto para o banco, com três transformações já aplicadas:

- **Acentos normalizados.** `JOSÉ AÇÚCAR & CIA` vira `JOSE ACUCAR  CIA`; `Rua São João` vira
  `RUA SAO JOAO`. A saída é **ASCII puro** — não há byte acima de 127 para o banco recusar.
- **Caixa alta** nos campos de texto.
- **Terminação CRLF** (`\r\n`), inclusive na última linha, como o padrão FEBRABAN espera.

Como `gera_arquivo()` devolve `str` já com `\r\n`, grave em modo binário ou desligue a tradução
de fim de linha — caso contrário o Windows duplica o `\r`:

```python
conteudo = remessa.gera_arquivo()

# Correto: não deixa o Python mexer nas quebras de linha.
with open("CB250807.REM", "w", encoding="ascii", newline="") as arquivo:
    arquivo.write(conteudo)

# Equivalente, em bytes:
with open("CB250807.REM", "wb") as arquivo:
    arquivo.write(conteudo.encode("ascii"))
```

O nome do arquivo é convenção de cada banco e não é gerado pela biblioteca.

## Valores monetários

Campos de valor aceitam `Decimal`, `float` e `str`, e são formatados com duas casas para o
arquivo. **Use `Decimal`**: é a convenção do projeto e evita que o erro de arredondamento do
`float` apareça em algum ponto do seu próprio cálculo, antes mesmo de chegar aqui.

```python
from decimal import Decimal

Pagamento(valor=Decimal("199.90"), **resto)
```

## Contrato de erros

Todas as exceções da biblioteca herdam de `PyCobrancaError`, então um `except` cobre tudo — e
cada uma herda também do erro embutido correspondente, de modo que quem já tratava por
`ValueError`/`KeyError` continua funcionando:

| Exceção | Quando |
|---|---|
| `BancoNaoRegistrado` | código FEBRABAN desconhecido em `Bancos.find()` ou `banco_info()` |
| `BoletoInvalido` | campo fora das regras do banco |
| `DadosInvalidos` | entrada fora do que a composição do título aceita |
| `RetornoInvalido` | arquivo de retorno vazio ou sem header reconhecível |
| `OFXInvalido` | arquivo que não é OFX |
| `ModeloInvalido` | modelo de documento ou bloco de fatura fora do catálogo |
| `DependenciaAusente` | `reportlab`/`qrcode` faltando na instalação |

De borda, e igualmente cobertas: `InvalidBarcodeError` (`render`), `ErroDeContrato`
(`contracts`) e `PixInvalido` (`pix`).

`BoletoInvalido` carrega **`.erros`**, uma lista com um item por problema — dá para devolver
todas as violações de uma vez, em vez de o usuário descobrir uma por tentativa:

```python
from pycobranca.bancos import Bancos
from pycobranca.exceptions import BoletoInvalido

try:
    boleto.validar()
except BoletoInvalido as erro:
    for problema in erro.erros:
        print(problema)
    # carteira '999' não suportada (use uma de: 104, 109, 112, 115, 175, 177, 188)
```

Chame `validar()` explicitamente antes de renderizar ou gerar remessa: é onde as regras por banco
são conferidas. `Pagamento.validar()` faz o mesmo para encargos.

A geração da remessa tem ainda uma conferência final de tamanho do registro, que impede o
arquivo malformado de sair:

```text
BoletoInvalido: registro 2 com 393 posições (esperado 400)
```

A mensagem informa o **registro**, não o campo. Ao receber esse erro, confira antes de mais nada
a largura dos campos de identificação da conta — agência, conta corrente, dígito e convênio —
contra a especificação do banco na página correspondente em [`docs/bancos/`](bancos/README.md).
Um campo com tamanho diferente do previsto desloca todas as posições seguintes.

## Lotes

`gera_arquivo()` monta o arquivo inteiro em memória e devolve de uma vez. Medido nesta máquina,
com o layout do Itaú 400:

| Títulos | Tempo | Arquivo |
|--------:|------:|--------:|
| 1.000 | ~44 ms | 0,4 MB |
| 10.000 | ~465 ms | 3,8 MB |

O crescimento é linear e o custo é baixo, mas **é tudo memória residente**. Para remessas muito
grandes, o limite prático não é a CPU — é o pico de memória do processo somado ao que o
hospedeiro fizer com a string depois (cópia para resposta HTTP, anexo, etc.).

## Homologação com o banco

Este é o item que mais distorce cronograma, e não depende da biblioteca.

Antes de liberar produção, o banco exige **homologar o arquivo de remessa**: você envia um
arquivo de exemplo, a área técnica confere posição a posição, aponta divergências e repete o
ciclo. Leva de semanas a meses, varia por banco e por agência, e costuma incluir exigências que
não estão no manual público — máscara de nosso número, faixa de carteira liberada para o
convênio, código de cedente com formato próprio.

O que a PyCobrança oferece para encurtar isso: a remessa é validada byte a byte contra arquivos
de referência (ver [17 — Compatibilidade](17-compatibilidade.md)), então a divergência tende a
estar no **cadastro do convênio**, não na montagem do registro. Vale começar a homologação cedo,
em paralelo ao desenvolvimento, e não depois.

## Checklist

- [ ] Nosso número persistido e avançado pelo hospedeiro, sem repetição.
- [ ] `sequencial_remessa` controlado, e conferido se o layout do banco usa o campo.
- [ ] Gravação em `newline=""` ou em bytes, para não duplicar o `\r`.
- [ ] Valores em `Decimal`.
- [ ] `validar()` chamado, e `.erros` propagado para a interface.
- [ ] `PyCobrancaError` tratado na fronteira do módulo.
- [ ] Homologação bancária iniciada em paralelo ao desenvolvimento.
