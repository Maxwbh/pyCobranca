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

O mapa código FEBRABAN → slug é `SLUG_POR_CODIGO`. Os nomes dentro de `data` acompanham os campos
de `BancoBase`, com quatro exceções que a serialização traduz — a tupla `NOMES_DO_CONTRATO` é a
fonte:

| No contrato | No construtor |
|---|---|
| `conta_corrente` | `conta` |
| `documento_cedente` | `cedente_documento` |
| `chave_pix` | `pix_chave` |
| `txid` | `pix_txid` |

> **`additionalProperties` é permissivo.** `valida_contrato` ignora campo desconhecido em vez de
> recusá-lo, então um `data` com `banco` dentro **passa** — e o banco declarado ali seria
> silenciosamente descartado. Quem monta o payload à mão precisa conferir a forma acima.

## Contrato de dados verificado

O módulo [`pycobranca.contracts`](../pycobranca/contracts/) mantém o **contrato de dados** REST
alinhado e **testado automaticamente**, sem que a engine dependa do serviço HTTP (o SDK é projeto à
parte). Ele oferece:

- **Serializadores** engine → schemas da API: `boleto_para_api(banco)` (→ `{"bank", "data"}` com
  `BoletoData`), `pagamento_para_api(pagamento)` (→ `Pagamento`), `remessa_para_api(remessa)` (→
  `RemessaRequest`) e `retorno_item_para_api(registro)` (→ `RetornoItem`, com valores em centavos
  convertidos para reais e a ocorrência traduzida).
- **`valida_contrato(dados, schema)`** — validador leve (obrigatórios, tipos, `enum`, itens de
  array via `$ref`) contra o contrato vendorizado.
- **`CONTRATO`** — fragmento curado de um `openapi.yaml` de referência (**v1.5.0**), versionado em
  `pycobranca/contracts/contrato_rest.json` e mantido em sincronia manual com o upstream.
- **`SLUG_POR_CODIGO`** — mapa código FEBRABAN → slug do banco (`bank`).

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

### Faixa de totalizadores (`BoletoData`)

Os cinco campos FEBRABAN impressos no boleto viajam no contrato com **os mesmos nomes** que têm em
`BancoBase` — não há tradução nos dois sentidos. A tupla `TOTALIZADORES` expõe a lista:

```python
from pycobranca.contracts import TOTALIZADORES, boleto_para_api

TOTALIZADORES
# ('desconto_abatimento', 'outras_deducoes', 'mora_multa', 'outros_acrescimos', 'valor_cobrado')

boleto_para_api(boleto)["data"]
# {..., 'desconto_abatimento': 150.0, 'mora_multa': 8.0}
```

Campo não informado **some do payload** — boleto sem encargo sai idêntico ao que saía antes destes
campos existirem. `valor_cobrado` é serializado como foi informado (ou omitido); o total calculado
a partir dos outros quatro é detalhe de renderização e vive em `contexto_render()`, não aqui —
assim `boleto_para_api` continua sendo uma projeção fiel do que o chamador montou.

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

retorno = Retorno.ler("retorno.ret")
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
ISO para `date` e descarta os campos de apresentação que o construtor não aceita. Levanta
`ErroDeContrato` (schema), `BancoNaoRegistrado` (slug desconhecido) ou `BoletoInvalido` (regra do
banco).

**A ida e volta é testada nos 18 bancos**: `boleto_de_api(boleto_para_api(b))` reproduz o mesmo
código de barras e a mesma linha digitável. É o que garante que os campos consumidos pelo campo
livre — `portfolio`, `incremento`, `byte_idt`, `digito_conta` e os demais de
`CAMPOS_POR_BANCO` — estejam todos no schema.

> `agencia` e `conta_corrente` **não são obrigatórios**: o Santander identifica o cedente pelo
> convênio e a Caixa pelo código do beneficiário. A exigência por banco é conferida por `validar()`
> na engine — ver [14 — Validação de campos](14-validacao-campos.md).

## O que o contrato não cobre

- **Não há cliente HTTP.** A biblioteca não fala rede; um SDK, se existir, é projeto de quem o
  escreve. Nenhum nome de cliente é importável de `pycobranca`.
- **`valida_contrato` confere forma, não regra bancária.** Ele aplica `required`, `type`, `enum`,
  `pattern` e itens de array — que é exatamente o conjunto de palavras-chave usado no
  `contrato_rest.json`. Carteira aceita pelo banco, largura de campo e DV são conferidos por
  `validar()` na engine, ver [14 — Validação de campos](14-validacao-campos.md).
- **O nível 3 da fatura (`fatura.desenhar`)** é um `callable` Python e não atravessa REST.

## Versionamento

`CONTRATO` é um fragmento curado, versionado em `pycobranca/contracts/contrato_rest.json` e
mantido **em sincronia manual**. Os testes de contrato (`tests/test_contrato_rest.py`) prendem a
serialização ao schema: um campo novo em `BancoBase` que não chegue ao `BoletoData` não quebra a
suíte sozinho — por isso, ao acrescentar campo ao domínio, acrescente-o também aqui.
