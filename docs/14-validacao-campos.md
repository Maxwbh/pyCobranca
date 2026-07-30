# 14 — Validação de campos e contrato de erros

A PyCobrança valida os dados **na geração** (boleto e remessa CNAB) e reporta os problemas por um
**contrato de erros estruturado**. Este documento é a referência para um consumidor — por exemplo,
uma camada REST — **tratar o erro** e devolver mensagens claras ao usuário. A engine é standalone:
qualquer serviço apenas chama `codigo_barras`/`linha_digitavel` (boleto) ou gera a remessa e captura
as exceções descritas aqui.

## Contrato de erros

| Exceção | Quando | Estrutura |
|---------|--------|-----------|
| `BoletoInvalido` | dados de boleto **ou** de pagamento (remessa) inválidos | `.erros: list[str]` (um item por problema); `str(exc)` = itens unidos por `"; "` |
| `BancoNaoRegistrado` | código FEBRABAN fora do registro | `KeyError` |
| `OFXInvalido` | conteúdo não é um OFX (marcador `<OFX>`/`OFXHEADER` ausente) — na leitura de extrato | `ValueError` |
| `RetornoInvalido` | arquivo de retorno CNAB vazio ou sem header de banco reconhecível | `ValueError` |
| `ErroDeContrato` | serialização fora do contrato REST (`valida_contrato`) | `ValueError` |

> **OFX e retorno CNAB:** `Extrato.ler(...)` levanta `OFXInvalido` para um arquivo que não é OFX
> (em vez de devolver um extrato vazio), e `Retorno.ler(...)` levanta `RetornoInvalido` para um
> arquivo vazio ou sem header — assim o consumidor distingue **arquivo inválido** de **resultado
> vazio**. Um extrato OFX válido **sem transações** não é erro.

Todas herdam de `PyCobrancaError`. O ponto-chave para um consumidor é o atributo **`.erros`** de
`BoletoInvalido` — uma lista, não uma string — que permite mapear cada violação individualmente.

```python
from pycobranca.bancos import Itau
from pycobranca.exceptions import BoletoInvalido

try:
    Itau(agencia="12345", conta="123456", carteira="999", ...).codigo_barras
except BoletoInvalido as exc:
    exc.erros
    # ['carteira '999' não suportada (use uma de: 104, 109, 112, 115, 175, 177, 188)',
    #  'agência deve ter no máximo 4 dígitos',
    #  'conta deve ter no máximo 5 dígitos']
```

### Exemplo de tratamento em uma camada REST

```python
# camada REST (fora da engine) — a PyCobrança não conhece o serviço
from pycobranca.exceptions import BoletoInvalido, BancoNaoRegistrado


def gerar_boleto(payload):
    try:
        return {"linha_digitavel": boleto.linha_digitavel}, 200
    except BoletoInvalido as exc:
        return {"erro": "dados_invalidos", "detalhes": exc.erros}, 422
    except BancoNaoRegistrado:
        return {"erro": "banco_nao_suportado"}, 404
```

## Regras — geração do boleto (por banco)

Campos numéricos aceitam máscara (a pontuação é removida) e são preenchidos com zero à esquerda até
o **máximo**. O **máximo** trava o formato do campo livre; o **mínimo** pega campo vazio/curto. As
**carteiras** são um conjunto fechado (`banco.carteiras`).

| Banco (cód) | Agência | Conta | Convênio | Carteiras válidas | Nosso nº | Especiais / obrigatórios |
|---|---|---|---|---|---|---|
| **Itaú** (341) | 1–4 | 1–5 | — | 104, 109, 112, 115, 175, 177, 188 | 1–8 (+DAC) | — |
| **Banco do Brasil** (001) | 0–4¹ | 0–8¹ | 4 / 6 / 7 | 11, 12, 15, 16, 17, 18, 31, 51 | conv7→10 · conv6→5 · conv4→7 | nosso nº e layout dependem do convênio |
| **Bradesco** (237) | 1–4 | 1–7 | — | 03, 06, 09, 19, 21, 22, 25, 26 | 1–11 (+DV; pode ser `P`) | — |
| **Caixa** (104) | 4² | —³ | 1–6 (cód. benef.) | 14, 24 (modalidade SIGCB) | 1–15 (efetivo 17) | 2 DVs (benef. + campo livre) |
| **Santander** (033) | —³ | fallback⁴ | 1–7 (cód. cedente) | 101, 102, 121 | 1–12 (+DV) | cedente = convênio **ou** conta |
| **Sicoob** (756) | 1–4 | —³ | 0–7 (ou nº contrato) | 1, 3, 9, 09 | 1–7 (+DV) | `numero_contrato` (0–7) na carteira 9 |
| **Sicredi** (748) | 1–4 | 1–5 (convênio) | 1–5 | 1, 3 | 1–5 (+ano+byte+DV) | `byte_idt` **obrig.**; `posto` (0–2); `data_documento` **obrig.** |
| **Banrisul** (041) | 1–4 | —³ | 1–7 | 1, 2 | 1–8 (+duplo dígito) | `digito_convenio` (impressão) |
| **Ailos** (085) | —³ | 1–7 (+DV) | 1–6 | 01, 1 | 1–9 | — |
| **Unicred** (136) | 1–4 | 1–9 (+`digito_conta`) | — | 21 | 1–10 (+DV) | `digito_conta` **obrig.** |
| **Citibank** (745) | 1–4 | —³ | 1–10 | 3 | 1–11 (+DV) | `portfolio` (0–3) |
| **CrediSIS** (097) | 1–4 | —³ | 1–6 | 18 | 1–6 | `cedente_documento` **obrig.** (gera DV) |
| **BRB** (070) | **1–3** | 1–7 | — | 1, 2 | 1–6 (+duplo dígito) | `incremento` (1–3) **obrig.** |
| **Banco do Nordeste** (004) | 1–4 | 1–7 (+`digito_conta`) | — | 21, 31, 41, 51 | 1–7 (+DV) | `digito_conta` |
| **Banestes** (021) | (impressão) | 1–10 (+`digito_conta`) | — | 11, 13 | 1–8 (+DV duplo) | variação; `digito_conta` |
| **C6 Bank** (336) | 4 | —³ | 1–12 | 10, 20 | 1–10 (+DV; pode ser `P`) | indicador 3/4 conforme carteira |
| **HSBC** (399) | 4 (CSB) | 1–7 | — | **CNR, CSB** (alfanum.) | 1–13 | CNR: `data_vencimento` **obrig.** (legado) |
| **Safra** (422) | 1–4 (+`digito_agencia`) | 1–8 (+`digito_conta`) | — | 1, 2 | 1–8 (+DV) | `digito_agencia` e `digito_conta` **obrig.** |

**Notas:** ¹BB só usa agência/conta nos convênios 4 e 6 (mín. 0). ²Caixa: agência só na impressão.
³Não entra no campo livre (o beneficiário vem do convênio). ⁴Santander usa `convenio` ou, na falta,
`conta` (1–7).

### Campos comuns a todos os bancos

| Campo | Tipo | Regra |
|---|---|---|
| `valor` | `Decimal`/`str`/`float` | > 0 (em centavos) |
| `data_vencimento` | `date` | obrigatória |
| `cedente` | `str` | obrigatório |
| `cedente_documento` / `sacado_documento` | `str` | se informado, CPF **ou** CNPJ válido |
| `carteira` | `str` | deve pertencer ao conjunto `banco.carteiras` |

> **Caracteres válidos:** todos os campos de conta/agência/convênio/nosso número são **numéricos**
> (a máscara é descartada; um valor sem dígito nenhum falha no mínimo). A carteira do **HSBC** é
> **alfanumérica** (`CNR`/`CSB`) — validada pelo conjunto.

## Regras — geração da remessa CNAB (`Pagamento`)

`Pagamento.validar()` (chamado ao montar a remessa) verifica campos obrigatórios **e a coerência dos
encargos**:

| Regra | Erro |
|-------|------|
| `nosso_numero`, `documento_sacado`, `nome_sacado`, `endereco_sacado`, `cep_sacado`, `data_vencimento` | `campo obrigatório ausente: <campo>` |
| `valor` | `valor deve ser positivo` |
| valores/percentuais | `<campo> não pode ser negativo` |
| `tipo_mora="1"` (valor ao dia) sem `valor_mora` | `tipo_mora="1" (valor ao dia) exige valor_mora > 0` |
| `tipo_mora="2"` (taxa mensal) sem `percentual_mora` | `tipo_mora="2" (taxa mensal) exige percentual_mora > 0` |
| `codigo_multa` ≠ 0 sem `percentual_multa` | `codigo_multa != 0 exige percentual_multa > 0` |
| desconto 1º/2º/3º indicado sem valor/data | `Nº desconto indicado (cód. != 0) exige valor > 0` / `exige data` |
| `uf_sacado` | `uf_sacado deve ter 2 letras` |
| `cep_sacado` | `cep_sacado deve ter no máximo 8 dígitos` |

Códigos de encargo (referência): `tipo_mora` **1**=valor/dia, **2**=taxa mensal (%), **3**=isento;
`codigo_multa` **0**=isento, **1**/**2**=percentual (FEBRABAN: multa é sempre percentual);
`cod_desconto` **0**=sem desconto, **≠0**=exige valor e data. Detalhe de posições por banco em
[`06-cnab.md`](06-cnab.md).

```python
from datetime import date
from pycobranca.cnab import Pagamento
from pycobranca.exceptions import BoletoInvalido

pag = Pagamento(nosso_numero="123", valor=0, tipo_mora="2", percentual_mora=0)
try:
    pag.validar()
except BoletoInvalido as exc:
    exc.erros
    # ['campo obrigatório ausente: documento_sacado', ..., 'valor deve ser positivo',
    #  'tipo_mora="2" (taxa mensal) exige percentual_mora > 0']
```
