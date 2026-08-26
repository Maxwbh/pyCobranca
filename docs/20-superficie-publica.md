---
description: >-
  Catálogo completo do que a PyCobrança entrega a quem a embute: cada módulo
  público, o que entra, o que sai e em que formato.
---

# 20 — Superfície pública

Esta página é o **catálogo do que a biblioteca entrega**. As outras páginas explicam *como* cada
recurso funciona; aqui está a lista do que existe — módulo a módulo, com o que entra, o que sai e
em que tipo.

Tudo que aparece aqui está no `__all__` do módulo correspondente e é coberto pela suíte. O que
não está aqui é interno e pode mudar sem aviso.

Para o que a biblioteca **não** faz — rede, disco, estado, numeração, agendamento — ver
[19 — Integração](19-integracao.md).

## Mapa em uma tela

| Módulo | Entrega |
|---|---|
| `pycobranca` | registro dos 19 bancos, versão, `banco_info` |
| `pycobranca.bancos` | as 19 classes de boleto e a base `BancoBase` |
| `pycobranca.render` | PDF (boleto, carnê, fatura), `emite_boleto`, logos, código de barras SVG |
| `pycobranca.pix` | BR Code EMV, CRC16, QR em SVG/matriz |
| `pycobranca.cnab` | remessa 400/240 (28 classes) e `Pagamento`/`PagamentoPix` |
| `pycobranca.cnab.retorno` | leitura de retorno 400/240 e rótulos de ocorrência |
| `pycobranca.ofx` | leitura de extrato OFX v1/v2 e conciliação |
| `pycobranca.contracts` | contrato REST: ida, volta e validação |
| `pycobranca.core` | CPF/CNPJ, módulo 10/11, fator de vencimento |
| `pycobranca.exceptions` | hierarquia única de erros |

Nenhum módulo depende de rede. As duas únicas dependências — `reportlab` (PDF) e `qrcode`
(imagem do QR) — entram no `pip install` e são Python puro, sem biblioteca de sistema. Boleto,
CNAB, OFX, PIX (EMV) e contrato não as importam: rodam só com a biblioteca padrão.

---

## 1. Boleto — `pycobranca.bancos`

`Bancos.find(codigo)` devolve a classe do banco; instanciá-la com os dados do título devolve o
boleto. Os 19 códigos aceitos estão em [05 — Bancos suportados](05-bancos-suportados.md).

### O que entra

Os campos do título, em quatro grupos:

| Grupo | Campos |
|---|---|
| **Obrigatórios** | `valor`, `nosso_numero`, `data_vencimento`, `cedente`, `cedente_documento`, `sacado`, `sacado_documento` |
| **Identificação da conta** | `agencia`, `conta`, `carteira`, `convenio`, `digito_agencia`, `digito_conta`, `digito_convenio` |
| **Impressão** | `numero_documento`, `data_documento`, `cedente_endereco`, `cedente_cidade`, `sacado_endereco`, `sacador_avalista`, `especie_documento`, `especie_moeda`, `aceite`, `quantidade`, `local_pagamento`, `instrucoes`, `demonstrativo`, `logo` |
| **Encargos** (contrato; não saem impressos) | `desconto_abatimento`, `outras_deducoes`, `mora_multa`, `outros_acrescimos`, `valor_cobrado` |
| **PIX** | `pix_copia_cola` (payload do banco), `pix_chave`, `pix_txid`, `pix_observacao` |
| **Específicos de banco** | `variacao`, `posto`, `byte_idt`, `portfolio`, `incremento`, `numero_contrato` |

Quais são obrigatórios **por banco** — e quais carteiras cada um aceita — está em
[14 — Validação de campos](14-validacao-campos.md) e na página do banco.

### O que sai

| Chamada | Tipo | Conteúdo |
|---|---|---|
| `.codigo_barras` | `str` | 44 posições, DV geral calculado |
| `.linha_digitavel` | `str` | 47 posições formatadas, com os DVs de campo |
| `.nosso_numero_formatado` | `str` | com o dígito e a máscara do banco |
| `.agencia_conta_formatado` | `str` | no formato de impressão do banco |
| `.campo_livre()` | `str` | 25 posições, montadas pela regra do banco |
| `.valor_centavos` | `int` | valor sem separador, para o código de barras |
| `.fator_vencimento` | `int` | fator FEBRABAN da data |
| `.digito_banco` | `str` | DV do código FEBRABAN |
| `.suporta_pix` | `bool` | se o **segmento PIX do CNAB** daquele banco está implementado |
| `.carteiras` | `tuple` | carteiras aceitas pelo banco |
| `.regras_campos` | `dict` | tamanhos mín./máx. por campo, para validação prévia |
| `.validar()` | — | levanta `BoletoInvalido` com `.erros` (lista) |
| `.to_dict()` | `dict` | 13 chaves — projeção enxuta do título |
| `.contexto_render()` | `dict` | o dicionário que os renderizadores consomem |

`contexto_render()` devolve as chaves `banco`, `beneficiario`, `pagador`, `carteira`,
`codigo_barras`, `linha_digitavel`, `nosso_numero`, `documento`, `vencimento`,
`valor_documento`, `quantidade`, `especie_moeda`, `local_pagamento`, `instrucoes`,
`demonstrativo`, `sacador_avalista`, `totalizadores` e `pix`. Já vem com os valores
**formatados para impressão** (`"1.279,50"`, `"10/09/2026"`). `totalizadores` é a exceção: os cinco
campos vêm sempre vazios, porque a faixa de encargos é preenchida pelo caixa no ato do pagamento.

---

## 2. PDF — `pycobranca.render`

`reportlab` já vem no `pip install pycobranca`. Numa instalação em que ele tenha sido removido,
as funções levantam `DependenciaAusente` em vez de `ImportError` cru.

| Função | Devolve | Para quê |
|---|---|---|
| `emite_boleto(boleto, modelo="moderno", *, tema=None)` | `BoletoEmitido` | **PDF e dados numa chamada só** |
| `render_boleto_pdf(contexto, modelo="moderno")` | `bytes` | boleto A4 |
| `render_carne_pdf(contexto)` | `bytes` | carnê, 3 parcelas por página |
| `render_fatura_pdf(contexto, modelo="moderno")` | `bytes` | demonstrativo + boleto na mesma página |
| `desenha_boleto(canvas, contexto, modelo="moderno")` | — | desenha num canvas seu (composição) |
| `logo_do_banco(codigo)` | `bytes \| None` | PNG do banco, se houver |
| `bancos_com_logo()` | `tuple` | os 19 códigos com logo empacotado |
| `interleaved_2of5_svg(codigo, *, altura, unidade, cor)` | `str` | código de barras isolado, em SVG |
| `sequencia_i2of5(codigo)` | `list[tuple[bool, int]]` | barras/espaços crus, para desenhar você mesmo |

**Modelos de boleto:** `"moderno"` (padrão) e `"classico"`. Nome fora do catálogo levanta
`ModeloInvalido`. Detalhes de layout, tema e fatura em [11 — Renderização](11-renderizacao.md).

### `BoletoEmitido`

O retorno de `emite_boleto` — o título é montado **uma vez** e o PDF sai junto dos dados, com a
garantia de que os dois descrevem o mesmo boleto:

| Campo | Tipo |
|---|---|
| `.pdf` | `bytes` |
| `.linha_digitavel` | `str` |
| `.codigo_barras` | `str` |
| `.nosso_numero` | `str` |
| `.vencimento` | `str` (`dd/mm/aaaa`) |
| `.valor_documento` | `str` (`1.279,50`) |
| `.pix_copia_cola` | `str \| None` |
| `.pix_vinculado` | `bool \| None` — `True` se o QR liquida o título; `False` se é PIX avulso |
| `.totalizadores` | `dict[str, str]` — sempre vazios: a faixa é do caixa |
| `.to_dict()` | `dict` — tudo, menos o PDF |

```python
from pycobranca.render import emite_boleto

emitido = emite_boleto(boleto, modelo="moderno")
resposta = emitido.to_dict()  # JSON-serializável
anexo = emitido.pdf  # bytes
```

---

## 3. PIX / Bolepix — `pycobranca.pix`

Python puro; só o QR em SVG precisa de `qrcode`.

| Símbolo | Devolve |
|---|---|
| `PixPayload(chave, nome, cidade, valor, txid, info_adicional)` | agregado do BR Code |
| `.br_code()` | `str` — EMV completo, com CRC16 |
| `crc16_ccitt(dados)` | `str` — 4 dígitos hexadecimais |
| `qr_matrix(payload)` | `list[list[int]]` — a matriz crua, sem renderizador |
| `qr_svg(payload, *, escala, cor)` | `str` |
| `PixInvalido` | erro de payload |

No boleto há **dois caminhos**, e eles não são equivalentes:

| Campo | QR gerado | Ao pagar |
|---|---|---|
| `pix_copia_cola` | o payload que o **banco** devolveu | credita **e dá baixa** no boleto |
| `pix_chave` | BR Code estático, montado aqui | credita, mas o **título fica em aberto** |

O primeiro tem precedência. `contexto_render()["pix"]["vinculado"]` e
`BoletoEmitido.pix_vinculado` dizem qual está no boleto. Sem `pix_txid`, o identificador é
derivado do nosso número (`txid_do_titulo()`), que é o que permite conciliar o QR avulso pelo
OFX. Ver [07 — PIX/Bolepix](07-pix.md).

---

## 4. Remessa CNAB — `pycobranca.cnab`

**28 classes de remessa**, cobrindo 14 bancos em CNAB 400 e 7 em CNAB 240 (as variantes `*Pix`
acrescentam o segmento PIX):

- **400:** `RemessaItau400`, `RemessaBradesco400`, `RemessaBancoBrasil400`, `RemessaSantander400`,
  `RemessaSicoob400`, `RemessaUnicred400`, `RemessaBanrisul400`, `RemessaBancoNordeste400`,
  `RemessaBancoBrasilia400`, `RemessaCitibank400`, `RemessaCredisis400`, `RemessaBancoC6_400`,
  `RemessaInter400`, `RemessaSafra400` — com PIX: Itaú, Bradesco, Santander e C6.
- **240:** `RemessaAilos240`, `RemessaBancoBrasil240`, `RemessaCaixa240`, `RemessaSantander240`,
  `RemessaSicoob240`, `RemessaSicredi240`, `RemessaUnicred240`
  — com PIX: Banco do Brasil, Caixa e Sicoob.

| Chamada | Devolve |
|---|---|
| `remessa.gera_arquivo()` | `str` — arquivo inteiro, ASCII, com `\r\n` |
| `remessa.validar()` | — levanta `BoletoInvalido` |
| `remessa.monta_header()` / `monta_detalhe(p)` / `monta_trailer()` | `str` — registro a registro |

**`Pagamento`** é o título dentro da remessa: 42 campos, incluindo a faixa completa de encargos
(mora por valor/dia ou taxa mensal, multa, três descontos, IOF, abatimento, protesto e baixa).
**`PagamentoPix`** acrescenta 10 campos do segmento PIX (`tipo_chave_dict`, `txid`, limites de
valor/percentual). Ambos têm `.validar()`.

A saída é validada **byte a byte** contra arquivos de referência —
ver [17 — Compatibilidade](17-compatibilidade.md) e [06 — CNAB](06-cnab.md).

---

## 5. Retorno CNAB — `pycobranca.cnab.retorno`

```python
from pycobranca.cnab import Retorno

Retorno.ler("CB250807.RET")  # caminho
Retorno.ler(upload.read())  # bytes — sem arquivo temporário
Retorno.ler(arquivo_aberto)  # qualquer objeto com .read()
```

Layout (400/240) e banco são detectados pelo próprio arquivo. Arquivo vazio ou sem header
reconhecível levanta `RetornoInvalido`.

| Chamada | Devolve |
|---|---|
| `Retorno.ler(fonte, layout=None)` | `Retorno` — com `.layout`, `.codigo_banco` e `.registros` |
| `Retorno.ler_linhas(linhas, layout=None)` | `Retorno`, a partir de linhas já lidas |
| `.registros` | `list[RegistroRetorno]` |
| `.to_dict(compact=True)` | `list[dict]` — JSON-serializável |
| `.descricao_ocorrencia(registro)` | `str \| None` |
| `descreve_ocorrencia(codigo, layout="400")` | `str \| None` |

**`RegistroRetorno`** traz 43 campos por título — `nosso_numero`, `codigo_ocorrencia`,
`motivo_ocorrencia`, `data_liquidacao`, `data_credito`, `valor_titulo`, `valor_recebido`,
`juros_mora`, `valor_tarifa`, `desconto`, `valor_abatimento`, `banco_recebedor`, além dos campos
PIX (`tipo_chave_dict`, `codigo_chave_dict`, `txid`) — e `.to_dict()`.

**16 dos 19 bancos** têm layout de retorno próprio (14 em 400, 5 em 240, com sobreposição); os
demais — Banestes (021), HSBC (399) e Citibank (745) — caem no layout de reserva, que lê o arquivo
mas pode divergir em campos específicos e emite o aviso `LayoutGenerico` dizendo isso.

---

## 6. Extrato OFX — `pycobranca.ofx`

| Chamada | Devolve |
|---|---|
| `Extrato.ler(fonte, *, somente_creditos=False)` | `Extrato` |
| `Extrato.parse(texto, *, somente_creditos=False)` | `Extrato` |
| `.transacoes` | `list[Transacao]` — tudo, na ordem do arquivo |
| `.creditos` / `.debitos` | `list[Transacao]` — filtradas pelo sinal |
| `.saldo_valor`, `.saldo_data`, `.periodo`, `.agencia`, `.conta_numero`, `.conta_tipo`, `.org`, `.fid` | metadados do extrato |
| `.to_dict()` | `dict` |
| `concilia(extrato, nossos_numeros, *, somente_creditos=True)` | `Conciliacao` |
| `extrair_nosso_numero(memo, banco_org)` | `str \| None` |

**`Transacao`**: `fitid`, `tipo`, `data`, `valor`, `memo`, `name`, `checknum`, `refnum` e
`nosso_numero_extraido`. **`Conciliacao`**: `conciliadas`, `nao_conciliadas`, `pendentes`.

Aceita OFX v1 (SGML) e v2 (XML). Arquivo que não é OFX levanta `OFXInvalido`.
Ver [13 — Extrato OFX](13-ofx.md).

---

## 7. Contrato REST — `pycobranca.contracts`

Serialização e validação sem dependência HTTP: quem expõe a biblioteca por rede não precisa
inventar o formato do payload nem repetir a validação.

| Símbolo | Para quê |
|---|---|
| `boleto_para_api(boleto)` | objeto → `{"bank": ..., "data": {...}}` |
| `boleto_de_api(payload)` | payload → objeto do banco (o caminho de volta) |
| `tema_de_api(data)` | extrai o tema visual do payload |
| `pagamento_para_api(pagamento)` | `Pagamento` → `dict` |
| `remessa_para_api(remessa)` | remessa → `dict` |
|  `retorno_item_para_api(registro, layout="400", banco=None)` | `RegistroRetorno` → `dict` |
| `openapi_de(paths, *, info, servers, schemas)` | `dict` | documento OpenAPI com **seus paths** e os schemas daqui |
| `valida_contrato(dados, schema)` | valida contra o schema; levanta `ErroDeContrato` |
| `CONTRATO` | o documento OpenAPI 3.0, como `dict` |

**13 schemas:** `BoletoData`, `RemessaRequest`, `Pagamento`, `Encargos`, `Mora`, `Multa`,
`Desconto`, `RetornoItem`, `ExtratoOFX`, `TransacaoOFX`, `ItemFatura`, `FaturaCorpo`,
`BlocoFatura`.

**Constantes de apoio**, para não duplicar listas do lado de fora: `SLUG_POR_CODIGO`
(código FEBRABAN → slug do payload), `TOTALIZADORES`, `CAMPOS_POR_BANCO`, `NOMES_DO_CONTRATO`
(nomes que divergem entre domínio e contrato) e `TEMA_DO_CONTRATO`.

A ida e volta `boleto_para_api` → `boleto_de_api` é testada nos **19 bancos**, com o código de
barras conferido nas duas pontas. Ver [04 — Contrato REST](04-api-rest.md).

---

## 8. Utilitários — `pycobranca.core`

Python puro, sem dependência: úteis para validar entrada antes de montar o título.

| Função | Devolve |
|---|---|
| `validar_cpf(v)` / `validar_cnpj(v)` | `bool` — CNPJ aceita a forma alfanumérica |
| `formatar_cpf(v)` / `formatar_cnpj(v)` | `str` com máscara |
| `modulo10(seq)` / `modulo11_codigo_barras(seq)` | `int` |
| `fator_vencimento(data)` | `int` |

Em `pycobranca.core.documentos` há ainda `so_alfanumerico`, `cnpj_e_alfanumerico`, `dv_cnpj` e
`formatar_documento` — ver [18 — CNPJ alfanumérico](18-cnpj-alfanumerico.md).

---

## 9. Erros — `pycobranca.exceptions`

Uma hierarquia só: **`except PyCobrancaError` cobre a biblioteca inteira**, e cada exceção também
herda do erro embutido correspondente, então quem já tratava por `ValueError`/`KeyError` continua
funcionando.

`PyCobrancaError`, `BoletoInvalido` (com `.erros`), `BancoNaoRegistrado`, `RetornoInvalido`,
`OFXInvalido`, `DadosInvalidos`, `ModeloInvalido`, `DependenciaAusente`, além de
`InvalidBarcodeError` (`render`), `ErroDeContrato` (`contracts`) e `PixInvalido` (`pix`).

Quando cada uma aparece: [14 — Validação de campos](14-validacao-campos.md).

---

## As três fronteiras de um serviço

Quem expõe a biblioteca por HTTP atravessa três fronteiras, e cada uma tem uma função pronta —
não é preciso escrever tradução à mão:

| Fronteira | Chamada |
|---|---|
| **JSON → objeto** | `boleto_de_api(payload)` (+ `tema_de_api(payload["data"])`) |
| **objeto → PDF + dados** | `emite_boleto(boleto, modelo)` → `BoletoEmitido` |
| **upload → dados** | `Retorno.ler(bytes)` / `Extrato.ler(bytes)` |

```python
from pycobranca.contracts import boleto_de_api, tema_de_api, valida_contrato
from pycobranca.render import emite_boleto

valida_contrato(payload["data"], "BoletoData")
boleto = boleto_de_api(payload)
emitido = emite_boleto(boleto, payload.get("modelo", "moderno"), tema=tema_de_api(payload["data"]))

# emitido.pdf → anexo;  emitido.to_dict() → corpo JSON
```

Exemplo completo e executável: [`examples/11_servico_rest.py`](https://github.com/Maxwbh/pyCobranca/tree/main/examples).

## Capacidade por banco, em números

| Recurso | Bancos |
|---|---|
| Boleto (barras, linha digitável, PDF) | **18** |
| PIX / Bolepix | **7** |
| Remessa CNAB 400 | **12** |
| Remessa CNAB 240 | **7** |
| Retorno com layout próprio | **14** |
| Logo empacotado | **17** |

A matriz banco a banco está em [05 — Bancos suportados](05-bancos-suportados.md).
