# 15 — Como adicionar um novo banco

Guia prático para implementar um banco novo na PyCobrança. Tudo aqui reflete o código real do
pacote — os nomes de classes, métodos e arquivos citados existem e podem ser abertos.

> **Pré-requisito de projeto:** um banco só entra com **manual oficial** (ou circular/layout
> publicado pela instituição) e pelo menos **um exemplo validável** — entrada conhecida e a saída
> esperada de código de barras/linha digitável. Sem vetor de referência não há como fechar o
> ciclo de testes descrito na seção 5.

## 1. O que compõe "um banco"

| Camada | Obrigatório? | Onde vive |
|--------|:------------:|-----------|
| **Boleto** — campo livre, DVs, formatos de exibição | ✅ | `pycobranca/bancos/<slug>.py` |
| **Export/registro** | ✅ | `pycobranca/bancos/__init__.py` |
| **Testes** — exemplo + paridade + validador FEBRABAN | ✅ | `tests/exemplos_boletos.py` |
| **Documentação** do banco | ✅ | `docs/bancos/<codigo>-<slug>.md` + `docs/bancos/README.md` |
| **Remessa CNAB 400** | opcional | `pycobranca/cnab/cnab400/<slug>.py` |
| **Remessa CNAB 240** | opcional | `pycobranca/cnab/cnab240/<slug>.py` |
| **Retorno CNAB** | opcional | mapas em `pycobranca/cnab/retorno/cnab400.py` / `cnab240.py` |
| **Logo empacotado** | opcional | `pycobranca/render/logos/<codigo>.png` |

O mínimo viável é **boleto + export + testes + doc**. Remessa e retorno são independentes: há
bancos que só emitem boleto (Banestes, HSBC, Safra) e bancos com remessa em um layout só.

## 2. Passo a passo — o boleto

### 2.1 Criar o módulo do banco

Crie `pycobranca/bancos/<slug>.py` com uma subclasse de
[`BancoBase`](../pycobranca/bancos/base.py). O docstring do módulo é o lugar canônico da tabela do
campo livre (veja `itau.py` e `caixa.py` como referência).

### 2.2 Declarar os ClassVars

| ClassVar | Tipo | Papel |
|----------|------|-------|
| `codigo` | `str` | Código FEBRABAN de 3 dígitos. **Dispara o auto-registro** — sem ele o banco não entra no `REGISTRO`. |
| `nome` | `str` | Nome exibido (usado em `contexto_render()` e em `banco_info()`). |
| `digito_banco` | `str` | DV do código do banco, só para exibição (`341-7`). Pode ser alfabético (`Sicredi` usa `X`). |
| `carteiras` | `tuple[str, ...]` | Conjunto fechado de carteiras aceitas. Vazio = sem checagem. |
| `suporta_pix` | `bool` | Habilita o Bolepix. Com `pix_chave` preenchida e `suporta_pix=False`, `contexto_render()` levanta `BoletoInvalido`. |
| `regras_campos` | `dict[str, tuple[int, int]]` | `campo -> (mínimo, máximo)` em **dígitos**, aplicado por `validar()`. |

O auto-registro acontece em `BancoBase.__init_subclass__`: toda subclasse com `codigo` não vazio é
inserida em `REGISTRO[codigo.zfill(3)]`. O registro só enxerga o banco depois que o módulo é
importado — por isso o passo 2.6 é obrigatório.

### 2.3 Escolher os campos de entrada

O `BancoBase` é uma `dataclass` e já traz todos os campos do título (`valor`, `cedente`, `agencia`,
`conta`, `carteira`, `convenio`, `nosso_numero`, `data_vencimento`, `sacado`, …). Para
particularidades, **reutilize os campos auxiliares já declarados** em vez de criar novos:

| Campo auxiliar | Usado hoje por |
|----------------|----------------|
| `variacao` | Sicoob, Banestes |
| `posto`, `byte_idt` | Sicredi |
| `digito_convenio` | Banrisul |
| `digito_conta` | Banco do Nordeste, Banestes, Safra, Unicred |
| `digito_agencia` | Safra |
| `portfolio` | Citibank |
| `incremento` | BRB |
| `numero_contrato` | Sicoob (carteira 9) |

### 2.4 Implementar `campo_livre()` — 25 dígitos

`campo_livre()` devolve **exatamente 25 caracteres, todos dígitos**. A montagem do código de barras
(`montar_codigo_barras`, em [`boleto/codigo_barras.py`](../pycobranca/boleto/codigo_barras.py))
rejeita qualquer outra coisa:

```python
if len(campo_livre) != 25 or not campo_livre.isdigit():
    raise ValueError(f"campo livre deve ter 25 dígitos: {campo_livre!r}")
```

Regras práticas:

- normalize **todo** campo de entrada com `so_digitos(...)` e `zfill(n)` — a máscara do usuário
  (`"12.345-6"`) nunca deve vazar para o campo livre;
- exponha cada bloco como `@property` privada (`_agencia4`, `_conta5`, …), como faz o Itaú: isso
  deixa o `campo_livre()` legível e permite testar os DVs isoladamente;
- constantes do layout (`"000"`, `"10"`, `"021"`) entram literais, com comentário no docstring.

### 2.5 Calcular os DVs com os helpers de `core/dv.py`

Não reimplemente módulo 10/11. [`pycobranca/core/dv.py`](../pycobranca/core/dv.py) expõe:

| Helper | Assinatura | Quando usar |
|--------|-----------|-------------|
| `modulo10(sequencia)` | `-> int` | DAC/DV módulo 10 (pesos 2,1,2,1… da direita). Itaú, DVs de campo. |
| `modulo11_resto(sequencia, *, peso_max=9)` | `-> int` | Devolve **só o resto**; o banco aplica a própria regra de mapeamento (Caixa, Santander). |
| `modulo11_codigo_barras(sequencia)` | `-> int` | DV geral do código de barras. **Já é aplicado pela base** — não chame no banco. |
| `modulo11_flex(seq, *, fatores, da_direita, bloco, mapa)` | `-> int \| str` | Módulo 11 configurável: fatores próprios, sentido de leitura e tradução do resultado (ex.: `mapa={10: 0, 11: 0}`, ou `{10: "P"}`). |
| `duplo_digito(sequencia)` | `-> str` | Dígito duplo (módulo 10 + módulo 11 fatores 2..7, com recálculo quando o 2º dígito dá 1). Banrisul, Banestes, BRB. |

Dois exemplos reais:

```python
# Caixa — módulo 11 pesos 2..9, DV = 11 - resto, DV > 9 vira "0"
def _dv11_caixa(sequencia: str) -> str:
    dv = 11 - modulo11_resto(sequencia, peso_max=9)
    return "0" if dv > 9 else str(dv)


# Sicredi — módulo 11 com fatores padrão 9..2 e resto 10/11 colapsado em 0
_MAPA = {10: 0, 11: 0}
dv = modulo11_flex(base, mapa=_MAPA)
```

### 2.6 Formatos de exibição

Sobrescreva quando o banco imprime algo diferente do valor cru:

- `nosso_numero_formatado()` — default: `self.nosso_numero`. Itaú: `109/12345678-0`.
- `agencia_conta_formatado()` — default: `f"{self.agencia} / {self.conta}"`. Caixa:
  `0001 / 123456-7`.

Os dois alimentam `contexto_render()` e, por consequência, o PDF.

### 2.7 Registrar o export

Em [`pycobranca/bancos/__init__.py`](../pycobranca/bancos/__init__.py), acrescente o import (em
ordem alfabética de módulo, como os demais) e o nome em `__all__`:

```python
from .banco_exemplo import BancoExemplo

__all__ = [
    "Bancos",
    "BancoBase",
    # ...
    "BancoExemplo",
]
```

Sem esse import o módulo nunca é carregado, `__init_subclass__` não roda e `Bancos.find("999")`
levanta `BancoNaoRegistrado`.

## 3. Checklist de validação

O que `BancoBase.validar()` **já cobre**, sem uma linha a mais no banco:

- `valor` positivo (em centavos) e `data_vencimento` presente;
- `cedente` preenchido;
- `carteira` pertencente a `carteiras` (mensagem lista as válidas);
- tamanhos mín./máx. de cada entrada de `regras_campos`, medidos em **dígitos** após
  `so_digitos()` — o mínimo pega campo vazio/curto, o máximo trava o formato do campo livre;
- `cedente_documento` e `sacado_documento`, quando informados, como CPF **ou** CNPJ válido.

Todos os problemas são acumulados e levantados de uma vez em `BoletoInvalido.erros` (lista). O
contrato completo está em [`14-validacao-campos.md`](14-validacao-campos.md).

**Rótulos das mensagens.** `base.py` tem um mapa `_ROTULOS_CAMPOS` com os nomes amigáveis
(`agencia` → "agência", `nosso_numero` → "nosso número", …). Se o seu banco validar um campo que
não está lá, a mensagem sai com o nome cru do atributo — inclua o rótulo no mapa.

**Regras próprias.** Quando houver uma regra que não cabe em `regras_campos` (dependência entre
campos, campo obrigatório condicional), estenda `validar()` chamando `super()` antes:

```python
def validar(self) -> None:
    super().validar()
    erros: list[str] = []
    if len(self._convenio) not in (4, 6, 7):
        erros.append("convênio deve ter 4, 6 ou 7 dígitos")
    if erros:
        raise BoletoInvalido(erros)
```

Esse é o padrão do Banco do Brasil (`banco_do_brasil.py`) e do Santander (`santander.py`).
Pré-condições que só existem no momento de montar o campo livre (ex.: `byte_idt` do Sicredi) podem
levantar `BoletoInvalido` de dentro da própria `@property`.

## 4. Passo a passo — remessa CNAB (opcional)

### 4.1 CNAB 400

Crie `pycobranca/cnab/cnab400/<slug>.py` com uma `@dataclass` herdando de
[`RemessaCnab400Base`](../pycobranca/cnab/cnab400/base.py). Ganchos **obrigatórios**:

| Método | Devolve |
|--------|---------|
| `cod_banco()` | Código FEBRABAN (3). |
| `nome_banco()` | Nome do banco no header, já com o `ljust` do layout (15 posições no Itaú). |
| `info_conta()` | Bloco de agência/conta/convênio do header. |
| `complemento()` | Brancos/zeros entre o header e o sequencial. |
| `monta_detalhe(pagamento, sequencial)` | Registro tipo 1 completo. |

Ganchos **opcionais** detectados por `hasattr` em `_monta_registros()`:
`monta_detalhe_multa(pagamento, sequencial)` (emitido quando `codigo_multa > 0`) e
`monta_detalhe_pix(pagamento, sequencial)` (emitido para um `PagamentoPix`).

A base já entrega header (`01REMESSA01COBRANCA…`), trailer (tipo 9), validação dos pagamentos,
CRLF, `upper()` e remoção de acentos. Quando o layout do banco não tem 400 posições no detalhe,
declare `tamanho_registro: int | None = None` para desligar a checagem estrita — a garantia passa a
ser a comparação byte a byte com a fixture (é o caso de Banco do Nordeste, CrediSIS e BRB).

Exporte a classe em `cnab400/__init__.py` **e** em `pycobranca/cnab/__init__.py`.

### 4.2 CNAB 240

Crie `pycobranca/cnab/cnab240/<slug>.py` herdando de
[`RemessaCnab240Base`](../pycobranca/cnab/cnab240/base.py). Ganchos **obrigatórios**:

`cod_banco()` · `nome_banco()` · `info_conta()` · `codigo_convenio()` · `convenio_lote()` ·
`versao_layout_arquivo()` · `versao_layout_lote()` · `complemento_header()` ·
`complemento_trailer()` · `complemento_p(pagamento)`.

Ganchos com default, sobrescritos conforme o manual: `_digito_agencia()`, `densidade_gravacao()`,
`uso_exclusivo_banco()`, `uso_exclusivo_empresa()`, `exclusivo_servico()`,
`dv_agencia_cobradora()`, `complemento_r()`, `numero(pagamento)`,
`identificacao_titulo_empresa(pagamento)`, `data_multa(pagamento)`, `data_mora(pagamento)`,
`valor_mora_segmento(pagamento)`, `descontos_adicionais(pagamento)`, `codigo_desconto(pagamento)`,
`codigo_baixa(pagamento)`, `dias_baixa(pagamento)` e `monta_trailer_arquivo(...)`.

A base monta Header de Arquivo (0) → Header de Lote (1) → segmentos **P/Q/R** (3) → Trailer de Lote
(5) → Trailer de Arquivo (9). Quando o pagamento é um `PagamentoPix` e a classe define
`monta_segmento_y(...)`, o segmento Y-03 entra depois do R. Defaults do dataclass (`especie_titulo`,
`forma_cadastramento`, `tipo_documento`, …) podem ser fixados num `__post_init__`, como faz o
Sicredi.

Exporte em `cnab240/__init__.py` e em `pycobranca/cnab/__init__.py`.

### 4.3 Campos de entrada da remessa

Os dois `Base` já expõem `pagamentos`, `empresa_mae`, `agencia`, `conta_corrente`, `digito_conta`,
`carteira`, `documento_cedente`, `aceite` e `sequencial_remessa` (o 400 tem `data_geracao`; o 240,
`convenio`, `data_geracao_fixa` e `hora_geracao_fixa`). Campos exclusivos do banco vão como
atributos do próprio dataclass filho (ex.: `codigo_transmissao` no Santander, `posto`/`byte_idt` no
Sicredi).

## 5. Testes

### 5.1 Exemplo do boleto (obrigatório)

Acrescente uma entrada em [`tests/exemplos_boletos.py`](../tests/exemplos_boletos.py) com o
construtor e a **saída de referência**:

```python
"banco_exemplo": {
    "boleto": lambda: BancoExemplo(
        **COMUM, agencia="1234", convenio="1234567", carteira="1", nosso_numero="12345678"
    ),
    "codigo_barras": "99991153900000127501234123456700012345678914",
    "linha_digitavel": "99991.23418 23456.700014 23456.789140 1 15390000012750",
    "nosso_numero": "00012345678-9",
},
```

Essa única entrada alimenta três suítes:

| Teste | O que garante |
|-------|---------------|
| [`test_validacao_cruzada.py`](../tests/test_validacao_cruzada.py) | Paridade com o vetor de referência: código de barras, linha digitável e nosso número idênticos. |
| [`test_validacao_externa.py`](../tests/test_validacao_externa.py) | Verificador FEBRABAN **independente** (não usa `core/dv.py`): DV geral, os três DVs de campo, round-trip linha ↔ barras, fator de vencimento, valor, banco e moeda. |
| [`test_boletos_todos.py`](../tests/test_boletos_todos.py) | `EXEMPLOS` cobre **exatamente** o `REGISTRO`; cada banco gera 44/47 dígitos e renderiza PDF nos modelos `classico` e `moderno`. |

> `test_boletos_todos.py` fixa a contagem (`len(EXEMPLOS) == len(REGISTRO) == 18`). Ao entrar com um
> banco novo, **atualize esse número** — é o guarda que impede um banco escapar da validação.

### 5.2 Campo livre de 25 dígitos

O tamanho é garantido indiretamente (`montar_codigo_barras` levanta `ValueError`), mas vale um
teste direto no arquivo do banco, junto com os DVs:

```python
def test_campo_livre_tem_25_digitos() -> None:
    campo = _boleto_exemplo().campo_livre()
    assert len(campo) == 25 and campo.isdigit()
```

Use [`tests/test_bancos_itau.py`](../tests/test_bancos_itau.py) e
[`tests/test_bancos_p1.py`](../tests/test_bancos_p1.py) como modelo para os testes de DV e de
formato de exibição, e [`tests/test_validacao_campos.py`](../tests/test_validacao_campos.py) para as
violações de `regras_campos` (conferindo `BoletoInvalido.erros`).

### 5.3 Remessa — byte a byte

1. Gere o arquivo de referência com os mesmos dados de `_pagamentos()` e `_COMUM_400`/`_COMUM_240`
   de [`tests/test_cnab_remessa.py`](../tests/test_cnab_remessa.py) (data/hora de geração são
   injetáveis justamente para isso).
2. Congele-o em `tests/fixtures/remessa_<slug>_cnab400.rem` (ou `_cnab240.rem`).
3. Acrescente a remessa em `_remessas_400()` / `_remessas_240()`; os testes parametrizados
   `test_remessa_cnab400_byte_a_byte` e `test_remessa_cnab240_byte_a_byte` passam a cobri-la
   automaticamente.
4. [`tests/test_cnab_estrutura.py`](../tests/test_cnab_estrutura.py) descobre os `.rem` por glob e
   revalida o arquivo posição a posição (sequência de registros, larguras, sequenciais e contagens
   dos trailers), sem reusar o gerador. Layouts proprietários entram na lista `_PROPRIETARIOS`.

Para remessa com Bolepix, o mesmo fluxo em
[`tests/test_cnab_remessa_pix.py`](../tests/test_cnab_remessa_pix.py) com a fixture
`remessa_<slug>_pix_cnab400.rem`.

## 6. Documentação

### 6.1 `docs/bancos/<codigo>-<slug>.md`

Siga o **template canônico** já usado por [`341-itau.md`](bancos/341-itau.md) e
[`021-banestes.md`](bancos/021-banestes.md), nesta ordem:

| # | Seção | Conteúdo |
|:-:|-------|----------|
| — | **Cabeçalho** | `# Nome (código)`; manuais oficiais de referência (com remissão a [`fontes-oficiais.md`](bancos/fontes-oficiais.md)); link para o módulo em `pycobranca/bancos/`; dígito do banco; PIX ✅/—; logo empacotado, se houver. |
| 1 | **Resumo** | Uma ou duas linhas com a particularidade do banco (o que o torna diferente). |
| 2 | **Campo livre (posições 20–44 do código de barras)** | Tabela `Posições \| Tam. \| Conteúdo`, somando 25. |
| 3 | **Dígitos verificadores** | Um item por DV: sequência de entrada, algoritmo, fatores e a regra de mapeamento do resto. |
| 4 | **Carteiras suportadas** | Lista do `carteiras`, com nota sobre carteiras fora de escopo. |
| 5 | **Validação de campos (geração do boleto)** | Tabela `Campo \| Regra` espelhando `regras_campos` + link para [`14-validacao-campos.md`](14-validacao-campos.md). |
| 6 | **Formatos de exibição** | Nosso número e agência/conta, com exemplo literal. |
| 7 | **Exemplo** | Entrada e as três saídas (campo livre, código de barras, linha digitável) em bloco de código. Título "Exemplo validado (por vetores de referência ✓)" quando houver paridade; "Exemplo (saída da engine)" quando não. |
| 8 | **Remessa CNAB 400/240** | Só se existir: link do módulo e da fixture + tabela `Registro \| Conteúdo principal`. |

### 6.2 Tabelas de `docs/bancos/README.md`

Registre o banco novo em **todas** as tabelas aplicáveis:

1. **Banco | Documento | Manual oficial de referência** — linha em ordem crescente de código.
2. **Todos os bancos suportados (N)** — `Código | Banco | Particularidade principal`; atualize o
   número no título da seção.
3. **Remessa CNAB — validada byte a byte** — `Banco | CNAB 400 | CNAB 240 | Observação de layout`,
   se houver remessa.
4. **Retorno CNAB** — acrescente o banco à lista do layout correspondente, se houver parser.

Atualize também a matriz do [`05-bancos-suportados.md`](05-bancos-suportados.md), a tabela
"🏦 Bancos suportados" do `README.md` na raiz e, quando houver remessa, o status em
[`06-cnab.md`](06-cnab.md).

## 7. Esqueleto completo (banco fictício)

Banco Exemplo (999), campo livre de 25 posições:

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–4   | 4  | Agência |
| 5–11  | 7  | Convênio |
| 12–22 | 11 | Nosso número |
| 23    | 1  | DV do nosso número (módulo 11, fatores 9..2; resto 10/11 → 0) |
| 24    | 1  | Carteira (1ª posição) |
| 25    | 1  | DV do campo livre (módulo 10 das 24 posições anteriores) |

```python
"""Banco Exemplo (999) — modelo comentado de implementação.

Campo livre (25 posições):

| Posições | Conteúdo |
|----------|----------|
| 1–4   | Agência (4) |
| 5–11  | Convênio (7) |
| 12–22 | Nosso número (11) |
| 23    | DV do nosso número (módulo 11, fatores 9..2; resto 10/11 -> 0) |
| 24    | Carteira (1ª posição) |
| 25    | DV do campo livre (módulo 10 das 24 posições) |
"""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_digitos
from ..core.dv import modulo10, modulo11_flex
from .base import BancoBase

__all__ = ["BancoExemplo"]

#: Regra do manual: resto 10 ou 11 do módulo 11 vira DV 0.
_MAPA_DV = {10: 0, 11: 0}


class BancoExemplo(BancoBase):
    # --- metadados: 'codigo' é o que dispara o auto-registro em REGISTRO ---
    codigo: ClassVar[str] = "999"
    nome: ClassVar[str] = "Banco Exemplo"
    digito_banco: ClassVar[str] = "8"
    carteiras: ClassVar[tuple[str, ...]] = ("1", "2")
    suporta_pix: ClassVar[bool] = False
    # --- tamanhos em dígitos: (mínimo, máximo); o máximo trava o campo livre ---
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "convenio": (1, 7),
        "nosso_numero": (1, 11),
    }

    # --- blocos normalizados: máscara removida + zero à esquerda ---
    @property
    def _agencia4(self) -> str:
        return so_digitos(self.agencia).zfill(4)

    @property
    def _convenio7(self) -> str:
        return so_digitos(self.convenio).zfill(7)

    @property
    def _nosso_numero11(self) -> str:
        return so_digitos(self.nosso_numero).zfill(11)

    # --- DVs: sempre pelos helpers de core/dv.py ---
    @property
    def dv_nosso_numero(self) -> int:
        """DV do nosso número: módulo 11 (fatores 9..2, direita->esquerda)."""
        return modulo11_flex(self._nosso_numero11, mapa=_MAPA_DV)

    # --- 25 dígitos, nem um a mais ---
    def campo_livre(self) -> str:
        base = (
            f"{self._agencia4}{self._convenio7}{self._nosso_numero11}"
            f"{self.dv_nosso_numero}{so_digitos(self.carteira)[:1]}"
        )
        return f"{base}{modulo10(base)}"

    # --- exibição no boleto (alimentam contexto_render/PDF) ---
    def nosso_numero_formatado(self) -> str:
        return f"{self._nosso_numero11}-{self.dv_nosso_numero}"

    def agencia_conta_formatado(self) -> str:
        return f"{self._agencia4} / {self._convenio7}"
```

Saída para agência `1234`, convênio `1234567`, carteira `1`, nosso número `12345678`,
R$ 127,50, vencimento 15/08/2026:

```
Campo livre:      1234123456700012345678914
Código de barras: 99991153900000127501234123456700012345678914
Linha digitável:  99991.23418 23456.700014 23456.789140 1 15390000012750
Nosso número:     00012345678-9
```

## Checklist final

- [ ] `pycobranca/bancos/<slug>.py` com ClassVars, `campo_livre()` de 25 dígitos e formatos.
- [ ] Import + `__all__` em `pycobranca/bancos/__init__.py`.
- [ ] `Bancos.find("<codigo>")` devolve a classe; `boleto.validar()` não levanta no caso feliz.
- [ ] Entrada em `tests/exemplos_boletos.py` e contagem atualizada em `test_boletos_todos.py`.
- [ ] (Opcional) Remessa 400/240 + fixture `.rem` + entrada em `test_cnab_remessa.py`.
- [ ] `docs/bancos/<codigo>-<slug>.md` no template canônico.
- [ ] Tabelas de `docs/bancos/README.md`, `docs/05-bancos-suportados.md` e `README.md` atualizadas.
- [ ] `ruff check . && ruff format --check .` e `pytest` verdes.
