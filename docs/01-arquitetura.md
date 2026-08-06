# 01 — Arquitetura

## Visão em camadas

A PyCobrança é organizada em camadas com dependências apontando sempre para dentro (domínio no
centro, infraestrutura na borda).

```
┌──────────────────────────────────────────────────────────────┐
│  Serialização / Renderização                                   │
│  to_dict / to_json  ·  render.pdf (reportlab)  ·  render.pix   │
├──────────────────────────────────────────────────────────────┤
│  CNAB                                                           │
│  cnab.remessa (240/400)       ·  cnab.retorno (parse → dict)    │
├──────────────────────────────────────────────────────────────┤
│  Domínio                                                        │
│  Boleto  ·  Banco (registro)  ·  validações  ·  linha/barra    │
├──────────────────────────────────────────────────────────────┤
│  Núcleo utilitário                                             │
│  módulo 10/11, dígitos verificadores, fator de vencimento,     │
│  formatação de valores/documentos (CPF/CNPJ)                   │
└──────────────────────────────────────────────────────────────┘
```

## Módulos do pacote

```
pycobranca/
├── __init__.py            # versão pública, exports de conveniência
├── core/
│   ├── dv.py              # dígitos verificadores (módulo 10, módulo 11)
│   ├── datas.py           # fator de vencimento, datas base FEBRABAN
│   ├── documentos.py      # validação/formatação CPF, CNPJ
│   └── numeros.py         # formatação monetária, zero-fill
├── boleto/
│   ├── base.py            # classe Boleto (dataclass + validações comuns)
│   ├── linha_digitavel.py # composição da linha digitável
│   └── codigo_barras.py   # composição do código de barras (44 posições)
├── bancos/
│   ├── __init__.py        # registro: Bancos.todos/find/com_pix
│   ├── base.py            # BancoBase (contrato por banco)
│   ├── banco_do_brasil.py
│   ├── bradesco.py
│   ├── itau.py
│   ├── santander.py
│   ├── caixa.py
│   ├── sicoob.py
│   └── ...                # um módulo por banco
├── cnab/
│   ├── remessa/           # geração 240/400 por banco
│   ├── retorno/           # parsing 240/400 → dict
│   └── layouts/           # definições posicionais de registros
├── pix/
│   ├── payload.py         # BR Code / EMV (copia-e-cola)
│   └── qrcode.py          # geração de QR Code
├── render/
│   ├── barcode.py        # Interleaved 2 of 5 (Python puro)
│   └── reportlab.py      # backend ÚNICO de renderização (modelos classico/moderno, carnê, tema)
├── serialization.py       # mixin to_dict/to_json
└── exceptions.py          # hierarquia de erros de domínio
```

### Convenção de nomenclatura (pt-BR canônica)

Os nomes de domínio são em **português** (`bancos`, `sacado`, `cedente`, `nosso_numero`),
alinhados ao domínio bancário brasileiro. A tabela abaixo fixa a nomenclatura canônica dos módulos:

| Módulo canônico (pt-BR) | Responsabilidade |
|-------------------------|------------------|
| `bancos/` | Regras por banco e registro. |
| `render/` | Renderização (ReportLab). |

> **Decisões de escopo:** o SDK HTTP é **projeto separado**; a **renderização é exclusivamente via
> ReportLab**.

## Domínio: o objeto `Boleto`

O `Boleto` é modelado como uma `dataclass` com validação explícita. Campos essenciais:

| Campo | Descrição |
|-------|-----------|
| `valor` | Valor do documento (Decimal). |
| `cedente` / `cedente_documento` | Beneficiário e CPF/CNPJ. |
| `agencia` / `conta` | Dados da conta. |
| `carteira` | Carteira/modalidade de cobrança. |
| `nosso_numero` | Identificador do título no banco. |
| `data_vencimento` / `data_documento` | Datas. |
| `sacado` / `sacado_documento` | Pagador e CPF/CNPJ. |

Propriedades derivadas (calculadas por banco): `linha_digitavel`, `codigo_barras`,
`nosso_numero_formatado`, `agencia_conta_formatado`, `campo_livre`.

## Registro de bancos

Cada banco herda de `BancoBase` e é auto-registrado por código
FEBRABAN. O registro permite descoberta sem hardcode:

```python
from pycobranca.bancos import Bancos

Bancos.todos()  # -> lista de classes de banco registradas
Bancos.find("341")  # -> classe do Itaú
Bancos.com_pix()  # -> bancos com suporte a Bolepix
```

Cada `BancoBase` declara: `codigo`, `nome`, `digito_banco`, carteiras suportadas, e implementa
`campo_livre()`, `nosso_numero_formatado()` e as regras de validação específicas.

## CNAB

O subsistema CNAB separa **layout** (definição posicional de registros) de **serialização**
(preencher/ler posições). Layouts são declarativos e versionados por banco e por formato
(240/400), permitindo testar posições isoladamente.

- **Remessa:** `boleto → registros → string de arquivo`.
- **Retorno:** `string de arquivo → registros → list[dict]` (JSON-friendly para conciliação).

Detalhes em [06 — CNAB](06-cnab.md).

## PIX / Bolepix

Geração do payload BR Code (EMV) e do QR Code, além do segmento PIX no CNAB para bancos
habilitados. Detalhes em [07 — PIX](07-pix.md).

## Renderização

Renderização **exclusivamente via ReportLab** (Python puro, zero dependências de sistema), com
os modelos `classico` e `moderno` (Bolepix, carnê e TEMA) e vencedora do benchmark de lote
(~120× mais rápida que HTML/CSS). Histórico da decisão e números em
[11 — Renderização](11-renderizacao.md).

## Serialização

Um mixin `SerializableMixin` fornece `to_dict()` e `to_json()` para `Boleto`, registros CNAB e
resultados de retorno, garantindo respostas amigáveis a APIs REST.

## Consumo via API REST

A biblioteca **produz** os artefatos (boleto, remessa, retorno) no contrato de dados descrito em
[04 — API REST](04-api-rest.md). O SDK HTTP que consome o serviço é
**projeto separado** (decisão de escopo).

## Decisões arquiteturais (ADR resumidas)

| # | Decisão | Motivo |
|---|---------|--------|
| ADR-1 | `pyproject.toml` + build PEP 517 | Empacotamento moderno; abandona `setup.py test`. |
| ADR-2 | `reportlab` como **único** backend de renderização (`modelo="moderno"` padrão) | Benchmark de lote (100–200 boletos: ~120× mais rápido, PDFs 3× menores, zero deps de sistema). Decisão e números em [11 — Renderização](11-renderizacao.md). |
| ADR-3 | Registro de bancos por auto-registro | Descoberta programática dos bancos. |
| ADR-4 | Layouts CNAB declarativos | Testabilidade posicional e reuso entre bancos. |
| ADR-5 | `Decimal` para valores monetários | Evita erros de ponto flutuante em centavos. |
| ADR-6 | **Sem retrocompatibilidade** | Decisão de projeto: API única e direta, sem camada de compatibilidade. |
