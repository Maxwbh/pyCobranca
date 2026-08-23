# 02 — Roadmap de Modernização

O roadmap está organizado em fases incrementais. Cada fase tem um **marco verificável** e
**critérios de aceite** verificados pela CI.

## Fase 0 — Fundação (este entregável)

**Objetivo:** estabelecer documentação, esqueleto de projeto e CI.

- [x] Documentação de arquitetura e plano (`docs/`).
- [x] Empacotamento moderno (`pyproject.toml`).
- [x] Esqueleto do pacote `pycobranca` com versionamento.
- [x] CI de validação (`ci.yml`) em matriz de versões Python.
- [x] Convenções de contribuição e changelog.

**Critério de aceite:** CI verde.

## Fase 1 — Núcleo e emissão de boleto

**Objetivo:** estabelecer o núcleo de emissão de boleto.

- [x] `core/`: dígitos verificadores (módulo 10/11), fator de vencimento (com rollover
  22/02/2025), CPF/CNPJ.
- [x] `boleto/`: composição das 44 posições e linha digitável (com DVs).
- [x] `bancos/`: registro auto-registrável (`Bancos.todos/find/com_pix`) e os **5 bancos P1**
  ponta a ponta — Itaú (341), Banco do Brasil (001, convênios 4/6/7), Bradesco (237, DV base 7
  com "P"), Santander (033) e Caixa (104, SIGCB).
- [x] `render/`: backend **ReportLab único** (modelos classico/moderno, carnê, TEMA),
  validado contra imagens de referência. Ver [11 — Renderização](11-renderizacao.md).
- [~] serialização: `to_dict()` no `BancoBase` (pronta para API REST).
- ~~Camada de compatibilidade~~ — **removida do escopo** (sem retrocompatibilidade).

**Critério de aceite:** emitir boleto válido (PDF + linha digitável + código de barras) para os
5 bancos prioritários, com testes de valor conhecido.
**Status: atendido e validado por vetores de referência** — os mesmos dados gerados na
implementação de referência (Ruby) produzem código de barras e linha digitável idênticos nos 5 bancos
(`tests/test_validacao_cruzada.py`; ver `docs/bancos/`).

## Fase 2 — CNAB Remessa

**Objetivo:** gerar arquivos de remessa.

- [x] `cnab/`: subsistema de remessa (Pagamento + formatação fiel + bases CNAB 400 e 240).
- [x] `cnab/cnab400/`: **12 bancos byte a byte** vs vetores de referência — Itaú, Bradesco, Banco do Brasil,
  Santander, Sicoob, Unicred, Banrisul, Banco do Nordeste, BRB (formato DCB), Citibank, CrediSIS
  e C6.
- [x] `cnab/cnab240/`: **7 bancos byte a byte** vs vetores de referência — Ailos, Banco do Brasil, Caixa,
  Santander, Sicoob, Sicredi e Unicred (estrutura em lotes: header de arquivo/lote, segmentos
  P/Q/R, trailers).
- [x] Validação estrutural (posições por registro, header/trailer, sequenciais) com desvios
  conhecidos do layout anotados (`tamanho_registro=None`).

**Critério de aceite:** remessa 240 e 400 geradas byte-a-byte compatíveis com os vetores de referência para os bancos prioritários. **Status: atendido** — 26 arquivos de remessa validados em
`tests/test_cnab_remessa.py`: 19 combinações banco/layout (12 em 400 e 7 em 240) mais as 7
variantes com segmento PIX; ver [`docs/bancos/`](../docs/bancos/README.md).

## Fase 3 — CNAB Retorno

**Objetivo:** ler arquivos de retorno.

- [x] `cnab/retorno/`: parsing **CNAB 400 e 240** → `list[RegistroRetorno]`/`list[dict]`, com
  auto-detecção de layout (tamanho do registro) e de banco (header). CNAB 400: Itaú, Bradesco,
  Banco do Brasil, Santander (com campos PIX), Banco do Nordeste, Banrisul, CrediSIS, C6, Unicred
  e BRB. CNAB 240: base/Caixa, Santander, Ailos, Sicredi e Sicoob (combinação dos segmentos T/U).
- [x] Mapeamento de códigos de ocorrência (rótulos legíveis, camada de conveniência indicativa).
- [~] Conciliação por `nosso_numero` (dados prontos no `RegistroRetorno`; helper de conciliação
  fica para a integração com o serviço REST).

**Critério de aceite:** retorno parseado corretamente para fixtures reais; ocorrências mapeadas.
**Status: atendido** — 11 arquivos `.RET` (8 em 400 e 3 em 240) parseados **campo a campo idênticos**
aos vetores de referência (`tests/test_cnab_retorno.py`).

## Fase 4 — PIX / Bolepix

**Objetivo:** boleto híbrido com QR Code e segmento PIX no CNAB.

- [x] `pix/payload.py`: BR Code (EMV) copia-e-cola, CRC16 validado contra o vetor do BCB.
- [x] `pix/qr.py`: QR real (matriz p/ ReportLab + SVG), round-trip decodificado do PDF.
- [x] QR Code embutido no PDF do boleto (`pix_chave`/`pix_txid` no `BancoBase`).
- [x] **Segmento PIX na remessa** para bancos habilitados: `PagamentoPix` + **registro tipo 8**
  (CNAB 400: Itaú, Bradesco, C6, Santander) e **segmento Y-03** (CNAB 240: Banco do Brasil,
  Caixa, Sicoob), validados **byte a byte** vs vetores de referência (`tests/test_cnab_remessa_pix.py`).

**Critério de aceite:** Bolepix gerado e validado para ao menos 3 bancos com PIX
(ex.: Banco do Brasil, Bradesco, Itaú). **Status: atendido** — 7 layouts PIX de remessa (4 em 400
e 3 em 240) byte a byte idênticos aos vetores de referência, além do QR no PDF (round-trip OpenCV).

## Fase 5 — Contrato de dados para API REST

**Objetivo:** garantir o contrato de dados (o SDK HTTP é **projeto separado**).

- [x] `pycobranca/contracts/`: serializadores dos artefatos (boleto, `Pagamento`, remessa,
  retorno) para os schemas REST (OpenAPI) e validador leve; contrato vendorizado do
  `openapi.yaml` (v1.5.0).
- [x] Testes de contrato dos artefatos contra o OpenAPI 3.0 (boleto dos 18 bancos + remessa +
  retorno), em `tests/test_contrato_rest.py`.
- [x] Guia de consumo da engine via API REST (doc 04 atualizado com o contrato verificado).

**Critério de aceite:** artefatos validados contra a especificação OpenAPI. **Status: atendido** —
`boleto_para_api`/`pagamento_para_api`/`remessa_para_api`/`retorno_item_para_api` validados por
`valida_contrato` contra `BoletoData`/`RemessaRequest`/`Pagamento`/`RetornoItem`.

## Fase 6 — Paridade e endurecimento

**Objetivo:** ampliar cobertura de bancos e robustez; release 1.0.

- [x] **Release 1.0.0** marcado (`pycobranca.__version__ = "1.0.0"`) com notas de versão no
  `CHANGELOG` consolidando as Fases 1–5.
- [~] **Bancos adicionais** — os **18 bancos** já cobrem o conjunto suportado. Bancos fora desse conjunto (ex.: **Inter/077**) emitem o boleto **no lado do banco**: a
  remessa é enviada **sem** nosso número e o campo livre (nº de operação de 7 dígitos) é atribuído
  pela instituição — **não há campo livre reproduzível client-side** nem vetor oficial
  recalculável. Seguindo o critério de portar **somente com vetor oficial publicado e
  reproduzível**, **nenhum banco novo foi adicionado nesta versão** (evitando enviar lógica não
  verificada). Novos bancos entram sob demanda, com manual oficial + exemplo numérico validável.
- [ ] Ampliação contínua da suíte de testes.
- [x] **Publicação no PyPI** — `pycobranca 1.0.0` publicado (sdist + wheel); instalação por
  `pip install pycobranca`.

**Critério de aceite:** matriz de bancos de [05 — Bancos](05-bancos-suportados.md) completa nos
itens marcados como prioritários; release 1.0. **Status: 1.0.0 marcado**; cobertura de bancos
completa para o conjunto suportado.

## Em aberto

Itens identificados e ainda **não implementados**. Ficam registrados aqui para que a ausência seja
explícita, não uma surpresa para quem avalia o projeto.

### CNAB 444 (Itaú) — remessa e retorno

O **444** é uma variante do Itaú: o registro de 400 posições acrescido de **44 posições de
mensagem** a serem impressas no boleto. Não há suporte na PyCobrança, nem na geração nem na
leitura.

A lacuna foi identificada comparando a cobertura com a [BrCobrança](https://github.com/kivanio/brcobranca),
que oferece `400 e 444` na remessa do Itaú — é a única diferença de layout a favor dela; nos demais
14 bancos em comum a cobertura de remessa é idêntica.

Entra sob o mesmo critério dos outros layouts: **manual oficial com exemplo numérico validável** e
comparação **byte a byte** contra um vetor de referência. Sem isso, o layout não é portado — enviar
arquivo não verificado ao banco é pior que não suportar.

### `conta_corrente` sem ajuste de largura em parte dos layouts CNAB 400

Alguns layouts concatenam `conta_corrente` cru no registro, em vez de ajustá-lo à largura do
campo. Qualquer tamanho diferente do previsto desloca todas as posições seguintes:

| `conta_corrente` no Sicoob 400 | Registro de detalhe |
|---|---|
| `"1"` | 393 posições |
| `"12345"` | 397 posições |
| `"12345678"` | **400 posições** |
| `"123456789012"` | 404 posições |

Varrendo os 12 layouts de 400: com conta **curta** falham **Banrisul, Citibank e Sicoob**; com
conta **longa** falham também **Banco do Brasil, Bradesco e Itaú**.

A causa é divergência entre implementações — o Itaú aplica `zfill(5)` (o que resolve a conta
curta, mas não a longa), enquanto o Sicoob concatena sem ajuste algum.

Dois atenuantes, que é por isso que o item está aqui e não como falha crítica: a conferência de
tamanho do registro **detecta e recusa** gerar o arquivo malformado, então nada inválido chega ao
banco; e as fixtures de teste usam contas na largura correta, de modo que a suíte atual não
cobre o caso.

O que a correção exigiria: normalizar `conta_corrente` nos layouts que não normalizam — com
truncamento ou erro explícito para conta longa demais — e enriquecer a mensagem da conferência,
que hoje informa o registro (`registro 2 com 393 posições`) sem apontar o campo responsável.
Nenhuma das duas quebra as fixtures existentes.

Enquanto não for corrigido, a orientação para quem integra está em
[19 — Integração](19-integracao.md#contrato-de-erros).

## Matriz de rastreabilidade (recurso → Fase)

| Recurso | Fase |
|--------------------|:---------------:|
| Emissão de boleto (PDF) | 1 |
| Linha digitável / código de barras | 1 |
| Registro de bancos (`Bancos.*`) | 1 |
| Validação por banco | 1 |
| Remessa CNAB 240/400 | 2 |
| Retorno CNAB 240/400 | 3 |
| PIX / Bolepix | 4 |
| Serialização JSON | 1 (contínuo) |
| Carnê (3 por A4) | 6 |
| Temização (logo, cor, marca d'água) | 6 |
