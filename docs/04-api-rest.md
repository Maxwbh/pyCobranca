# 04 — Contrato de dados para API REST

A PyCobrança serializa seus artefatos (boleto, remessa, retorno) para um **contrato de dados JSON**
(OpenAPI 3.0), pronto para ser exposto por um serviço REST. A relação acontece de duas formas:

1. **Como produtora de artefatos** — gera boletos, remessa e retorno em JSON compatível com o
   contrato, permitindo que qualquer serviço REST reutilize a lógica.
2. **Como consumidora** — um **cliente Python** (`clients/`) pode chamar um serviço remoto que
   exponha o mesmo contrato.

## Endpoints de referência

Endpoints típicos de um serviço de cobrança. Os prioritários para o SDK:

| Endpoint | Método | Uso |
|----------|:------:|-----|
| `/api/boleto` | GET | Gera boleto (PDF/JPG/PNG/TIF), opcionalmente base64. |
| `/api/boleto/multi` | POST | Geração em lote. |
| `/api/remessa` | POST | Gera arquivo de remessa CNAB 240/400. |
| `/api/retorno` | POST | Faz parsing de arquivo de retorno CNAB → JSON. |
| `/api/bancos` | GET | Lista bancos suportados e capacidades. |
| `/api/ofx/parse` | POST | Extrai transações de extrato OFX (conciliação). |
| `/api/docs` | GET | Swagger UI (OpenAPI 3.0). |

## Contrato de dados (boleto)

Campos principais aceitos pela API — a PyCobrança usa os mesmos nomes na serialização para
minimizar atrito:

```json
{
  "banco": "341",
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
```

Campos opcionais de temização (logo, cor da marca, marca d'água, fonte) e `template` (`carne`)
são repassados quando presentes.

> **Nota de contrato:** no endpoint `GET /api/boleto`, o banco vai no parâmetro `bank` (slug,
> ex.: `itau`) e os demais campos no parâmetro `data` (schema `BoletoData`, sem o campo `banco`).

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
  "banco": "341", "valor": 127.50, "...": "...",
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

## Cliente Python (design alvo) — **projeto separado**

> **Decisão de escopo:** o SDK HTTP abaixo **não faz parte deste repositório** nem do pacote
> `pycobranca` — seria projeto próprio. O código a seguir é ilustração do contrato, não API
> existente: nenhum destes nomes é importável hoje. A biblioteca não fala HTTP.

```python
# Ilustrativo — este módulo não existe.
from cobranca_client import CobrancaClient

client = CobrancaClient(base_url="https://sua-instancia/api")

# Gerar boleto remotamente
pdf_bytes = client.boleto(
    banco="341",
    valor=127.50,
    cedente="Empresa Exemplo LTDA",
    documento_cedente="12345678000190",
    agencia="1234",
    conta_corrente="56789",
    carteira="109",
    nosso_numero="12345678",
    data_vencimento="2026-08-15",
    sacado="Cliente Final",
    sacado_documento="12345678909",
    formato="pdf",
)

# Gerar remessa
remessa = client.remessa(banco="341", tipo="cnab400", pagamentos=[...])

# Parsear retorno
ocorrencias = client.retorno(arquivo=open("retorno.ret", "rb"))

# Listar bancos
bancos = client.bancos()
```

## Estratégia de compatibilidade

- **Mesmos nomes de campos** entre `Boleto.to_dict()` e o corpo esperado pela API.
- **Testes de contrato** contra o `openapi.json` de referência, garantindo que o cliente e os
  artefatos permaneçam válidos conforme a API evolui.
- **Modo local vs. remoto:** o mesmo código de aplicação pode alternar entre gerar o boleto
  localmente (`Boleto.to_pdf`) ou remotamente (`client.boleto`) conforme configuração.

## Autenticação

O cliente Python deve suportar cabeçalhos de autenticação (`Authorization`) e `timeout`
configuráveis para uso em produção atrás de gateway.

## Caminho de evolução

Os testes de contrato validam o SDK. Em uma etapa futura (fora do escopo atual), um serviço REST
poderia oferecer um backend opcional baseado em PyCobrança para deployments Python-only.
