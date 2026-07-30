# Caixa Econômica Federal (104) — SIGCB

**Manuais oficiais de referência:** *Manual de Boleto de Cobrança CAIXA — SIGCB* (2020) ·
*Manual de Leiaute CNAB 240* · *Manual de Leiaute CNAB 400*. Fontes e portal em
[`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas citados.

**Implementação:** [`pycobranca/bancos/caixa.py`](../../pycobranca/bancos/caixa.py) ·
Dígito do banco: **0** · PIX: ✅

**Logo empacotado:** disponível via `logo_do_banco("104")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

SIGCB: nosso número de 17 posições intercalado no campo livre; dois DVs (beneficiário e campo
livre) por módulo 11 Caixa.

## Nosso número (17 posições)

`modalidade(2) + sequencial(15)`, onde a modalidade combina **tipo de cobrança** (1º dígito:
`1` registrada, `2` sem registro) e **identificador de emissão** (2º dígito: `4` beneficiário).
Modalidades usuais: `14` e `24`. Na PyCobrança a modalidade é informada no campo `carteira`.

## Campo livre (25 posições) — intercalação SIGCB

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1–6   | 6 | Código do beneficiário (convênio) |
| 7     | 1 | DV do código do beneficiário (módulo 11) |
| 8–10  | 3 | Nosso número — posições 3 a 5 |
| 11    | 1 | Tipo de cobrança (1º dígito do nosso número) |
| 12–14 | 3 | Nosso número — posições 6 a 8 |
| 15    | 1 | Identificador de emissão (2º dígito do nosso número) |
| 16–24 | 9 | Nosso número — posições 9 a 17 |
| 25    | 1 | DV do campo livre (módulo 11 das 24 posições) |

## Módulo 11 Caixa

Pesos 2..9; `DV = 11 - (soma % 11)`; **DV > 9 vira 0** (mapeamento `{10, 11} → 0` do manual).

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Convênio | 1–6 dígitos |
| Nosso número | 1–15 dígitos |
| Carteira | conjunto: 14, 24 |

## Formatos de exibição — corrigido na validação cruzada

O manual SIGCB define o nosso número impresso com **17 posições + DV**:
`14000000000000123-1`. A implementação inicial da PyCobrança omitia o DV; a divergência foi
detectada na comparação com os vetores de referência e **arbitrada pelo manual oficial** (o vetor de referência estava
correta) — corrigida em `nosso_numero_formatado()`.

## Exemplo validado (por vetores de referência ✓)

Entrada: código do beneficiário `123456`, modalidade `14`, nosso número `123`, R$ 127,50,
vencimento 15/08/2026.

```
Campo livre:      1234560000100040000001230
Código de barras: 10491153900000127501234560000100040000001230
Linha digitável:  10491.23456 60000.100044 00000.012302 1 15390000012750
Nosso número:     14000000000000123-1
```

## Remessa CNAB 240 — implementada e validada byte a byte ✓

**Implementação:** [`pycobranca/cnab/cnab240/caixa.py`](../../pycobranca/cnab/cnab240/caixa.py) ·
fixture: [`tests/fixtures/remessa_caixa_cnab240.rem`](../../tests/fixtures/remessa_caixa_cnab240.rem)

A Caixa opera apenas com CNAB 240 (SIGCB). Estrutura em lotes (registros de 240 posições,
CRLF, maiúsculas sem acentos). Versão do layout de arquivo `050`, de lote `030`.

| Registro | Conteúdo principal |
|----------|--------------------|
| Header de Arquivo (0) | `104` · CPF/CNPJ · convênio zerado(20) · info da conta (agência 5 + DV + convênio 6 + zeros) · empresa(30) · `CAIXA ECONOMICA FEDERAL` · data + hora + sequencial · versão `050` · versão do aplicativo(4) · uso da empresa `REMESSA-PRODUCAO` |
| Header de Lote (1) | serviço `01` (`exclusivo_servico` = `00`) · convênio do lote (convênio 6 + zeros) · info da conta · empresa · versão `030` |
| Segmento P | ocorrência · agência 5 + DV · convênio(6) · **modalidade da carteira**(2, ex. `14`) + nosso número(15) · emissão `2` · vencimento (DDMMAAAA) · valor(15) · espécie `99` · mora/desconto/IOF/abatimento · protesto · baixa (código/dias derivados do protesto) |
| Segmento Q | dados do sacado (tipo/doc 15/nome 40/endereço 40/bairro 15/CEP/cidade 15/UF) · avalista |
| Segmento R | multa (quando houver), com **data da multa = vencimento + 1 dia** |
| Trailers de Lote (5) e de Arquivo (9) | contadores |

`data_multa`/`data_mora` usam **vencimento + 1 dia**; a baixa vira `1`/`120` quando o código
de protesto é `3`, senão `2`/`000`.
