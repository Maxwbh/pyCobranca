# 04 — Contrato de dados para API REST

A PyCobrança serializa seus artefatos (boleto, remessa, retorno) para um **contrato de dados JSON**
(OpenAPI 3.0), pronto para ser exposto por um serviço REST. O contrato vem como **dado, não como
servidor**: a biblioteca não fala HTTP e não traz cliente nem framework — quem expõe é você, em
FastAPI, Flask, Django ou o que preferir.

## Contrato de dados (boleto)

O payload é `{"bank": <slug>, "data": <BoletoData>}` — o banco vai **fora** do `data`, como slug
(`itau`, não `341`), e o schema `BoletoData` **não tem** campo `banco`:

```json
{
  "bank": "itau",
  "data": {
    "valor": 127.50,
    "cedente": "Empresa Exemplo LTDA",
    "documento_cedente": "12345678000190",
    "agencia": "1234",
    "conta_corrente": "56789",
    "carteira": "109",
    "nosso_numero": "12345678",
    "data_vencimento": "2026-08-15",
    "sacado": "Cliente Final",
    "sacado_documento": "12345678909"
  }
}
```

**Obrigatórios no schema** são seis: `nosso_numero`, `valor`, `cedente`, `documento_cedente`,
`sacado` e `sacado_documento`. `agencia` e `conta_corrente` **não** entram nessa lista — o
Santander identifica o cedente pelo convênio e a Caixa pelo código do beneficiário, e exigi-los
tornaria esses dois inexprimíveis. O que cada banco realmente precisa é conferido por `validar()`
na engine, ver [14 — Validação de campos](14-validacao-campos.md).

O mapa código FEBRABAN → slug é `SLUG_POR_CODIGO`. Os nomes dentro de `data` acompanham os campos
de `BancoBase`, com quatro exceções que a serialização traduz — o mapa `NOMES_DO_CONTRATO` é a
fonte:

| No contrato | No construtor |
|---|---|
| `conta_corrente` | `conta` |
| `documento_cedente` | `cedente_documento` |
| `chave_pix` | `pix_chave` |
| `txid` | `pix_txid` |

> **`additionalProperties` é permissivo — mas só na validação.** `valida_contrato` ignora campo
> desconhecido em vez de recusá-lo, então um `data` com `banco` dentro **passa** por ele, e o banco
> declarado ali seria silenciosamente descartado. **`boleto_de_api` recusa**, nomeando o campo:
>
> ```
> ErroDeContrato: BoletoData.banco: campo desconhecido para o banco Itaú (341)
> ```
>
> Quem valida sem construir o título (um serviço que só confere a forma antes de enfileirar)
> precisa conferir a forma acima por conta própria.

### Campos específicos de banco

Sete dos 18 bancos precisam de campo que não aparece no payload genérico: ele entra no **campo
livre** do código de barras ou é exigido por regra do banco. A tupla `CAMPOS_POR_BANCO` lista os
nove:

```python
from pycobranca.contracts import CAMPOS_POR_BANCO
# ('data_documento', 'digito_conta', 'digito_agencia', 'digito_convenio',
#  'variacao', 'incremento', 'portfolio', 'posto', 'byte_idt')
```

Quem precisa de quê, nos dados de referência de cada banco:

| Banco | Campos |
|---|---|
| 004 Banco do Nordeste | `digito_conta` |
| 021 Banestes | `digito_conta`, `variacao` |
| 041 Banrisul | `digito_convenio` |
| 070 BRB | `incremento` |
| 136 Unicred | `digito_conta` |
| 422 Safra | `digito_conta`, `digito_agencia` |
| 745 Citibank | `portfolio` |
| 748 Sicredi | `posto`, `byte_idt` |
| 756 Sicoob | `variacao` |

`data_documento` vale para qualquer banco (é a data impressa no título). Os demais 11 bancos não
usam nenhum destes campos.

**Omitir um deles não levanta erro em todos os casos.** Banco do Nordeste, Banestes e Unicred
falham na montagem (campo livre com 24 dígitos em vez de 25); BRB, Safra e Sicredi barram na
validação. **O Citibank produz um código de barras diferente, sem exceção nenhuma** — com o
`portfolio` zerado, estruturalmente válido, DV recalculado e destino errado:

```
com portfolio:  74593153900000127503172006247107010999940225
sem portfolio:  74595153900000127503000006247107010999940225
                                  ^^^ 172 → 000
```

Por isso a ida e volta é testada nos 18 bancos (ver [Caminho de volta](#caminho-de-volta-boleto_de_api)).

## Contrato de dados verificado

O módulo [`pycobranca.contracts`](../pycobranca/contracts/) mantém o **contrato de dados** REST
alinhado e **testado automaticamente**, sem que a engine dependa de qualquer camada HTTP. Ele
oferece:

- **Serializadores** engine → schemas da API: `boleto_para_api(banco)` (→ `{"bank", "data"}` com
  `BoletoData`), `pagamento_para_api(pagamento)` (→ `Pagamento`), `remessa_para_api(remessa)` (→
  `RemessaRequest`) e `retorno_item_para_api(registro, layout="400")` (→ `RetornoItem`, com valores
  em centavos convertidos para reais e a ocorrência traduzida).
- **`boleto_de_api(payload)`** e **`tema_de_api(data)`** — o caminho de volta, contrato → engine.
- **`valida_contrato(dados, schema)`** — validador leve (obrigatórios, tipos, `enum`, itens de
  array via `$ref`) contra o contrato vendorizado.
- **`CONTRATO`** — os **13 schemas** (`BoletoData`, `RemessaRequest`, `Pagamento`, `Encargos`,
  `Mora`, `Multa`, `Desconto`, `RetornoItem`, `ExtratoOFX`, `TransacaoOFX`, `ItemFatura`,
  `FaturaCorpo`, `BlocoFatura`), versionados em `pycobranca/contracts/contrato_rest.json`.
- **Constantes de apoio**, para não duplicar listas do lado de fora: `SLUG_POR_CODIGO`
  (código FEBRABAN → slug do `bank`), `NOMES_DO_CONTRATO`, `TOTALIZADORES`, `CAMPOS_POR_BANCO` e
  `TEMA_DO_CONTRATO`.

Os **testes de contrato** (`tests/test_contrato_rest.py`) validam a serialização de boleto
para os **18 bancos**, além de remessa e retorno (usando as fixtures `.RET`), garantindo que os
artefatos permaneçam válidos conforme a API evolui:

```python
from pycobranca.bancos.itau import Itau
from pycobranca.contracts import boleto_para_api, valida_contrato

payload = boleto_para_api(
    Itau(
        valor="127.50",
        agencia="1234",
        conta="56789",
        carteira="109",
        nosso_numero="12345678",
        cedente="Empresa LTDA",
        cedente_documento="12345678000190",
        sacado="Cliente",
        sacado_documento="12345678909",
    )
)
valida_contrato(payload["data"], "BoletoData")  # levanta ErroDeContrato se divergir
# payload == {"bank": "itau", "data": {...}}
```

### Faixa de encargos (`BoletoData`)

Os cinco campos FEBRABAN viajam no contrato com **os mesmos nomes** que têm em `BancoBase` — não
há tradução nos dois sentidos. A tupla `TOTALIZADORES` expõe a lista:

```python
from pycobranca.contracts import TOTALIZADORES, boleto_para_api

TOTALIZADORES
# ('desconto_abatimento', 'outras_deducoes', 'mora_multa', 'outros_acrescimos', 'valor_cobrado')

boleto_para_api(boleto)["data"]
# {..., 'desconto_abatimento': 150.0, 'mora_multa': 8.0}
```

Campo não informado **some do payload** — boleto sem encargo sai idêntico ao que saía antes destes
campos existirem. `valor_cobrado` é serializado como foi informado, ou omitido: não há cálculo em
lugar nenhum, então `boleto_para_api` é projeção fiel do que o chamador montou.

> **Estes campos não são impressos no boleto.** A faixa da ficha sai em branco, porque quem a
> preenche é o caixa no ato do pagamento — ver
> [11 — Renderização](11-renderizacao.md#faixa-de-encargos-sempre-em-branco). No contrato eles
> servem para **trafegar o encargo entre sistemas**, que é outro problema: a regra que o pagador lê
> vai em `instrucao1`/`instrucao2`.

### Encargos na remessa (`Pagamento`)

Quando o `Pagamento` tem juros/mora, multa, desconto (1º/2º/3º), IOF ou abatimento, o schema
`Pagamento` ganha um objeto **`encargos`** (`{"mora", "multa", "descontos", "iof", "abatimento"}`),
emitido **apenas quando há encargo** — pagamentos sem encargo ficam com o payload inalterado.

```python
from datetime import date
from pycobranca.cnab import Pagamento
from pycobranca.contracts import pagamento_para_api, valida_contrato

pag = Pagamento(
    nosso_numero="12345678",
    data_vencimento=date(2026, 8, 15),
    valor=199.90,
    tipo_mora="2",
    percentual_mora=3.17,  # juros: taxa mensal (%)
    codigo_multa="2",
    percentual_multa=2.00,  # multa: 2%
    cod_desconto="1",
    valor_desconto=10.0,
    data_desconto=date(2026, 8, 1),
)
dados = pagamento_para_api(pag)
valida_contrato(dados, "Pagamento")
# dados["encargos"] == {
#   "mora": {"tipo": "2", "percentual": 3.17},
#   "multa": {"codigo": "2", "percentual": 2.0},
#   "descontos": [{"codigo": "1", "valor": 10.0, "data": "2026-08-01"}],
# }
```

Schemas: `Encargos`, `Mora`, `Multa` e `Desconto` (em `contrato_rest.json`).

### Documentos: CPF e **CNPJ alfanumérico**

Os campos `documento_cedente`, `sacado_documento` (`BoletoData`) e `documento_sacado` (`Pagamento`)
têm **`pattern`** no contrato, então um serviço HTTP rejeita formato inválido **antes** de chamar a
engine. O padrão aceita:

- **CPF** — 11 dígitos, com ou sem máscara (`529.982.247-25`);
- **CNPJ** — 14 posições, com ou sem máscara, sendo as **12 primeiras alfanuméricas** e os
  **2 DVs numéricos** (IN RFB 2.229/2024): `12ABC34501DE35` ou `12.ABC.345/01DE-35`.

```json
{"documento_cedente": "12ABC34501DE35", "sacado_documento": "529.982.247-25"}
```

O `pattern` valida apenas o **formato**; o **dígito verificador** é conferido pela engine
(`validar_cnpj`) na emissão. Ver [14 — Validação de campos](14-validacao-campos.md).

### Tema visual (faixa de marca)

Quatro campos do `BoletoData` descrevem a faixa de marca do boleto moderno. Eles são de
**apresentação**, não de domínio: não existem em `BancoBase`, então `boleto_para_api` nunca os
emite — é uma via de mão única, do contrato para a renderização. `tema_de_api(data)` faz a
tradução, porque contrato e renderizador usam vocabulários diferentes (o mapa é
`TEMA_DO_CONTRATO`):

| No contrato | No renderizador |
|---|---|
| `cor_marca` | `cor` |
| `logo_empresa` | `logo_texto` (e, por herança, `empresa`) |
| `marca_dagua` | `marca_dagua` |
| `rodape_contato` | `rodape` |

```python
from pycobranca.contracts import boleto_de_api, tema_de_api
from pycobranca.render import emite_boleto

emite_boleto(boleto_de_api(payload), tema=tema_de_api(payload["data"]))
```

`parcela_atual` e `total_parcelas`, quando vêm juntos, viram o texto `Parcela 2/12` na faixa.
Sem nenhum campo de tema, `tema_de_api` devolve `None` e o boleto sai sem faixa. O que cada chave
faz no desenho está em [11 — Renderização](11-renderizacao.md).

### Fatura (`BoletoData.itens` / `BoletoData.fatura`)

O mesmo schema `BoletoData` carrega o corpo da **fatura** — não há schema novo de requisição:

- **`itens`** — array de **`ItemFatura`** (`descricao`, `quantidade`, `valor_unitario`, `valor`):
  a tabela pronta.
- **`fatura`** — **`FaturaCorpo`** (`titulo` + `blocos`), onde cada **`BlocoFatura`** tem `tipo`
  (`tabela`, `campos`, `texto`, `total`, `separador`, `espaco`) e os campos daquele bloco.

```json
{
  "valor": 127.50, "...": "...",
  "fatura": {
    "titulo": "FATURA DE CONSUMO",
    "blocos": [
      {"tipo": "campos", "itens": [["Período", "01/08 a 31/08"]]},
      {"tipo": "tabela", "colunas": ["Descrição", "Total"],
       "linhas": [["Água", "63,00"]], "alinhamento": "lr"},
      {"tipo": "texto", "conteudo": "Leitura em <b>18/08</b>."},
      {"tipo": "total", "rotulo": "Total da fatura", "valor": 127.50}
    ]
  }
}
```

O `tipo` do bloco é validado por `enum`, então um serviço HTTP rejeita bloco desconhecido antes de
chamar a renderização. Detalhes de layout em [11 — Renderização](11-renderizacao.md).

> O terceiro nível da fatura (`fatura.desenhar`, um `callable` Python) **não faz parte do
> contrato** — só existe no uso em processo, por não ser serializável.

### Retorno curado (`RetornoItem`)

O `RegistroRetorno` da engine expõe os campos **crus** do arquivo (fidelidade total). Para a visão
curada da API — valores monetários em reais e ocorrência legível — use `retorno_item_para_api`:

```python
from pycobranca.cnab.retorno import Retorno
from pycobranca.contracts import retorno_item_para_api

retorno = Retorno.ler(upload.read())  # caminho, bytes ou objeto com .read()
itens = [retorno_item_para_api(r, layout=retorno.layout) for r in retorno.registros]
# {'nosso_numero': '00000011', 'valor_titulo': 40.0, 'valor_pago': 37.9,
#  'codigo_ocorrencia': '06', 'motivo_ocorrencia': 'Liquidação normal', ...}
```

## Caminho de volta: `boleto_de_api`

Receber um `BoletoData` e construir o título é uma chamada:

```python
from pycobranca.contracts import boleto_de_api, tema_de_api
from pycobranca.render import emite_boleto

boleto = boleto_de_api(payload)  # {"bank": ..., "data": {...}}
saida = emite_boleto(boleto, tema=tema_de_api(payload["data"]))

resposta = {"pdf_base64": b64(saida.pdf), **saida.to_dict()}
```

Ela valida contra o schema, resolve o slug, aplica as quatro traduções de nome, converte as datas
ISO para `date`, junta `instrucao1`/`instrucao2` na lista `instrucoes` e descarta os campos de
apresentação que o construtor não aceita (tema e fatura).

**A ida e volta é testada nos 18 bancos**: `boleto_de_api(boleto_para_api(b))` reproduz o mesmo
código de barras e a mesma linha digitável. É o que garante que os
[campos específicos de banco](#campos-especificos-de-banco) estejam todos no schema.

#### Entrada malformada

O payload vem de fora, então a fronteira é onde o lixo tem de parar. **Toda falha sai como
`PyCobrancaError`, nomeando o campo** — nada de `TypeError` do construtor ou de `ValueError` do
`fromisoformat` escapando de um `except` da biblioteca:

| No payload | O que você recebe |
|---|---|
| obrigatório ausente | `ErroDeContrato: BoletoData: campo obrigatório ausente/vazio: 'nosso_numero'` |
| `"data_vencimento": "15/08/2026"` | `ErroDeContrato: BoletoData.data_vencimento: '15/08/2026' não é uma data ISO 8601 (AAAA-MM-DD)` |
| `"valor": true` | `ErroDeContrato: BoletoData.valor: esperado number, recebido bool` |
| `"cor_do_papel": "azul"` | `ErroDeContrato: BoletoData.cor_do_papel: campo desconhecido para o banco Itaú (341)` |
| `"bank": "banco_x"` | `BancoNaoRegistrado` |
| carteira fora do banco | `BoletoInvalido`, com `.erros` |

O `bool` é o caso que passa despercebido: `isinstance(True, int)` é verdadeiro em Python, então um
validador ingênuo aceita `true` como `number` e o erro só aparece lá adiante, em `Decimal("True")`.

## O que o contrato não cobre

- **Não há cliente HTTP.** A biblioteca não fala rede; um SDK, se existir, é projeto de quem o
  escreve. Nenhum nome de cliente é importável de `pycobranca`.
- **`valida_contrato` confere forma, não regra bancária.** Ele aplica `required`, `type`, `enum`,
  `pattern` e itens de array — que é exatamente o conjunto de palavras-chave usado no
  `contrato_rest.json`. Carteira aceita pelo banco, largura de campo e DV são conferidos por
  `validar()` na engine, ver [14 — Validação de campos](14-validacao-campos.md).
- **O nível 3 da fatura (`fatura.desenhar`)** é um `callable` Python e não atravessa REST.

## Versionamento

`CONTRATO` é versionado em `pycobranca/contracts/contrato_rest.json` e mantido **em sincronia
manual** com o domínio. Os testes de contrato (`tests/test_contrato_rest.py`) prendem a
serialização ao schema, mas só conferem o que **está** no payload: **um campo novo em `BancoBase`
que não chegue ao `BoletoData` deixa o consumidor sem acesso ao recurso e não quebra a suíte
sozinho.** A omissão é invisível porque o payload continua válido — falta um campo que ninguém
declarou esperar.

Foi assim que a faixa de totalizadores e os nove campos específicos de banco ficaram de fora, com
o resultado descrito acima: **o Citibank sem `portfolio` produzia um código de barras
estruturalmente válido, com DV recalculado, e o destino errado.**

Quem acrescentar campo ao domínio acrescenta aqui também. Duas redes pegam o esquecimento hoje:
`test_contrato_hierarquia_erros.py` confere que os totalizadores estão declarados, e o teste de
ida e volta nos 18 bancos falha se um campo consumido pelo campo livre ficar de fora.
