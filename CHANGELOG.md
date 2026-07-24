# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue
[SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [1.0.0] - 2026-07-24

Primeira versão pública — cobrança bancária brasileira em Python 3.14+ puro
(boleto, CNAB 240/400 e PIX/Bolepix), com 18 bancos e um único `pip install`.

### Adicionado

- **Logo opt-in no boleto** (`banco.logo`): o cabeçalho do recibo, da ficha e de ambos os lados do
  carnê aceita um logo opcional fornecido pelo chamador — `bytes` de PNG/JPEG, caminho de arquivo
  ou `ImageReader` — desenhado no lugar do nome do banco, com a proporção preservada. Sem logo, a
  saída permanece **byte a byte idêntica** ao comportamento anterior.
- **Logos de bancos empacotados** (`pycobranca/render/logos/`, `logo_do_banco`/`bancos_com_logo`):
  conveniência com os logos de 12 bancos (BB, Bradesco, Itaú, Santander, Caixa, C6, Sicredi,
  Sicoob, Banco do Nordeste, Banrisul, Ailos, Unicred), nomeados pelo código FEBRABAN. As marcas
  são de propriedade dos respectivos bancos (uso nominativo, para identificar o emissor);
  atribuição e origem (laravel-boleto, MIT) em `logos/NOTICE.md`. Validação visual de todos os 12
  logos renderizados no cabeçalho.
- **Validação externa do boleto** (`tests/test_validacao_externa.py`): um verificador FEBRABAN
  **independente do núcleo** confere os 18 bancos como faria um sistema externo ao receber o
  título — DV geral (módulo 11) do código de barras, os três DVs de campo (módulo 10) da linha
  digitável, **reconstrução da linha digitável → código de barras** (round-trip), decodificação do
  fator de vencimento de volta à data e conferência de valor, banco e moeda.
- Fonte única de exemplos por banco (`tests/exemplos_boletos.py`), compartilhada entre a validação
  cruzada com vetores de referência e o validador externo.
- **README de divulgação**: GIF do fluxo (`pip install` → boleto → PIX → remessa CNAB), galeria
  com capturas reais (boleto tradicional, boleto com PIX e carnê, rasterizadas dos PDFs gerados),
  diagrama de arquitetura em SVG, tabela de comparação (PyCobrança × PyBoleto × BrCobrança),
  seções "Para quem é" e "Roadmap", e palavras-chave (SEO).

- **Validação estrutural independente das remessas CNAB** (`tests/test_cnab_estrutura.py`): um
  verificador FEBRABAN que lê cada arquivo `.rem` posição a posição — como o intake de um banco ou
  um validador online (ValidaCNAB/Toolspace) faria — **sem reusar o código gerador**. Cobre os 26
  arquivos de remessa (400, 240 e PIX): sequência header→detalhe→trailer, larguras, numeração
  sequencial, ordem dos segmentos e as contagens dos trailers de lote e de arquivo. O layout
  proprietário DCB do BRB é validado à parte.
- **Validação independente do retorno CNAB** (`tests/test_retorno_estrutura.py`): confere a
  estrutura FEBRABAN dos arquivos `.RET` (header → detalhe → trailer, código do banco, tipos de
  registro) e faz o **cross-check do parser** — releitura independente confirma que a contagem de
  registros bate com as linhas de detalhe (400) e com os segmentos T (240), e que cada
  `nosso_numero` extraído está de fato na linha de origem.
- **Fixtures de retorno externos** (`tests/fixtures/retorno/externos/`, `tests/test_retorno_externos.py`):
  retornos CNAB **reais de terceiros** — Caixa 240, HSBC 400 e Sicredi 400 — do projeto laravel-boleto
  (MIT, atribuição em `externos/NOTICE.md`), como regressão independente sobre dados que não geramos.
- **Boletos reais externos** (`tests/test_boleto_externo.py`): o mesmo validador FEBRABAN independente
  é aplicado a linhas digitáveis e códigos de barras **reais** de validadores públicos (Bradesco, Banco
  do Brasil), confirmando os DVs (módulo 10/11) e a reconstrução linha↔código sobre dados de banco reais.

### Corrigido

- **CNAB 240 com PIX — contagem no trailer de arquivo.** A *quantidade de registros do arquivo*
  passava a excluir os segmentos Y (PIX): o trailer de lote os contava, mas o de arquivo não,
  ficando abaixo do total físico — um arquivo que o intake bancário rejeitaria. Agora a contagem
  usa o total real de registros (tipos 0/1/3/5/9), conforme o **Layout Padrão FEBRABAN CNAB 240**.
  Correção arbitrada pela documentação oficial; os fixtures `*_pix_cnab240.rem` (Banco do Brasil,
  Caixa, Sicoob) foram atualizados e **divergem propositalmente** do vetor de referência.
- **Retorno CNAB 400 — trailer vazando como registro.** O parser processava todas as linhas após
  o header, incluindo o **trailer (tipo 9)**, que entrava em `registros` como um título fantasma
  (nosso número zerado, ocorrência vazia). Agora o trailer é ignorado: `registros` contém apenas os
  registros de detalhe. As contagens esperadas em `tests/test_cnab_retorno.py` foram ajustadas.

### Alterado

- **Instalação única**: `reportlab` e `qrcode` passam a ser dependências do pacote (ambos Python
  puro) — `pip install pycobranca` já entrega boleto, CNAB, PIX, PDF e QR, sem extras a decorar.
- **Refatoração do backend ReportLab** (`render/reportlab.py`): o corpo procedural gigante do boleto
  foi decomposto em seções nomeadas (`desenha_tema`, `recibo_moderno`/`recibo_classico`,
  `bloco_demonstrativo`, `corte`, `ficha_moderna`/`ficha_classica`) com um orquestrador claro no fim;
  o carnê extraiu `desenha_parcela`; e o primitivo de escrita de texto foi unificado em `_faz_texto`.
- **Separação dados × desenho** (`_Info`/`_informacoes`): boleto e carnê passam a consumir um
  **view-model único** extraído do contexto — a fonte de informações fica em um só lugar e o desenho
  (layout) não acessa mais o dicionário diretamente, facilitando criar novos temas/layouts.
- **Modelo `moderno` como padrão**: `render_boleto_pdf(ctx)` sem `modelo` agora gera o layout
  **moderno** (Recibo do Pagador com chips e paleta teal; a célula PIX aparece só quando há dados de
  PIX). O layout tradicional continua disponível via `modelo="classico"`.
- **Funções de render renomeadas**: `render_boleto_reportlab_pdf` → **`render_boleto_pdf`** e
  `render_carne_reportlab_pdf` → **`render_carne_pdf`** (o sufixo do backend era redundante, já que o
  ReportLab é o único). Toda a refatoração foi **verificada byte a byte** (PDF idêntico em 6 cenários
  sob `rl_config.invariant`).

## [1.0.0] — 2026-07-24

Primeira versão estável da PyCobrança: plataforma de cobrança bancária brasileira em Python
(boleto, CNAB, PIX). Marcos consolidados nas Fases 1–5:

- **Emissão de boleto** para **18 bancos**, com código de barras (44 posições) e linha digitável
  **idênticos** aos vetores de referência (validação congelada em `tests/`).
- **Renderização** exclusiva via **ReportLab** (modelos `classico`/`moderno`, carnê, TEMA e
  Bolepix), ~120× mais rápida que o backend HTML/CSS de referência.
- **PIX real** (BR Code EMV + CRC16 validado contra o vetor do BCB, QR com round-trip) e
  **Bolepix na remessa** (registro tipo 8 no CNAB 400; segmento Y-03 no CNAB 240).
- **Remessa CNAB 400** (12 bancos) e **CNAB 240** (7 bancos), **byte a byte** vs vetores de referência.
- **Retorno CNAB 400/240** parseado **campo a campo** idêntico aos vetores de referência (11 arquivos `.RET`).
- **Contrato de dados** REST (OpenAPI 3.0 v1.5.0) verificado por testes.
- **Suíte com 143 testes** (ruff limpo); documentação por banco no padrão `docs/Banco C6/`.

> **Escopo de bancos adicionais (Fase 6):** os 18 bancos cobrem o conjunto suportado. Bancos fora desse conjunto (ex.: Inter/077) emitem o boleto **no lado do banco**
> (a remessa vai sem nosso número; o campo livre é atribuído pela instituição) e **não têm campo
> livre reproduzível client-side** nem vetor oficial recalculável — por isso, seguindo o critério
> de só portar com **vetor oficial publicado e reproduzível**, nenhum banco novo foi adicionado
> nesta versão. Novos bancos entram mediante manual oficial com exemplo numérico validável.

### Adicionado (Fase 1 — Núcleo e emissão de boleto)
- `pycobranca/core/`: dígitos verificadores (módulo 10 e módulo 11 do código de barras FEBRABAN),
  **fator de vencimento com a regra de reinício de 22/02/2025** e validação/formatação de
  CPF/CNPJ — com testes de vetores conhecidos.
- `pycobranca/boleto/`: montagem das **44 posições** do código de barras (DV geral módulo 11) e
  da **linha digitável** (3 campos com DV módulo 10).
- `pycobranca/bancos/`: `BancoBase` (dataclass com validações comuns, `to_dict()` alinhado à
  API REST e `contexto_render()` para o ReportLab) com **auto-registro**
  (`Bancos.todos/find/com_pix`) e **Itaú (341) ponta a ponta** (campo livre, DACs, formatadores),
  testado do domínio ao PDF.
- `pycobranca/exceptions.py`: hierarquia de erros (`BoletoInvalido`, `BancoNaoRegistrado`).
- **Bancos P1 completos** (emissão ponta a ponta, testada até o PDF): **Banco do Brasil (001)**
  com convênios de 4/6/7 dígitos; **Bradesco (237)** com DV do nosso número em módulo 11 base 7
  (restos 1→"P" e 0→"0"); **Santander (033)** com código do cedente e IOS; **Caixa (104)** no
  layout SIGCB (intercalação do nosso número e DVs módulo 11). `modulo11_resto` adicionado ao
  núcleo; campo `convenio` no `BancoBase`.

### Adicionado (Fase 5 — Contrato de dados para API REST)
- `pycobranca/contracts/`: alinhamento do **contrato de dados** REST (engine
  permanece **sem dependência HTTP** — o SDK é projeto separado). Serializadores dos artefatos
  para os schemas do OpenAPI 3.0: `boleto_para_api` (→ `{"bank", "data"}` com `BoletoData`),
  `pagamento_para_api` (→ `Pagamento`), `remessa_para_api` (→ `RemessaRequest`) e
  `retorno_item_para_api` (→ `RetornoItem`, valores em centavos → reais e ocorrência traduzida).
- `valida_contrato(dados, schema)`: validador leve (obrigatórios, tipos, `enum`, itens de array
  via `$ref`) e `SLUG_POR_CODIGO` (código FEBRABAN → slug do banco aceito pela API).
- Contrato **vendorizado** de um `openapi.yaml` de referência (v1.5.0) em
  `pycobranca/contracts/contrato_rest.json` (mantido em sincronia manual com o upstream).
- **Testes de contrato** (`tests/test_contrato_rest.py`): serialização de boleto validada
  para os **18 bancos**, mais remessa e retorno (fixtures `.RET`), garantindo compatibilidade
  contínua conforme a API evolui. Doc 04 atualizado com o guia de consumo.

### Adicionado (Fase 3 — CNAB Retorno)
- `pycobranca/cnab/retorno/`: leitura de arquivos de retorno com `Retorno.ler(caminho)` —
  **auto-detecção** do layout (240/400 pelo tamanho do registro) e do banco (pelo header) e
  `RegistroRetorno` (dataclass com `to_dict()` JSON-friendly).
- **CNAB 400 — 10 bancos**: Itaú (341), Bradesco (237, com agência+DV calculada em módulo 11),
  Banco do Brasil (001), Santander (033, com campos PIX `tipo_chave_dict`/`codigo_chave_dict`/
  `txid`), Banco do Nordeste (004), Banrisul (041), CrediSIS (097), C6 (336), Unicred (136) e
  BRB (070). **CNAB 240 — base/Caixa (104), Santander (033), Ailos (085), Sicredi (748) e
  Sicoob (756)** com combinação dos segmentos **T** (dados gerais) e **U** (valores).
- **Validação campo a campo** contra vetores de referência: 11 arquivos `.RET` parseados
  com **resultado idêntico** (extração posicional com faixas inclusivas do parseline, remoção de
  espaços das pontas e transformações de `motivo_ocorrencia` por banco). Fixtures em
  `tests/fixtures/retorno/` e verificação em `tests/test_cnab_retorno.py`.
- `retorno/ocorrencias.py`: tradução dos códigos de ocorrência para rótulos legíveis (camada de
  conveniência **indicativa**, padrão FEBRABAN, sem impacto no parsing).

### Adicionado (Fase 4 — PIX real)
- `pycobranca/pix/`: **payload EMV (BR Code)** com CRC16-CCITT-FALSE **validado byte a byte
  contra o exemplo canônico do manual do BCB** (CRC `1D3D`); normalização de acentos e limites
  de campo (nome ≤25, cidade ≤15, txid alfanumérico ≤25); **QR Code real** via `qrcode`
  (matriz para o ReportLab + SVG).
- Bolepix integrado ao domínio: campos `pix_chave`/`pix_txid`/`cedente_cidade` no `BancoBase`;
  `contexto_render()` monta o PIX automaticamente (com validação de `suporta_pix`).
- **Round-trip comprovado**: o QR desenhado no PDF (ReportLab) decodifica de volta ao
  copia-e-cola exato (verificado com OpenCV).
- **Segmento PIX na remessa (Bolepix)**: `PagamentoPix` (chave DICT/TXID + limites de valor) e os
  registros PIX — **tipo 8** no CNAB 400 (`RemessaItau400Pix`, `RemessaBradesco400Pix`,
  `RemessaBancoC6_400Pix`, `RemessaSantander400Pix`) e **segmento Y-03** no CNAB 240
  (`RemessaBancoBrasil240Pix`, `RemessaCaixa240Pix`, `RemessaSicoob240Pix`), gerados após o
  detalhe/segmentos de cada título e validados **byte a byte** vs vetores de referência
  (`tests/test_cnab_remessa_pix.py`, fixtures em `tests/fixtures/remessa_*_pix_cnab*.rem`).

### Adicionado (Fase 2 — CNAB Remessa)
- `pycobranca/cnab/`: subsistema de remessa — `Pagamento` (campos e formatadores CNAB,
  incluindo `formata_documento_ou_numero`, `identificacao_sacado/avalista`, datas de multa/2º
  desconto), formatação fiel (`format_size` com a mesma ordem de limpeza do Ruby, `format_valor`,
  remoção de acentos + CRLF + maiúsculas no arquivo) e bases **CNAB 400** e **CNAB 240**.
- **Remessa CNAB 400 — 12 bancos byte a byte** vs vetores de referência: Itaú (341), Bradesco (237), Banco do
  Brasil (001), Santander (033), Sicoob (756), Unicred (136), Banrisul (041), Banco do Nordeste
  (004), Banco de Brasília/BRB (070, formato **DCB**), Citibank (745), CrediSIS (097) e C6 (336).
- **Remessa CNAB 240 — 7 bancos byte a byte** vs vetores de referência: Ailos (085), Banco do Brasil (001),
  Caixa (104), Santander (033), Sicoob (756), Sicredi (748) e Unicred (136) — estrutura em lotes
  (header de arquivo/lote, segmentos P/Q/R, trailers de lote/arquivo).
- Fixtures congeladas em `tests/fixtures/remessa_*_cnab{400,240}.rem` e verificação parametrizada
  em `tests/test_cnab_remessa.py` (19 arquivos).
- **Divergências de comprimento arbitradas**: onde o layout de referência emite registros fora de 400/240
  (detalhe 401 do Banco do Nordeste, 402 do CrediSIS, formato DCB do BRB e segmento P de 241 do
  Santander 240), a PyCobrança mantém a **paridade byte a byte** e anota o desvio no código
  (`tamanho_registro=None`), documentando-o em `docs/bancos/`.
- **`docs/bancos/fontes-oficiais.md`**: consolidação das URLs de manuais oficiais por banco;
  seções de "Remessa CNAB 400/240" adicionadas aos documentos por banco.

### Boleto para todos os bancos (18)
- **13 bancos adicionais portados**: Banco do Nordeste (004), Banestes
  (021), Banrisul (041), BRB (070), Ailos (085), CrediSIS (097), Unicred (136), C6 (336),
  HSBC-CNR/CSB (399), Safra (422), Citibank (745), Sicredi (748) e Sicoob (756) — cada um com
  seu campo livre e regras de DV específicas (dígito duplo, fatores fixos 3-1-9-7, base 7 com
  "P", data juliana etc.).
- Utilitários portados para o núcleo: `modulo11_flex` (módulo 11 com fatores/mapa configuráveis,
  com fatores/direção/bloco/mapa) e `duplo_digito` (verificado contra o Ruby).
- **Validação cruzada 18/18**: mesmos dados nos dois sistemas geram código de barras e linha
  digitável idênticos em todos os bancos; divergência do Ailos detectada e corrigida conforme o
  manual da cooperativa (conta 7+DV, nosso número 9). Fixtures congeladas.

### Validação cruzada com vetores de referência
- **Mesmos dados gerados em duas implementações** (uma de referência em Ruby 3.3, executada da
  fonte): **código de barras e linha digitável idênticos em 5/5 bancos P1**; vetores congelados
  como fixtures permanentes em `tests/test_validacao_cruzada.py`.
- Divergências arbitradas pela **documentação oficial dos bancos**: Caixa corrigida para exibir
  o nosso número com DV (17 posições + DV, manual SIGCB — o vetor de referência estava correto);
  Santander mantido com 13 posições (12+DV, layout oficial — divergência cosmética
  documentada).
- **`docs/bancos/`** criado: um documento por banco
  P1 com layout do campo livre posição a posição, DVs, carteiras, referência ao manual oficial
  e exemplo validado; pasta destinada a armazenar os PDFs oficiais.

### Decisões de escopo
- **SDK HTTP**: movido para **projeto separado** (doc 04 vira especificação).
- **Sem retrocompatibilidade** (camada `compat` removida do plano; ADR-6).
- **Renderização exclusivamente via ReportLab**: templates Jinja2/WeasyPrint removidos do pacote
  (a análise comparativa permanece no doc 11 como histórico).

### Adicionado (Fase 0 — Fundação)
- Documentação de arquitetura e plano de modernização em `docs/` (visão geral, arquitetura,
  roadmap, mapa de recursos, integração via API REST, bancos, CNAB, PIX,
  testes/qualidade, CI/CD, guia de contribuição, renderização e processamento em lote).
- Estratégia de renderização com **tabela de decisão** de backends de PDF (ReportLab padrão,
  WeasyPrint/Playwright opcionais) e contrato de backend plugável (`docs/11-renderizacao.md`).
- Contrato de **processamento assíncrono em lote** (jobs, idempotência, estados, sublotes CNAB
  determinísticos) e divisão de responsabilidades engine × comunicação (`docs/12-processamento-lote.md`).
- Tabela de riscos e mitigação; convenção de nomenclatura pt-BR canônica dos módulos.
- Versão do `ruff` fixada (`==0.16.0`) para alinhar formatação local e CI (o `ruff` 0.16 formata
  blocos de código Python embutidos no Markdown).
- **Decisão de renderização:** `WeasyPrintBackend` (HTML/CSS + Jinja2) como padrão, priorizando
  experiência visual e manutenção; `ReportLab` como alternativa de alto volume/serverless.
- Exemplo visual de boleto em HTML/CSS no **modelo moderno** (Recibo do Sacado + Ficha de
  Compensação), com código de barras Interleaved 2 of 5 real e **QR Code PIX (Bolepix)** —
  `docs/exemplos/boleto-demo.html`.
- **Templates Jinja2 reais** do boleto em `pycobranca/render/templates/` no **layout clássico** (Recibo do Sacado, 5 caixas laterais com Valor cobrado, Código de baixa,
  barcode 103×13mm) com melhorias (Bolepix, temas), fonte única de estilos/partes
  (`_componentes.html.j2`) e três variantes:
  `boleto.html.j2` (com recibo + Bolepix), `boleto_sem_recibo.html.j2` (só ficha) e
  `carne.html.j2` (carnê, 3 parcelas por A4). O módulo `pycobranca.render` expõe
  `render_boleto_html/_pdf`, `render_boleto_sem_recibo_html/_pdf` e `render_carne_html/_pdf`,
  além do gerador de código de barras Interleaved 2 of 5 em Python puro (`interleaved_2of5_svg`).
  Testes de renderização (Jinja2, sem WeasyPrint) na CI.
- Empacotamento do subpacote `pycobranca.render` e inclusão dos templates como package-data;
  extras `render` (WeasyPrint + Jinja2) e `render-reportlab` (alternativa).
- **Backend ReportLab implementado** (`pycobranca/render/reportlab.py`): mesmo layout clássico do
  clássico e mesmo contrato de contexto, desenhado em Python puro — código de barras nativo a
  partir dos 44 dígitos (`sequencia_i2of5`) e QR do Bolepix por matriz de módulos
  (`pix.qrcode_matrix`). Testado na CI (`render_boleto_pdf`).
- Parâmetro `modelo` no backend ReportLab: `"classico"` (padrão) ou `"moderno"` — este último
  **validado visualmente contra imagens de referência**
  (`docs/images/boletos/boleto_pix_prawn.png`): Recibo do Pagador com chips, célula PIX central
  no bloco de instruções (57%|18%|25%) com cabeçalho teal, paleta cinza, totalizadores
  horizontais no recibo, "Corte aqui" e código de barras 68%×48pt.
- **Carnê ReportLab** (`render_carne_pdf`) validado contra `carne_prawn.png`: 3 parcelas
  por A4, canhoto aberto à esquerda, ficha compacta com coluna direita fixa, célula PIX teal e
  código de barras de 32pt; quebra de página automática a cada 3 parcelas.
- **Suporte a TEMA** no modelo `moderno`, validado contra
  `boleto_tema.png`: faixa de marca no topo (logo em caixa branca + empresa + badge de parcela),
  marca d'água diagonal em tinta clara da cor do tema, rodapé de contatos e barra inferior
  full-bleed — via chave opcional `tema` no contexto (`habilitado`, `cor`, `logo_texto`,
  `empresa`, `parcela_texto`, `marca_dagua`, `rodape`).
- **Decisão de renderização revisada (ADR-2):** com a paridade visual comprovada contra as
  imagens de referência e o benchmark de lote (100 boletos: 1,2s vs 132s; 200: 2,1s vs 265s —
  ~120× mais rápido; PDFs 3× menores), o **ReportLab (`modelo="moderno"`) foi promovido a
  renderizador padrão**; WeasyPrint permanece como opt-in para white-label/prévia web.
- Esqueleto do pacote `pycobranca` com versionamento e registro inicial de bancos.
- Empacotamento moderno via `pyproject.toml` (PEP 517).
- Testes de fumaça (`tests/test_smoke.py`).
- Pipelines de CI (`ci.yml`) e homologação (`hml.yml`) na última versão estável do Python (3.14).
- Branch de homologação `hml` como foco dos testes.
- `.gitignore`, `CHANGELOG.md` e guia de contribuição.
