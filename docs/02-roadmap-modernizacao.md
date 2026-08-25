---
description: >-
  O que ainda não existe na PyCobrança e o que ficou fora por decisão — com o
  critério que um layout precisa cumprir para entrar.
---

# 02 — Roadmap

As fases 0 a 6 do plano original estão **concluídas** — núcleo, boleto, CNAB 240/400, PIX,
contrato REST e o release 1.0. O que elas entregaram é descrito nas páginas do recurso, que são
onde os números ficam atualizados:

| O que | Onde |
|---|---|
| Escopo e arquitetura | [00 — Visão geral](00-visao-geral.md) · [01 — Arquitetura](01-arquitetura.md) |
| Tudo o que é chamável | [20 — Superfície pública](20-superficie-publica.md) |
| Bancos e o que cada um suporta | [05 — Bancos suportados](05-bancos-suportados.md) |
| Remessa e retorno | [06 — CNAB](06-cnab.md) |
| Bolepix | [07 — PIX](07-pix.md) |
| Extrato e conciliação | [13 — OFX](13-ofx.md) |
| Contrato de dados | [04 — Contrato REST](04-api-rest.md) |
| Como cada afirmação é verificada | [17 — Compatibilidade](17-compatibilidade.md) |

Esta página guarda o resto: **o que ainda não existe** e **o que ficou de fora por decisão**. Os
dois estão aqui para que a ausência seja explícita, não uma surpresa para quem avalia o projeto.

## O critério de entrada

Vale para todo layout novo — banco, remessa, retorno: **manual oficial com exemplo numérico
validável** e comparação **byte a byte** contra um vetor de referência. Sem os dois, o layout não
é portado. Enviar ao banco um arquivo montado a partir de lógica não verificada é pior do que não
suportar o layout.

## Em aberto

### CNAB 444 (Itaú) — remessa e retorno

O **444** é uma variante do Itaú: o registro de 400 posições acrescido de **44 posições de
mensagem** a serem impressas no boleto. Não há suporte na PyCobrança, nem na geração nem na
leitura.

A lacuna foi identificada comparando a cobertura com a
[BrCobrança](https://github.com/kivanio/brcobranca), que oferece `400 e 444` na remessa do Itaú —
é a única diferença de layout a favor dela; nos demais 14 bancos em comum a cobertura de remessa
é idêntica.

### `conta_corrente` sem ajuste de largura em parte dos layouts CNAB 400

Alguns layouts concatenam `conta_corrente` cru no registro, em vez de ajustá-lo à largura do
campo. Qualquer tamanho diferente do previsto desloca todas as posições seguintes — o registro que
o layout montaria fica assim:

| `conta_corrente` no Sicoob 400 | Registro que seria montado | Hoje |
|---|---|---|
| `"1"` | 393 posições | recusado |
| `"12345"` | 397 posições | recusado |
| `"12345678"` | **400 posições** | emitido |
| `"123456789012"` | 404 posições | recusado |

**Estado atual — nenhum layout emite mais registro deslocado.** A varredura de valores-limite
(`tests/test_limites_campos.py`) percorre agência, conta e nosso número em todos os tamanhos de 0
a 20 dígitos, nos 14 layouts de 400 e nos 7 de 240, e o resultado é sempre um dos dois: registro
de 400/240 posições, ou recusa com `BoletoInvalido`. O arquivo malformado deixou de ser uma saída
possível.

Três coisas mudaram desde a medição original:

- **Os quatro layouts que saíam fora de 400/240 voltaram ao tamanho do formato.** Banco de
  Brasília, Banco do Nordeste, CrediSIS e o segmento P do Santander 240 saíam com 401, 402 e 241
  posições **com os dados da própria fixture**, e cada módulo anotava isso como desvio do layout
  do banco, com `tamanho_registro = None`. Não era desvio de layout: era `rjust` estourando o
  campo, e o `None` desligava a única conferência que pegaria. Hoje os quatro conferem o tamanho
  (o BRB com `(39, 400)`, pelo header DCB) e um teste exige que nenhuma remessa desligue a
  checagem.
- **Agência, conta e nosso número passaram por `campo_numerico`** onde o valor podia não caber, e
  a recusa **nomeia o campo**: `conta_corrente: '999999999999' não cabe em 7 posições`.
- **A conferência de tamanho guarda todos os layouts**, inclusive os quatro que antes escapavam.

O que continua aberto: nos campos que ainda não passam por `campo_numerico`, a recusa vem da
conferência de tamanho, cuja mensagem informa o registro (`registro 2 com 393 posições`) **sem
apontar o campo responsável**. O arquivo errado não sai — a mensagem é que é pior do que poderia.
Fechar isso é uma varredura por vinte módulos, e cada campo precisa do layout do banco para saber
a largura; entra por banco, junto com o manual.

A orientação para quem integra está em
[19 — Integração](19-integracao.md#contrato-de-erros).

## Fora de escopo, por decisão

### Bancos que emitem o boleto do próprio lado

Os **19 bancos** cobertos são aqueles cujo campo livre é reproduzível fora do banco. O corte é
**por carteira, não por banco** — o Inter (077) é o exemplo: a carteira **110** entra, porque o
cliente numera a partir de uma faixa recebida antes; a **112** fica de fora, porque ali o nosso
número é atribuído pela instituição depois de receber a remessa. Não há o que calcular
*client-side* numa carteira assim, e a PyCobrança **recusa** a 112 na validação em vez de gerar um
título com um número que o banco nunca emitiu.

Banco novo entra sob demanda, pelo [critério de entrada](#o-criterio-de-entrada).

### Cliente HTTP

A biblioteca transforma dados em arquivos e documentos; não fala rede. O que ela oferece para
quem quer expor isso por HTTP é o **contrato de dados** — schemas, serializadores, o caminho de
volta e um validador leve, em [04](04-api-rest.md). Servidor, autenticação, fila e persistência
são de quem expõe, e [19 — Integração](19-integracao.md) lista essa fronteira item a item.

### Retrocompatibilidade com bibliotecas anteriores

Não há camada de compatibilidade com `pyboleto`, BrCobrança ou qualquer outra API. A dívida de
manter dois vocabulários não se pagaria, e a paridade que importa — **o que sai no arquivo e no
código de barras** — é verificada contra os vetores dessas implementações, não copiando a
interface delas. Ver [17 — Compatibilidade](17-compatibilidade.md).
