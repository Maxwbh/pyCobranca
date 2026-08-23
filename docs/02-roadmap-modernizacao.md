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
campo. Qualquer tamanho diferente do previsto desloca todas as posições seguintes:

| `conta_corrente` no Sicoob 400 | Registro de detalhe |
|---|---|
| `"1"` | 393 posições |
| `"12345"` | 397 posições |
| `"12345678"` | **400 posições** |
| `"123456789012"` | 404 posições |

Medindo os 12 layouts de 400 com a conferência de tamanho desligada — que é o que revela o
deslocamento cru —, o registro de detalhe sai assim:

| Layout | Conta curta (`"1"`) | Conta longa (12 dígitos) |
|---|:---:|:---:|
| Itaú | 400 | **407** |
| Bradesco | 400 | **405** |
| Banco do Brasil | 400 | **404** |
| Sicoob | **393** | **404** |
| Santander | 400 | **399** |
| Banrisul, Citibank, C6, Unicred | 400 | 400 |

Três coisas que a medição mostra e a leitura do código não sugeria:

- **Só o Sicoob quebra com conta curta.** O Itaú aplica `zfill(5)`, o que resolve a conta curta e
  não a longa; o Sicoob concatena sem ajuste algum. Banrisul e Citibank não usam
  `conta_corrente` no detalhe.
- **O Santander encolhe em vez de crescer**, e por outro motivo: acima de 8 posições ele entra no
  ramo de "conta padrão novo", que grava `conta[8] + digito_conta`. Com `digito_conta` vazio o
  campo sai com um caractere em vez de dois. Não é largura da conta, é um ramo que pressupõe o
  dígito preenchido.
- **Banco de Brasília (402), Banco do Nordeste (401) e CrediSIS (402)** já saem fora de 400 com a
  conta da própria fixture: é o desvio de layout anotado com `tamanho_registro=None`. Eles também
  deslocam com conta longa, mas a conferência de tamanho nunca os guardou.

Dois atenuantes, que é por isso que o item está aqui e não como falha crítica: nos layouts com
`tamanho_registro` declarado, a conferência **detecta e recusa** gerar o arquivo malformado, então
nada inválido chega ao banco; e as fixtures usam contas na largura correta, de modo que a suíte
atual não cobre o caso.

O que a correção exigiria: normalizar `conta_corrente` nos layouts que não normalizam — com
truncamento ou erro explícito para conta longa demais —, preencher o dígito no ramo novo do
Santander e enriquecer a mensagem da conferência, que hoje informa o registro
(`registro 2 com 393 posições`) sem apontar o campo responsável. Nenhuma delas quebra as fixtures
existentes.

Enquanto não for corrigido, a orientação para quem integra está em
[19 — Integração](19-integracao.md#contrato-de-erros).

## Fora de escopo, por decisão

### Bancos que emitem o boleto do próprio lado

Os **18 bancos** cobertos são aqueles cujo campo livre é reproduzível fora do banco. O **Inter
(077)** é o exemplo do que fica de fora: a remessa vai **sem** nosso número e o campo livre
(número de operação de 7 dígitos) é atribuído pela instituição — não há o que calcular
*client-side*, nem vetor oficial recalculável para conferir.

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
