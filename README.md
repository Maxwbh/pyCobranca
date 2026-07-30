<div align="center">

<img src="docs/images/pycobranca-banner.svg" alt="PyCobrança — boletos, CNAB e PIX em Python puro" width="820">

# A plataforma Open Source mais completa para cobrança bancária em Python

**Boletos, CNAB 240/400 e PIX para 18 bancos — com uma única biblioteca, em Python puro.**

[![Versão](https://img.shields.io/badge/versão-1.0.1-2ea44f)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.14+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licença](https://img.shields.io/badge/licença-BSD--3--Clause-blue)](LICENSE)
[![Python puro](https://img.shields.io/badge/Python_puro-sem_libs_de_sistema-2ea44f)](pyproject.toml)
[![PIX](https://img.shields.io/badge/PIX-Bolepix-32BCAD)](docs/07-pix.md)
[![Estrelas](https://img.shields.io/github/stars/Maxwbh/pycobranca?style=flat&logo=github&color=2ea44f)](https://github.com/Maxwbh/pycobranca/stargazers)

⭐ **18 bancos**  ·  📄 **CNAB 240/400**  ·  💳 **PIX / Bolepix**  ·  ⚡ **Python puro**  ·  📦 **Um único `pip install`**  ·  🔓 **BSD-3**

</div>

**PyCobrança** é a plataforma Open Source de **cobrança bancária brasileira** em Python. Uma única
biblioteca cobre todo o ciclo: emite boletos (código de barras, linha digitável e PDF), gera e lê
arquivos **CNAB** (remessa e retorno 240/400) e produz **PIX/Bolepix** (QR Code e segmento PIX no
CNAB) — para **18 bancos**, com uma API limpa e **sem dependências de sistema** (tudo em Python
puro, instalado com um `pip install`).

Projetada para ser o **motor de cobrança** de sistemas Python — do script pontual à emissão em
lote de milhares de boletos — com identidade e arquitetura próprias.

<div align="center">

<img src="docs/images/demo.gif" alt="Do pip install ao boleto, PIX e remessa CNAB em segundos" width="720">

</div>

---

## 🏗️ Arquitetura

A PyCobrança é a **camada única** que emite os artefatos de cobrança. A sua aplicação (ERP, API,
back-end) chama a biblioteca; ela cuida de boletos, CNAB, PIX e PDF.

<div align="center">

<img src="docs/images/pycobranca-arquitetura.svg" alt="Arquitetura: ERPs e frameworks consomem a PyCobrança, que emite boletos, CNAB, PIX e PDF" width="820">

</div>

---

## 💡 Por que a PyCobrança?

A cobrança bancária brasileira mudou. O **PIX** e o **Bolepix** entraram no dia a dia, o **Python
moderno** consolidou-se como base de back-ends e integrações, e as **APIs REST** tornaram-se o
padrão para conectar sistemas de emissão a ERPs e plataformas de pagamento.

A PyCobrança nasceu para atender esse cenário com uma **plataforma única e coesa** — pensada desde
o início para PIX, CNAB 240/400, PDF em Python puro e consumo via API. Em vez de juntar
peças soltas, oferece uma API consistente, testada banco a banco e pronta para produção.

## ✨ Destaques

- 🏦 **18 bancos** com emissão de boleto ponta a ponta (código de barras de 44 posições, linha
  digitável com DVs e regras de carteira/nosso número por banco).
- 📄 **PDF em Python puro** via ReportLab — dois modelos visuais (*clássico* e *moderno*), **carnê**
  (3 parcelas por A4) e **tema** (marca da empresa, cor, marca d'água, rodapé).
- 🖼️ **Logo no cabeçalho** (opt-in): use o seu próprio arquivo (`banco.logo`) ou os **logos de 17
  bancos já empacotados** (`logo_do_banco`), em alta resolução com transparência.
- 🧾 **Remessa CNAB** 400 (12 bancos) e 240 (7 bancos), com agrupamento por convênio/carteira e
  **juros, multa e desconto** (1º/2º/3º, IOF e abatimento).
- 📥 **Retorno CNAB** 400/240 com parsing por banco e tradução dos códigos de ocorrência.
- 🧮 **Extrato OFX** (v1/v2) com extração de nosso número e **conciliação** contra os boletos
  emitidos — fecha o ciclo emissão → retorno → extrato.
- 🟢 **PIX / Bolepix**: BR Code (EMV) copia-e-cola com CRC16, QR Code embutido no PDF e **segmento
  PIX na remessa** (registro tipo 8 no CNAB 400; segmento Y-03 no CNAB 240).
- 🔌 **Pronto para API REST** (OpenAPI 3.0): serializadores JSON dos artefatos para consumo HTTP.
- ⚡ **Instalação única**: boleto, CNAB, PIX, PDF e QR num só `pip install` — tudo Python puro,
  sem bibliotecas de sistema (nada de cairo, Pango ou wkhtmltopdf).

## 🖼️ Exemplos reais

PDFs gerados pela própria PyCobrança (dados fictícios, saída real do backend ReportLab):

<div align="center">

| Boleto (modelo moderno) | Boleto com PIX (Bolepix) |
|:---:|:---:|
| <img src="docs/images/screenshots/boleto-moderno.png" alt="Boleto no modelo moderno gerado pela PyCobrança" width="330"> | <img src="docs/images/screenshots/boleto-pix.png" alt="Boleto híbrido com QR Code PIX" width="330"> |
| Recibo do Pagador + ficha, código de barras nativo | QR Code Bolepix embutido, célula PIX teal |
| **Boleto com logo do banco** | **Carnê (3 por A4)** |
| <img src="docs/images/screenshots/boleto-logo.png" alt="Boleto com o logo do banco no cabeçalho (recibo e ficha)" width="330"> | <img src="docs/images/screenshots/carne.png" alt="Carnê com 3 parcelas por página A4" width="330"> |
| Logo no cabeçalho do recibo e da ficha (`logo_do_banco`) | Canhoto à esquerda, uma A4 a cada 3 parcelas |

</div>

## 📦 Instalação

```bash
pip install pycobranca   # tudo: boleto, CNAB, PIX, PDF e QR Code (Bolepix)
```

Uma única instalação entrega o que um sistema de cobrança precisa — código de barras, linha
digitável, remessa/retorno **CNAB**, **PIX** (copia-e-cola e QR) e **PDF**. Sem extras a decorar e
**sem bibliotecas de sistema**: ReportLab e qrcode são Python puro, resolvidos pelo próprio `pip`.

Requer **Python 3.14+**.

## 🚀 Início rápido

### Emitir um boleto (PDF)

```python
from datetime import date
from pycobranca.bancos import Bancos
from pycobranca.render import render_boleto_pdf

Banco = Bancos.find("341")  # Itaú (descoberta pelo código FEBRABAN)
boleto = Banco(
    valor="127.50",
    cedente="Empresa Exemplo LTDA",
    cedente_documento="11.222.333/0001-81",
    agencia="0057",
    conta="12345",
    carteira="109",
    nosso_numero="12345678",
    data_vencimento=date(2026, 8, 15),
    sacado="Cliente Final da Silva",
    sacado_documento="529.982.247-25",
)

boleto.validar()
print(boleto.linha_digitavel)  # 34191.09123 ... com DVs
print(boleto.codigo_barras)  # 44 posições (DV geral módulo 11)

pdf = render_boleto_pdf(boleto.contexto_render(), modelo="moderno")
open("boleto.pdf", "wb").write(pdf)
```

Para exibir um logo no cabeçalho, use o seu arquivo ou um logo empacotado:

```python
from pycobranca.render import logo_do_banco

boleto = Banco(..., logo=logo_do_banco("341"))  # ou logo=b"...bytes PNG/JPEG..." / "caminho.png"
```

### Gerar uma remessa CNAB

```python
from datetime import date
from pycobranca.cnab import Pagamento, RemessaItau400

remessa = RemessaItau400(
    empresa_mae="Empresa Exemplo LTDA",
    documento_cedente="11222333000181",
    agencia="0057",
    conta_corrente="12345",
    digito_conta="7",
    carteira="109",
    pagamentos=[
        Pagamento(
            nosso_numero="12345678",
            valor=199.90,
            data_vencimento=date(2026, 8, 15),
            documento_sacado="52998224725",
            nome_sacado="Cliente Final da Silva",
            endereco_sacado="Rua das Flores, 100",
            bairro_sacado="Centro",
            cep_sacado="30110000",
            cidade_sacado="Belo Horizonte",
            uf_sacado="MG",
        ),
    ],
)
open("CB.REM", "w", newline="").write(remessa.gera_arquivo())
```

### Juros, multa e desconto na remessa

Cada encargo é opcional e informado direto no `Pagamento`. Com os defaults, o boleto sai sem
encargos (o caixa preenche na hora do recebimento); ao informá-los, eles entram na remessa nas
posições do padrão FEBRABAN.

```python
from datetime import date
from pycobranca.cnab import Pagamento

Pagamento(
    nosso_numero="12345678",
    valor=199.90,
    data_vencimento=date(2026, 8, 15),
    # ... dados do sacado ...
    # Juros de mora: por dia (tipo_mora="1") ou taxa mensal % (tipo_mora="2")
    tipo_mora="1",
    valor_mora=1.53,  # R$ 1,53 ao dia
    # tipo_mora="2", percentual_mora=1.00,        # 1% ao mês
    # Multa por atraso (percentual)
    codigo_multa="2",
    percentual_multa=2.00,  # 2%
    data_multa=date(2026, 8, 16),  # opcional; padrão = vencimento
    # Descontos (até 3) — código, valor e data por faixa
    cod_desconto="1",
    valor_desconto=10.00,
    data_desconto=date(2026, 8, 1),
    cod_segundo_desconto="1",
    valor_segundo_desconto=5.00,
    data_segundo_desconto=date(2026, 8, 10),
    valor_abatimento=0.0,
    valor_iof=0.0,
)
```

| Encargo | Código/tipo | Valor | Data |
|---|---|---|---|
| **Multa** | `codigo_multa` (`0` isento · `1` valor · `2` %) | `percentual_multa` (%) | `data_multa` |
| **Juros/Mora** | `tipo_mora` (`1` valor/dia · `2` taxa mensal % · `3` isento) | `valor_mora` · `percentual_mora` | `data_mora` |
| **Desconto 1º/2º/3º** | `cod_desconto` / `cod_segundo_desconto` / `cod_terceiro_desconto` | `valor_desconto` / `valor_segundo_desconto` / `valor_terceiro_desconto` | `data_desconto` / `data_segundo_desconto` / `data_terceiro_desconto` |
| **IOF** · **Abatimento** | — | `valor_iof` · `valor_abatimento` | — |

**Suporte por banco.** O `Pagamento` sempre aceita os campos; eles entram no arquivo onde o layout
tem posição.

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

<sub>✅ campo posicional na remessa · — sem campo no layout · **Desc. 3º**: apenas CNAB 240.
📝¹ Itaú/BB (400): multa vai por **instrução** (código), não como percentual posicional.
📅² Santander (400): 2º desconto só a **data**. ³ CrediSIS: 1º desconto **sem** campo de data.
⁴ Ailos (240): segmento R (multa + 2º/3º desconto) emitido só quando há multa.
Banestes (021), HSBC (399) e Safra (422) só emitem boleto (sem remessa CNAB).</sub>

> Detalhes por layout (posições 240/400, valor × percentual por banco) em
> [`docs/06-cnab.md`](docs/06-cnab.md); via API REST, o objeto `encargos` em
> [`docs/04-api-rest.md`](docs/04-api-rest.md).

### Ler um retorno CNAB

```python
from pycobranca.cnab.retorno import Retorno

retorno = Retorno.ler("CB.RET")  # layout (240/400) e banco detectados pelo arquivo
for r in retorno.registros:
    print(r.nosso_numero, r.codigo_ocorrencia, retorno.descricao_ocorrencia(r), r.valor_recebido)
```

### Ler um extrato OFX e conciliar

Lê o extrato bancário (OFX v1/v2), extrai o **nosso número** do memo de cada transação e **concilia**
contra os boletos emitidos — fechando o ciclo emissão → retorno → extrato.

```python
from pycobranca.ofx import Extrato, concilia

extrato = Extrato.ler("extrato.ofx")  # OFX v1 (SGML) ou v2 (XML), encoding Latin-1/UTF-8
print(extrato.org, extrato.saldo_valor)
for t in extrato.creditos:
    print(t.data, t.valor, t.nosso_numero_extraido, t.memo)

# Conciliação contra os nossos números emitidos
resultado = concilia(extrato, ["12345678", "87654321"])
print(len(resultado.conciliadas), "casadas ·", resultado.pendentes, "pendentes")
```

<div align="center">

<img src="docs/images/pycobranca-ciclo.svg" alt="Ciclo de cobrança: emissão → remessa CNAB → retorno CNAB → extrato OFX, conciliados pelo nosso número" width="820">

</div>

### Boleto híbrido com PIX (Bolepix)

```python
Banco = Bancos.find("237")  # Bradesco
boleto = Banco(
    valor="127.50",
    cedente="Empresa Exemplo LTDA",
    cedente_documento="11222333000181",
    agencia="1234",
    conta="56789",
    carteira="09",
    nosso_numero="12345678",
    data_vencimento=date(2026, 8, 15),
    sacado="Cliente Final",
    sacado_documento="52998224725",
    cedente_cidade="SAO PAULO",
    pix_chave="11222333000181",
    pix_txid="TX2026080100001",
)
pdf = render_boleto_pdf(boleto.contexto_render(), modelo="moderno")  # QR embutido
```

## 🏦 Bancos suportados

Funcionalidade por banco (✅ = disponível/validado):

| Cód. | Banco | Boleto | Rem. 400 | Rem. 240 | Retorno | PIX | Logo |
|:----:|-------|:------:|:--------:|:--------:|:-------:|:---:|:----:|
| 001 | Banco do Brasil | ✅ | ✅ | ✅ |  | ✅ | ✅ |
| 004 | Banco do Nordeste | ✅ | ✅ |  | ✅ |  | ✅ |
| 021 | Banestes | ✅ |  |  |  |  | ✅ |
| 033 | Santander | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 041 | Banrisul | ✅ | ✅ |  | ✅ |  | ✅ |
| 070 | BRB | ✅ | ✅¹ |  | ✅ |  | ✅ |
| 085 | Ailos | ✅ |  | ✅ | ✅ |  | ✅ |
| 097 | CrediSIS | ✅ | ✅ |  | ✅ |  | ✅ |
| 104 | Caixa | ✅ |  | ✅ | ✅ | ✅ | ✅ |
| 136 | Unicred | ✅ | ✅ | ✅ | ✅ |  | ✅ |
| 237 | Bradesco | ✅ | ✅ |  | ✅ | ✅ | ✅ |
| 336 | C6 Bank | ✅ | ✅ |  |  | ✅ | ✅ |
| 341 | Itaú | ✅ | ✅ |  | ✅ | ✅ | ✅ |
| 399 | HSBC | ✅ |  |  | ✅ |  | ✅ |
| 422 | Safra | ✅ |  |  |  |  | ✅ |
| 745 | Citibank | ✅ | ✅ |  |  |  |  |
| 748 | Sicredi | ✅ |  | ✅ | ✅ |  | ✅ |
| 756 | Sicoob | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Σ 18** | | **18** | **12** | **7** | **13** | **7** | **17** |

- **Boleto** — código de barras (44 pos.), linha digitável e PDF.
- **Rem. 400 / Rem. 240** — remessa CNAB validada **byte a byte** contra vetores de referência.
- **Retorno** — parser validado contra arquivo `.RET` **real**; o leitor auto-detecta 240/400 pelo
  cabeçalho e também processa layouts compatíveis dos demais bancos.
- **PIX** — Bolepix (BR Code + QR no PDF + segmento PIX na remessa).
- **Logo** — logo empacotado via `logo_do_banco("NNN")`, em alta resolução com transparência
  (17 dos 18 bancos; marca do banco, uso nominativo — origem e licença por arquivo em
  [`render/logos/NOTICE.md`](pycobranca/render/logos/NOTICE.md)).
- ¹ BRB usa formato de remessa **DCB proprietário**.

Detalhes de carteiras, quirks e fixtures por banco na
[matriz de bancos](docs/05-bancos-suportados.md) e nos [documentos por banco](docs/bancos/README.md).

## 🧩 O que a PyCobrança faz

| Recurso | Descrição |
|---------|-----------|
| **Boleto** | Código de barras (44 pos.), linha digitável (DVs), fator de vencimento e regras por banco. |
| **PDF** | ReportLab (Python puro): modelos *clássico* e *moderno*, carnê e tema. |
| **Remessa CNAB** | 400 (12 bancos) e 240 (7 bancos), com `Pagamento`/`PagamentoPix`. |
| **Retorno CNAB** | Parsing 400/240 por banco + tradução de ocorrências. |
| **PIX/Bolepix** | BR Code (EMV) + CRC16, QR no PDF e segmento PIX na remessa. |
| **API REST** | Serialização JSON dos artefatos (OpenAPI 3.0), pronta para consumo HTTP. |

## ⚖️ Comparação

| Recurso | PyCobrança | PyBoleto | BrCobrança |
|---|:---:|:---:|:---:|
| Boleto (código de barras + linha digitável) | ✅ | ✅ | ✅ |
| CNAB 240/400 (remessa e retorno) | ✅ | ❌ | ✅ |
| PIX / Bolepix | ✅ | ❌ | ✅ |
| PDF do boleto | ✅ | ✅ | ✅ |
| Linguagem | Python 3.14+ | Python (legado) | Ruby |
| Instalação única (um `pip install`) | ✅ | ✅ | — |
| Contrato para API REST | ✅ | ❌ | ❌ |
| Situação | 🟢 Desenvolvimento ativo | Manutenção | Manutenção |

## 👥 Para quem é

Feita para quem precisa **emitir e conciliar cobrança bancária** dentro de um sistema Python:

**ERPs** · **sistemas financeiros** · **SaaS de cobrança** · **software de contabilidade** ·
**fintechs** · **marketplaces** · **e-commerce** · **prefeituras e órgãos públicos** ·
**universidades**.

Do script pontual à emissão em lote de milhares de boletos — a API é a mesma, sem serviço externo
nem dependências de sistema.

## 🔭 Visão

A PyCobrança é construída para ser a **base de longo prazo** do ecossistema de cobrança bancária
brasileira em Python. O rumo do projeto:

- **Emissão de boletos** para os principais bancos, com regras por carteira e nosso número.
- **CNAB 240 e 400** — remessa e retorno, cobrindo os layouts do mercado.
- **PIX e Bolepix** — BR Code (EMV), QR Code e o segmento PIX no CNAB.
- **APIs REST** — artefatos serializáveis em JSON, prontos para expor via HTTP.
- **OpenAPI** — contrato validável dos artefatos (OpenAPI 3.0).
- **Renderização em PDF** — em Python puro, sem dependências de sistema.
- **Integração com ERPs e frameworks Python** — API limpa, pronta para embutir.
- **Evolução contínua** conforme os padrões da **FEBRABAN** e a regulação de meios de pagamento.

## 🗺️ Roadmap

Entregue e em evolução:

- ✅ Emissão de boletos (18 bancos)
- ✅ CNAB 240 e 400 (remessa e retorno)
- ✅ PIX / Bolepix (BR Code, QR e segmento PIX na remessa)
- ✅ Renderização em PDF (boleto, carnê e tema)
- ✅ Serialização REST dos artefatos (OpenAPI 3.0)
- ✅ Validação FEBRABAN independente do boleto
- ✅ Leitura de extrato OFX e conciliação com os boletos emitidos
- ✅ Encargos completos na remessa (juros, multa, desconto 1º/2º/3º, IOF, abatimento)
- ✅ Fatura (demonstrativo de itens + boleto) com corpo livre
- 🚧 Novos bancos (mediante manual oficial com exemplo validável)
- 🚧 Novos modelos de documento (o catálogo em `render/modelos/` aceita extensões)

## 📚 Documentação

| Documento | Conteúdo |
|-----------|----------|
| [Visão Geral](docs/00-visao-geral.md) · [Arquitetura](docs/01-arquitetura.md) | Objetivo, escopo e camadas |
| [Arquitetura e diretórios](docs/16-arquitetura-diretorios.md) | Árvore do pacote, subsistemas e fluxos |
| [Bancos Suportados](docs/05-bancos-suportados.md) · [por banco](docs/bancos/README.md) | Matriz, carteiras e especificação |
| [Adicionar um novo banco](docs/15-novo-banco.md) | Campo livre, DVs, remessa, testes e documentação |
| [CNAB](docs/06-cnab.md) | Remessa e retorno 240/400 |
| [Validação de campos](docs/14-validacao-campos.md) | Tamanhos, conjuntos e contrato de erros |
| [OFX](docs/13-ofx.md) | Extrato bancário e conciliação |
| [PIX / Bolepix](docs/07-pix.md) | QR Code e segmento PIX no CNAB |
| [API REST](docs/04-api-rest.md) | Contrato de dados e consumo via HTTP |
| [Renderização](docs/11-renderizacao.md) | Backend de PDF (ReportLab) |

## 🤝 Contribuindo

Este é um projeto **novo** e contribuições são muito bem-vindas — desde relatar um comportamento
de banco divergente até adicionar um layout de CNAB. Comece pelo
[guia de contribuição](CONTRIBUTING.md). Em resumo:

```bash
git clone https://github.com/Maxwbh/pycobranca.git
cd pycobranca
pip install -e ".[dev]"
ruff check . && ruff format --check .   # lint + formatação
pytest                                   # suíte de testes
```

Boas primeiras contribuições: novos bancos (com exemplo oficial validável), casos de teste de
retorno reais (anonimizados) e melhorias de documentação. Abra uma _issue_ antes de mudanças
grandes para alinharmos o desenho.

## 📄 Licença

Distribuída sob a licença **[BSD-3-Clause](LICENSE)** — permissiva: permite uso comercial,
modificação e redistribuição, exigindo apenas a manutenção do aviso de copyright.
© 2026 **[M&S DO BRASIL LTDA](https://msbrasil.inf.br)**.

## 🙏 Créditos

Desenvolvida e mantida pela **[M&S DO BRASIL LTDA](https://msbrasil.inf.br)**. Projeto independente,
inspirado em soluções Open Source anteriores de cobrança bancária em Python e Ruby.

Feito com ☕ para o ecossistema de pagamentos brasileiro.

---

<sub>
<b>Palavras-chave:</b> boleto Python · CNAB Python · FEBRABAN · remessa CNAB · retorno CNAB ·
PIX QR Code · boleto PIX · Bolepix · boleto bancário Python · integração bancária ·
cobrança bancária · CNAB 240 · CNAB 400 · linha digitável · código de barras · boleto PDF.
</sub>
