---
description: >-
  Boleto Safra (422) em Python: campo livre posição a posição, dígitos verificadores, nosso número, carteiras aceitas (1, 2) e remessa/retorno CNAB 400 conforme o manual oficial.
---

# Safra (422)

**Manual oficial de referência:** *Leiaute de Arquivos — Cobrança CNAB 400* (Banco Safra). Fontes e
portal em [`fontes-oficiais.md`](fontes-oficiais.md) — os PDFs não são redistribuídos, apenas
citados.

**Implementação:** [`pycobranca/bancos/safra.py`](../../pycobranca/bancos/safra.py) ·
Dígito do banco: **7** · PIX: —

**Logo empacotado:** disponível via `logo_do_banco("422")` — a marca é do banco (uso nominativo); ver [`render/logos/NOTICE.md`](../../pycobranca/render/logos/NOTICE.md).

## Resumo

DV do nosso número calculado da esquerda para a direita (mapa 10→0, 11→1).

## Campo livre (posições 20–44 do código de barras)

| Posições | Tam. | Conteúdo |
|:--------:|:----:|----------|
| 1     | 1 | `7` (constante) |
| 2–5   | 4 | Agência |
| 6     | 1 | Dígito da agência |
| 7–14  | 8 | Conta |
| 15    | 1 | Dígito da conta |
| 16–23 | 8 | Nosso número |
| 24    | 1 | DV do nosso número |
| 25    | 1 | `2` (constante) |

A posição 25 é **fixa em `2`** — o manual (seção 7.2.7) a descreve como *"Fixo o número 2 =
Cobrança Registrada"*. Ela **não** carrega a carteira: `1` e `2` distinguem cobrança simples de
vinculada no arquivo CNAB, e as duas produzem o mesmo campo livre.

## Dígitos verificadores

- **DV do nosso número**: módulo 11 sobre o nosso número de 8 posições, percorrido **da esquerda
  para a direita** (`da_direita=False`), fatores 9..2 cíclicos. O DV é `11 - (soma % 11)`, com o
  mapa final `10 → 0` e `11 → 1`.

O mapa das bordas vem literal do manual (seção 7.1): *"Se na divisão o resto for 0, o dígito de
controle será 1"* e *"se o resto for 1, o dígito será 0"*. São os casos que aparecem em cerca de
um a cada onze títulos — errá-los produz um boleto que imprime e é recusado no banco.

Os dígitos de agência e conta (`digito_agencia`/`digito_conta`) são informados pelo beneficiário e
são obrigatórios para montar o campo livre.

## Validação de campos (geração do boleto)

Tamanhos em **dígitos** (mín.–máx.); a máscara é descartada e o valor é preenchido com zero à esquerda. Violações vêm em `BoletoInvalido.erros` (lista) — ver o [contrato de erros e a matriz completa](../14-validacao-campos.md).

| Campo | Regra |
|-------|-------|
| Agência | 1–4 dígitos |
| Dígito da agência | 1 dígito — entra no campo livre em 1 posição |
| Conta | 1–8 dígitos |
| Dígito da conta | 1 dígito — entra no campo livre em 1 posição |
| Nosso número | 1–8 dígitos |
| Carteira | conjunto: 1, 2 |

## Formatos de exibição

- Nosso número: `nosso_numero-DV` → `12345678-9`
- Agência/conta: `01234 / 000123456`

## Exemplo (saída da engine)

Entrada: agência `0123`, dígito da agência `4`, conta `00012345`, dígito da conta `6`, carteira `1`,
nosso número `12345678`, R$ 127,50, vencimento 15/08/2026.

```
Campo livre:      7012340001234561234567892
Código de barras: 42291153900000127507012340001234561234567892
Linha digitável:  42297.01232 40001.234562 12345.678929 1 15390000012750
```

## Sobre a evidência

O Safra tem **as duas procedências**: vetor cruzado com uma implementação de produção
independente (em `exemplos_boletos.py`) **e** conferência contra o manual oficial.

O manual acrescentou o que o vetor não podia dar — dois sistemas concordarem prova que a saída
não é invenção de um só, não que ambos estejam certos:

- o **DV do nosso número** conferido contra os **três exemplos resolvidos** da seção 7.1,
  incluindo o de resto zero, que exercita a borda do mapa;
- as **posições do campo livre** conferidas uma a uma contra a tabela da seção 7.2.2;
- a **linha digitável** conferida contra a tabela da seção 7.2.3, que o manual descreve à parte —
  ali a agência aparece **partida**, com os quatro primeiros dígitos em 6–9 e o último em 11.
  Conferir contra essa tabela pega o que o round-trip com o código de barras não pegaria, porque
  os dois estariam errados juntos.

As duas confirmaram a implementação existente sem exigir mudança nela. Ver
[`tests/test_bancos_safra.py`](../../tests/test_bancos_safra.py).

## Nosso número: quem numera

O manual descreve três modalidades (seção 5), e só duas são componíveis aqui:

| Modalidade | Quem numera | Boleto offline |
|---|---|:--:|
| Cobrança Convencional | o **banco**; o campo vai zerado na remessa | ✗ |
| Cobrança Direta, faixa pré-determinada | a empresa, a partir da faixa que o banco entrega | ✓ |
| Cobrança Direta, numeração livre | a empresa | ✓ |

Na convencional o número **só existe depois, no retorno** — não há código de barras a montar
antes disso. É o mesmo corte por modalidade descrito em
[05 — Ausências que são permanentes](../05-bancos-suportados.md).

A faixa vem do banco: *"O banco informará à empresa a faixa de numeração (INICIAL E FINAL)"*
(seção 7.1). A tabela de consistências da remessa exige o que isso produz — nosso número
*"Diferente de 0"* e com *"Dígito de Controle Válido"*.

## Remessa CNAB 400 — implementada

**Implementação:** [`pycobranca/cnab/cnab400/safra.py`](../../pycobranca/cnab/cnab400/safra.py) ·
fixture: [`tests/fixtures/remessa_safra_cnab400.rem`](../../tests/fixtures/remessa_safra_cnab400.rem)

Registros de 400 posições (header, N detalhes tipo 1, trailer), conforme a seção 6.1.

Três diferenças em relação ao layout comum dos demais bancos:

| Onde | O que muda |
|---|---|
| Trailer, posições 369–376 e 377–391 | **quantidade de títulos e valor somado** (o trailer genérico leva brancos ali) |
| Detalhe, posições 206–218 | o campo de **abatimento** carrega a **multa**, em formato próprio |
| Detalhe, posições 140–142 e 389–391 | **banco cobrador/emitente** configurável: `422`, `341` ou `237` |

!!! danger "Nosso número na remessa: 8 ou 9 dígitos, nunca preenchido com zero"
    A faixa que o Safra entrega vem com **8 dígitos, sem DV**. As 9 posições do campo (63–71)
    pedem número **+ DV** — completar com zero à esquerda desloca o valor inteiro uma casa e o
    banco recusa na consistência *"Dígito de Controle Válido"*. As 9 posições continuam
    numéricas, então isso **passa em validador de layout** e só quebra no processamento.

    `nosso_numero9()` aceita as duas formas: com 8 dígitos calcula o DV, com 9 valida o que veio.

### Multa: ocupa o campo de abatimento

O Safra não tem campo próprio para multa. A nota 6.1.8 manda gravá-la **dentro do campo de
abatimento**, com forma específica:

| Posições | Conteúdo |
|:--------:|----------|
| 157–158 | primeira instrução, obrigatoriamente `16` |
| 206–211 | data a partir da qual a multa vale (`ddmmaa`) |
| 212–215 | percentual, no formato `99v99` |
| 216–218 | zeros |

Consequências que a biblioteca impõe em `validar()`, em vez de deixar passar:

- **multa e abatimento não cabem no mesmo título** — um sobrescreveria o outro em silêncio;
- a multa é **percentual**, não valor: quatro posições em `99v99` não comportam um valor;
- `data_multa` é obrigatória e **posterior ao vencimento** (*"A data da multa deve ser superior a
  data de vencimento"*).

### Correspondentes Itaú e Bradesco

As seções 8 e 9 do manual descrevem o arranjo em que o Safra emite sob o código de outro banco.
`banco_cobrador` grava `341` ou `237` nas posições 140–142 e 389–391; nesse caso o boleto sai
com o código do correspondente, já atendido pelas implementações desses dois bancos.

## Retorno CNAB 400 — implementado

**Layout:** `LAYOUTS_400["422"]` em
[`pycobranca/cnab/retorno/cnab400.py`](../../pycobranca/cnab/retorno/cnab400.py) ·
fixture: [`tests/fixtures/retorno_safra_cnab400.ret`](../../tests/fixtures/retorno_safra_cnab400.ret)

Datas e valores caem nas posições comuns — o risco está em outro lugar:

| Campo | Safra | Layout de reserva (Itaú) |
|---|:--:|:--:|
| **Nosso número** | **63–71** (9 posições) | 63–70 (8 posições) |
| Motivo | **105–107** (código de rejeição) | 378–385 |

Sem a entrada `422`, o parser cai no layout de reserva e lê **oito** posições onde o Safra grava
nove: o nosso número sai **sem o dígito verificador**, sem erro e sem aviso, e a conciliação
passa a comparar um número que não é o do título.
`test_sem_o_layout_proprio_o_safra_perderia_o_dv_do_nosso_numero` mede exatamente isso.

### Códigos de ocorrência próprios

A nota 6.2.2 define códigos que **divergem do padrão FEBRABAN**, e um deles inverte o sentido:

| Código | Safra | Padrão FEBRABAN |
|:--:|---|---|
| **40** | **Baixa de título protestado** | **Baixa por ter sido liquidado** |
| 42 | Título retirado do cartório | Alteração de nosso número |
| 44 | Aceite do título DDA pelo pagador | Título pago com cheque devolvido |
| 51 | Valor do título alterado | Título DDA reconhecido pelo sacado |
| 52 | Acerto de data de emissão | Título DDA não reconhecido pelo sacado |
| 53 | Acerto de código de espécie | Título DDA recusado pela CIP |

O `40` é o perigoso: no padrão significa título **pago**, no Safra significa **protestado**.
Por isso a sobreposição em `OCORRENCIAS_400_POR_BANCO`, consultada antes do mapa padrão —
`descreve_ocorrencia` aceita o banco, e `Retorno.descricao_ocorrencia` o repassa sozinho.

O Safra também **não usa** `07` nem `08` (liquidação parcial e por saldo).

!!! warning "A fixture do retorno foi montada a partir do manual"
    Não há arquivo de retorno real do Safra aqui: a fixture foi construída posição a posição
    conforme a seção 6.2. Ela prova o **mapeamento**, não o arquivo que o banco de fato emite.
    Um retorno real fecharia essa lacuna — se você tiver um, [abra uma
    issue](https://github.com/Maxwbh/pyCobranca/issues).

## CNAB 240 — não existe para cobrança no Safra

Não é lacuna: o manual de cobrança do Safra descreve **apenas o CNAB 400**.
