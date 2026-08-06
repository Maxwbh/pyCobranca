# 06 — CNAB (Remessa e Retorno)

CNAB (Centro Nacional de Automação Bancária) é o padrão FEBRABAN para troca de arquivos entre
empresa e banco. A PyCobrança implementa os **dois layouts** de uso geral na cobrança registrada:

| Layout | Tamanho do registro | Uso típico | Status |
|--------|:-------------------:|------------|:---:|
| **CNAB 240** | 240 posições | Padrão FEBRABAN mais recente, estrutura em lotes. | ✅ |
| **CNAB 400** | 400 posições | Layout legado por banco, ainda muito usado. | ✅ |
| CNAB 444 | 444 posições | Variante do Itaú — o 400 acrescido de 44 posições de mensagem. | 🚧 |

!!! warning "CNAB 444 ainda não é implementado"
    O 444 é uma **variante do Itaú**: o registro de 400 posições acrescido de 44 para mensagem no
    boleto. Não há suporte na PyCobrança — nem na remessa, nem no retorno. Está registrado no
    [roadmap](02-roadmap-modernizacao.md) e entra sob o mesmo critério dos demais layouts: manual
    oficial com exemplo numérico validável, e comparação byte a byte contra vetor de referência.

> **Status (Fase 2):** remessa **CNAB 400 implementada para 12 bancos** (Itaú, Bradesco, Banco do
> Brasil, Santander, Sicoob, Unicred, Banrisul, Banco do Nordeste, BRB/DCB, Citibank, CrediSIS e
> C6) e **CNAB 240 para 7 bancos** (Ailos, Banco do Brasil, Caixa, Santander, Sicoob, Sicredi e
> Unicred), todas validadas **byte a byte** contra vetores de referência (fixtures congeladas em
> `tests/fixtures/`; ver [`docs/bancos/`](bancos/README.md)).
>
> **Bolepix na remessa (Fase 4):** com um `PagamentoPix`, a remessa acrescenta o **registro tipo 8**
> (CNAB 400: Itaú, Bradesco, C6, Santander) ou o **segmento Y-03** (CNAB 240: Banco do Brasil,
> Caixa, Sicoob) após cada título — classes `Remessa*Pix`, validadas byte a byte.

## Conceitos

- **Remessa:** arquivo gerado pela empresa e enviado ao banco solicitando registro/baixa/alteração
  de títulos. Fluxo: `Boleto[] → registros → string do arquivo`.
- **Retorno:** arquivo devolvido pelo banco com o resultado do processamento (liquidação,
  rejeição, baixa). Fluxo: `string do arquivo → registros → list[dict]`.

## Estrutura do subsistema

```
cnab/
├── pagamento.py          # título a registrar (campos + formatadores CNAB)
├── formatacao.py         # format_size / format_valor / remover_acentos (fiéis ao Ruby)
├── cnab400/
│   ├── base.py           # header/detalhe/trailer + gera_arquivo (400 posições)
│   └── <banco>.py        # RemessaXxx400 (12 bancos)
├── cnab240/
│   ├── base.py           # header arq/lote + segmentos P/Q/R + trailers (240 posições)
│   └── <banco>.py        # RemessaXxx240 (7 bancos)
└── retorno/
    ├── base.py           # RegistroRetorno + extração posicional + motivo
    ├── cnab400.py        # mapas por banco (header = código nas pos. 76–78)
    ├── cnab240.py        # combinação dos segmentos T/U (header = código nas pos. 0–2)
    └── ocorrencias.py    # rótulos legíveis dos códigos de ocorrência (convenience)
```

## Retorno — status (Fase 3)

> **Implementado e validado campo a campo** contra vetores de referência para 11 arquivos `.RET`.
> **CNAB 400**: Itaú, Bradesco, Banco do Brasil, Santander (com campos PIX), Banco do Nordeste,
> Banrisul, CrediSIS, C6, Unicred e BRB. **CNAB 240**: base/Caixa, Santander, Ailos, Sicredi e
> Sicoob (dois segmentos, **T** = dados gerais e **U** = valores, combinados em um registro).
> `Retorno.ler(caminho)` detecta o layout pelo tamanho do registro e o banco pelo header.

### Layouts declarativos

Cada registro é descrito por uma tabela de campos posicionais (início, fim, tipo, formato,
default). Isso permite testar posições isoladamente e reusar definições entre bancos.

```python
# Exemplo conceitual de definição posicional (layout declarativo)
HEADER_ARQUIVO_240 = [
    Campo("banco", 1, 3, tipo="num"),
    Campo("lote", 4, 7, tipo="num", default="0000"),
    Campo("tipo_registro", 8, 8, tipo="num", default="0"),
    # ...
    Campo("nome_empresa", 73, 102, tipo="alfa"),
    # ...
]
```

## Estrutura CNAB 240 (em lotes)

```
Header de Arquivo        (registro 0)
  Header de Lote         (registro 1)
    Detalhe Segmento P   (registro 3) ─┐ título
    Detalhe Segmento Q   (registro 3) ─┤ sacado
    Detalhe Segmento R   (registro 3) ─┘ multa/desconto/PIX
  Trailer de Lote        (registro 5)
Trailer de Arquivo       (registro 9)
```

## Estrutura CNAB 400 (por registro)

```
Header       (tipo 0)
Detalhe      (tipo 1)  — um por título
...
Trailer      (tipo 9)  — totais
```

## Remessa — API alvo

```python
from pycobranca.cnab.remessa import Remessa

remessa = Remessa(
    banco="341",
    layout="cnab400",
    cedente="Empresa Exemplo LTDA",
    documento_cedente="12345678000190",
    agencia="1234",
    conta="56789",
    boletos=[boleto1, boleto2, ...],
)
conteudo = remessa.gerar()  # -> str (arquivo)
remessa.salvar("CB240723.REM")
```

## Encargos (juros/mora, multa, desconto, IOF, abatimento)

Cada encargo do `Pagamento` é um **trio** *código/tipo → valor → data* (a data é opcional):

| Encargo | Código/tipo | Valor | Data |
|---|---|---|---|
| **Multa** | `codigo_multa` (`0`=isento, `1`=valor fixo, `2`=percentual) | `percentual_multa` (%) | `data_multa` |
| **Juros/Mora** | `tipo_mora` (`1`=valor/dia, `2`=taxa mensal %, `3`=isento) | `valor_mora` (R$, tipo 1) · `percentual_mora` (%, tipo 2) | `data_mora` |
| **Desconto** 1º/2º/3º | `cod_desconto` / `cod_segundo_desconto` / `cod_terceiro_desconto` | `valor_desconto` / `valor_segundo_desconto` / `valor_terceiro_desconto` | `data_desconto` / `data_segundo_desconto` / `data_terceiro_desconto` |
| **IOF** | — | `valor_iof` | — |
| **Abatimento** | — | `valor_abatimento` | — |

Todos os campos são **opcionais** e têm default neutro (`"0"`/`0.0`/`None`); sem informá-los, o
arquivo sai idêntico ao anterior (encargos zerados).

**Semântica por layout:**

- **CNAB 240** — segmento **P**: `tipo_mora` + data de mora + valor/percentual de mora (percentual
  quando `tipo_mora == "2"`, conforme FEBRABAN "Taxa Mensal") + 1º desconto + IOF + abatimento.
  Segmento **R**: 2º e 3º desconto + multa (código + data + percentual). As **datas de mora e multa**
  usam o campo informado; na ausência, caem para o **vencimento** (Caixa e Sicredi/Unicred usam
  **vencimento + 1 dia**), como prevê o padrão FEBRABAN.
- **CNAB 400** — a multa é sempre **percentual** (`percentual_multa`); a mora é **valor ao dia**
  (`valor_mora`). Larguras variam por banco (ex.: Sicoob 6, Banrisul 12, Brasília/DCB 14). Só o
  **C6** usa `data_mora` no detalhe; os demais 400 não carregam data de mora.

> Observação: no padrão FEBRABAN **não existe "valor de multa"** monetário — a multa é sempre
> percentual. O método `Pagamento.formata_valor_multa` é mantido apenas por compatibilidade e é um
> alias de `formata_percentual_multa`.

### Suporte por banco

O `Pagamento` sempre aceita os campos; eles entram no arquivo onde o layout tem posição.

**CNAB 240** — suporte **completo e uniforme** (segmentos P/R):

| Banco (CNAB 240) | Mora (valor/%) | Multa | Desc. 1º | Desc. 2º | Desc. 3º | IOF | Abat. |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Banco do Brasil (001) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Caixa (104) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Santander (033) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sicoob (756) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sicredi (748) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Unicred (136) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ailos (085) | ✅ | ✅⁴ | ✅ | ✅ | ✅ | ✅ | ✅ |

**CNAB 400** — varia por layout do banco:

| Banco (CNAB 400) | Mora | Multa | Desc. 1º | Desc. 2º | IOF | Abat. |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Santander (033) | ✅ | ✅ | ✅ | 📅² | ✅ | ✅ |
| Bradesco (237) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| Sicoob (756) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| Banrisul (041) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| Banco do Nordeste (004) | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| C6 (336) | ✅ | ✅ | ✅ | — | — | ✅ |
| Unicred (136) | ✅ | ✅ | ✅ | — | — | ✅ |
| CrediSIS (097) | ✅ | ✅ | ✅³ | — | — | — |
| Itaú (341) | ✅ | 📝¹ | ✅ | — | ✅ | ✅ |
| Banco do Brasil (001) | ✅ | 📝¹ | ✅ | — | ✅ | ✅ |
| Citibank (745) | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| BRB/Brasília (070) | ✅ | — | ✅ | — | — | ✅ |

Legenda: ✅ campo posicional na remessa · — sem campo no layout · **Desc. 3º** apenas no CNAB 240.
📝¹ Itaú/BB (400): multa vai por **instrução** (código), não como percentual posicional.
📅² Santander (400): 2º desconto só a **data**. ³ CrediSIS: 1º desconto **sem** campo de data.
⁴ Ailos (240): segmento R (multa + 2º/3º desconto) emitido só quando há multa.
Banestes (021), HSBC (399) e Safra (422) só emitem boleto (sem remessa CNAB).

## Retorno — API

```python
from pycobranca.cnab.retorno import Retorno

retorno = Retorno.ler("retorno.ret")  # layout e banco detectados automaticamente
for registro in retorno.registros:
    print(
        registro.nosso_numero,
        registro.codigo_ocorrencia,
        retorno.descricao_ocorrencia(registro),
        registro.valor_recebido,
        registro.data_credito,
    )

# Serialização JSON-friendly para conciliação
dados = retorno.to_dict()  # list[dict], nulos removidos
```

> **Validação:** `Retorno.ler` levanta `RetornoInvalido` para um arquivo vazio ou sem header de
> banco reconhecível (em vez de devolver lista vazia). Ver
> [contrato de erros](14-validacao-campos.md).

Os valores são devolvidos como **strings cruas** do arquivo (ex.: `valor_recebido`
`"0000000003790"` = R$ 37,90; datas no formato do banco), preservando fidelidade ao retorno; a
interpretação numérica/monetária fica a cargo do consumidor (aplicação).

## Agrupamento determinístico (remessa em lote)

Ao gerar remessa a partir de vários títulos, o agrupamento é **determinístico**: um arquivo CNAB
**nunca** mistura banco, layout, convênio, carteira ou conta incompatíveis. Quando a entrada
contém títulos heterogêneos, ela é separada automaticamente em **sublotes compatíveis**, cada um
gerando seu próprio arquivo. Os totais de header/trailer são validados antes de disponibilizar o
arquivo, o conteúdo é guardado de forma imutável para auditoria e é possível reprocessar apenas o
sublote com erro. O fluxo assíncrono desse agrupamento está detalhado em
[12 — Processamento em Lote](12-processamento-lote.md).

## Mapeamento de ocorrências

O parsing traduz códigos numéricos de ocorrência/motivo para rótulos legíveis (ex.: `06` →
"Liquidação normal", `09` → "Baixa"). O mapa é declarado por banco/layout, pois os códigos variam.

## Estratégia de testes

- **Fixtures de referência:** arquivos de remessa/retorno de referência viram fixtures de teste.
- **Comparação byte-a-byte** na remessa para os bancos prioritários.
- **Round-trip** onde aplicável: gerar remessa, reprocessar posições e conferir campos.
- **Casos de retorno reais** (anonimizados) para validar o mapeamento de ocorrências.

Ver [08 — Testes e Qualidade](08-testes-e-qualidade.md).
