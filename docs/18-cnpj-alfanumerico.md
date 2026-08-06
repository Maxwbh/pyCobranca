---
description: >-
  CNPJ alfanumérico (IN RFB 2.229/2024) no boleto e no CNAB: o que muda, como calcular o dígito
  verificador, o que quebra nos sistemas e como validar em Python.
---

# 18 — CNPJ alfanumérico no boleto e no CNAB

O **CNPJ alfanumérico** entrou em vigor: os sistemas da Receita Federal foram atualizados em
**27/07/2026** e as **primeiras emissões acontecem a partir de 31/07/2026** (IN RFB 2.229/2024).

Se o seu sistema emite boleto ou gera arquivo CNAB, ele vai receber um CNPJ com letras em algum
momento — e a maioria das implementações quebra de um jeito silencioso, que só aparece quando o
banco rejeita o título. Esta página explica o que muda, onde quebra e como a PyCobrança trata.

## O que muda, em uma tabela

| | Antes | Agora |
|---|---|---|
| Posições | 14 | **14** (não muda) |
| 12 primeiras | dígitos | **dígitos ou letras `A`–`Z`** |
| 2 últimas (DV) | dígitos | **dígitos** (continuam numéricos) |
| Padrão | `\d{14}` | **`[A-Z0-9]{12}[0-9]{2}`** |
| CPF | numérico | **numérico** (não muda) |

Os CNPJ numéricos existentes **continuam válidos e não mudam**. Os dois formatos coexistem
indefinidamente — não há migração, não há prazo para converter nada.

## O cálculo do dígito verificador

Continua sendo **módulo 11 com os mesmos pesos**. A única mudança é o valor de cada caractere:

```
valor do caractere = ord(caractere) - 48
```

Ou seja: `"0"` → 0, `"1"` → 1, … `"9"` → 9, `"A"` → 17, `"B"` → 18, … `"Z"` → 42.

O detalhe elegante da norma: para um CNPJ **puramente numérico**, `ord("7") - 48 == 7`, então o
resultado é **idêntico ao cálculo antigo**. Não existe bifurcação — a mesma função serve aos dois
formatos.

```python
from pycobranca.core.documentos import validar_cnpj, formatar_cnpj, cnpj_e_alfanumerico, dv_cnpj

validar_cnpj("12ABC34501DE35")  # True — aceita máscara e minúsculas
formatar_cnpj("12ABC34501DE35")  # '12.ABC.345/01DE-35'
cnpj_e_alfanumerico("12ABC34501DE35")  # True
dv_cnpj("12ABC34501DE")  # '35' — os dois DVs, sempre numéricos

validar_cnpj("11222333000181")  # True — numérico segue funcionando igual
```

!!! tip "Letras que a Receita recomenda evitar"
    A Receita recomenda **não usar `I`, `O`, `Q` e `F`** na emissão, por confusão visual com
    `1`, `0` e dígitos. É uma **recomendação de emissão, não uma regra de validação** — um CNPJ
    que as contenha é válido, e a PyCobrança o aceita. Não rejeite documento por causa disso.

## Onde os sistemas quebram

### 1. `so_digitos()` — o erro mais comum

Quase todo código brasileiro de cobrança tem uma função que "limpa" o documento removendo tudo que
não é dígito:

```python
# ERRADO com CNPJ alfanumérico
def so_digitos(valor):
    return "".join(c for c in valor if c.isdigit())


so_digitos("12ABC34501DE35")  # '123450135' — 9 caracteres, não 14!
```

O CNPJ de 14 posições vira **9 caracteres**. E aí vem o efeito dominó.

### 2. O tipo de inscrição sai errado no CNAB

Os layouts CNAB gravam um **tipo de inscrição**: `01` para CPF, `02` para CNPJ. Quase sempre esse
tipo é decidido pelo **tamanho** do documento limpo — 11 → CPF, 14 → CNPJ.

Com o documento reduzido a 9 caracteres pelo passo anterior, o registro sai marcado como **CPF** e
com o documento **truncado**. O arquivo é aceito pelo formato e rejeitado pelo banco, ou pior:
processado com o sacado errado.

Este foi um bug real corrigido na PyCobrança, em **34 pontos de escrita** de registro CNAB. A
correção tem duas partes: normalizar preservando letras, e decidir o tipo pelo tamanho do
documento **normalizado**, não do documento "só dígitos".

```python
from pycobranca.core.documentos import so_alfanumerico

so_alfanumerico("12.ABC.345/01DE-35")  # '12ABC34501DE35' — 14, íntegro
```

### 3. Campo do boleto com validação numérica

Formulários, colunas de banco de dados (`NUMERIC`), validações de front-end e integrações que
declaram o CNPJ como número passam a rejeitar cadastro legítimo. A conferência aqui é de
inventário, não de código: **onde o CNPJ é armazenado como número em vez de texto?**

## Na PyCobrança

Suportado desde a **1.0.1**, em toda a cadeia:

| Camada | Comportamento |
|---|---|
| Validação | `validar_cnpj` aceita `[A-Z0-9]{12}[0-9]{2}`, com máscara e minúsculas |
| Formatação | `formatar_cnpj` preserva as letras: `12.ABC.345/01DE-35` |
| Boleto | documento do cedente e do sacado aceitam o formato |
| Remessa CNAB | documento gravado íntegro; tipo de inscrição (`01`/`02`) correto |
| Contrato REST | campos de documento têm `pattern` que aceita CPF e CNPJ nos dois formatos |

O `pattern` no contrato permite que uma camada HTTP rejeite formato inválido **antes** de chamar a
engine — ver [Contrato REST](04-api-rest.md).

### Layouts que embutem o documento no campo livre

Alguns layouts calculam parte do campo livre a partir do **documento do beneficiário** — e os
manuais correspondentes são anteriores à norma, sem definir o que fazer quando esse documento tem
letras.

Nesses casos a PyCobrança **falha explicitamente** na emissão, levantando `BoletoInvalido`, em vez
de gerar um código de barras que o banco rejeitaria. Falhar cedo e visível é melhor que emitir
título inválido e descobrir na devolução. Assim que o manual publicar a regra com exemplo
validável, o suporte entra.

A situação por banco está em [14 — Validação de campos](14-validacao-campos.md).

## Checklist para o seu sistema

- [ ] Toda função de "limpar documento" preserva letras quando o documento tem 14 posições
- [ ] O tipo de inscrição CNAB é decidido pelo documento **normalizado**, não pelo "só dígitos"
- [ ] Colunas de banco de dados guardam CNPJ como **texto**, nunca como número
- [ ] Máscaras de entrada e validações de front-end aceitam letras nas 12 primeiras posições
- [ ] Comparações e chaves de conciliação são **case-insensitive** (normalize para maiúsculas)
- [ ] Relatórios e exportações não reformatam o documento como número

## Fontes

- **IN RFB 2.229/2024** — institui o CNPJ alfanumérico
- Nota técnica da Receita Federal sobre o cálculo do DV e as recomendações de emissão
- Layouts CNAB 240/400 (FEBRABAN) para as posições de documento e tipo de inscrição
