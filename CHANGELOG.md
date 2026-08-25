# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Adicionado

- **Retorno CNAB 400 do Sicoob (756)**, conforme a aba *04.Retorno* do
  `Layout_Cobranca_CNAB400.xls` publicado no portal do banco (19/05/2025). O nosso número ocupa
  **63–73 mais o DV em 74**; o layout de reserva lia oito posições e cortava três dígitos e o
  dígito verificador. A data de crédito fica em **176–181**, não em 296–301 — o reserva devolvia
  zeros, indistinguível de "ainda não creditado".
- **Retorno CNAB 400 do Sicredi (748)**, conforme a seção 9.2 do *Manual CNAB 400* v2.4. O nosso
  número fica em **48–62, quinze posições**; o layout de reserva lia 63–70, que ali é *filler*, e
  devolvia `00000000` — zeros com aparência de número válido. Medido sobre o **arquivo de retorno
  real** que já estava em `fixtures/retorno/externos`.
- **Varredura de valores-limite por banco** (`tests/test_limites_campos.py`), nos dois artefatos:
  boleto e remessa CNAB. Para cada campo de cada banco — sem dados, 1 caractere, o máximo
  declarado e máximo+1 —, e para agência, conta e nosso número em todos os tamanhos de 0 a 20
  dígitos. O contrato que ela prende: **ou o valor é recusado com um erro do pacote, ou o
  artefato sai no tamanho certo**; nunca calado e errado. Foi ela que encontrou os sete campos
  sem limite e os quatro `tamanho_registro = None`.
- **Aviso `LayoutGenerico`** quando o retorno é lido sem layout próprio do banco. O parser
  continua lendo o arquivo — o que muda é que agora **diz** que os campos podem estar em outras
  posições. Filtrável como qualquer aviso; `warnings.simplefilter("error", LayoutGenerico)` faz
  falhar em vez de seguir adiante.

- **`RemessaSafra400` e retorno 400 do Safra** — conforme o *Leiaute de Arquivos, Cobrança CNAB
  400* do banco. O boleto já existia; faltavam os arquivos. Trailer com quantidade e valor
  somado (369–391), multa gravada **dentro do campo de abatimento** em formato próprio (nota
  6.1.8) — os dois não cabem no mesmo título — e banco cobrador `422`, `341` ou `237`, para o
  arranjo de correspondente.
- **Layout de retorno `422`.** O nosso número do Safra ocupa 63–71, nove posições; o layout de
  reserva lê oito e cortava o **DV** em silêncio. Os códigos de ocorrência também divergem: o
  `40` é *baixa de título protestado*, não *baixa por ter sido liquidado* — sentidos opostos
  numa conciliação.

### Corrigido

- **Revisão dos 19 bancos.** Passou a existir uma varredura que gera boleto para **toda carteira
  declarada de todo banco** e roda o verificador FEBRABAN independente — 55 carteiras válidas, e
  uma que nunca funcionou: a **`CSB` do HSBC**, cujo campo livre monta 27 posições onde cabem 25.
  Antes só uma carteira por banco era exercitada. **A CSB saiu de `carteiras`** — corrigi-la
  precisa do manual do HSBC, que o banco não publica mais, e anunciá-la como suportada era
  promessa que sempre falhava. A composição segue em `campo_livre()` para quem tiver o manual.
- **Quatro remessas produziam registro fora do comprimento do formato** — 401 e 402 posições no
  CNAB 400 (Banco de Brasília, Banco do Nordeste, CrediSIS) e 241 no 240 (Santander). Causa única
  nas quatro: `str.rjust` **preenche mas nunca corta**, então um valor maior que o campo
  atravessava para a posição seguinte e deslocava todo o resto do registro — o CNAB é posicional.
  As fixtures não pegavam: vêm da implementação de referência, que estoura igual. Entra
  `campo_numerico`, que descarta zeros à esquerda sobrando e **recusa** dígito significativo que
  não cabe; truncar um nosso número produziria um título com outro número. As quatro fixtures
  foram regeradas e deixaram de ser vetor de paridade.
- **A remessa não aplicava os limites de campo que o boleto já declarava.** Banco do Nordeste
  (7 posições), CrediSIS (6) e BRB (6) aceitavam nosso número de oito dígitos — o mesmo que
  `regras_campos` recusa no boleto — e o gravavam estourando o registro. Agora é erro, com a
  mensagem dizendo quantos dígitos não couberam.
- **Atributos aceitos e nunca gravados**, removidos: `posto` no `RemessaSicoob240` e
  `modalidade_carteira`, `parcela`, `posto` e `byte_idt` no `RemessaSicredi240` (herdados pela
  Unicred). Mesma classe do `tipo_formulario`. Um teste passa a exigir, de **todas** as remessas,
  que nenhum campo declarado fique sem ser lido.
- **Sicoob: "seu número" (111–120) era gravado com zeros à esquerda.** O layout oficial declara
  o campo `X(10)`, alfanumérico — `DOC0001` virava `000DOC0001`, e é isso que o banco devolve no
  retorno: quem guardou `DOC0001` não reencontrava o título ao conciliar. Valor só de dígitos
  continua com zeros, onde as duas convenções coincidem. A fixture da remessa **deixou de ser
  vetor de paridade** (a referência preenchia com zeros); a diferença é só naquelas dez posições.
- **Sicoob: `tipo_formulario` era aceito na remessa 400 e nunca gravado.** O layout 400 não tem
  esse campo — é do 240, onde segue em uso. Removido do `RemessaSicoob400`: aceitar um parâmetro
  inerte é pior que recusá-lo. `modalidade_carteira` também ganhou documentação — ela grava a
  posição 106, *Tipo de Emissão*, não *Carteira/Modalidade*, que é de `carteira`.
- **Boleto do Safra sustentado só por vetor cruzado.** Passa a ser conferido contra o manual: o
  DV do nosso número bate com os **três exemplos resolvidos** da seção 7.1, incluindo o de resto
  zero; o campo livre bate posição a posição com a seção 7.2.2; e a linha digitável, que o manual
  documenta em **tabela própria** (7.2.3, com a agência partida entre as posições 6–9 e 11), bate
  com ela. Nenhuma mudança foi necessária na implementação — a verificação confirmou o que já
  havia.
- **`Retorno.ler` percorria arquivo que não é retorno CNAB.** A checagem do código do banco vinha
  **depois** do parsing, então uma entrada inválida era lida inteira antes de ser recusada — e
  ainda produzia um aviso apontando para um código que só existia porque a linha era lixo.
- **Sete campos entravam no campo livre sem limite declarado** e estouravam as 25 posições:
  `digito_conta` (Banco do Nordeste, Banestes, Unicred, Safra), `digito_agencia` (Safra),
  `variacao` (Sicoob), `byte_idt` (Sicredi) e a parcela do Sicoob (`quantidade`, 3 posições).
  `validar()` passava e o erro só aparecia na montagem do código de barras, sem dizer qual campo
  o causara. Agora estão em `regras_campos`, e a mensagem nomeia o campo.
- **Agência e conta estouravam o registro em quatro remessas** — Banco do Nordeste, CrediSIS,
  BRB e Santander 240 —, mesma causa do nosso número: `rjust` preenche e não corta. Passam por
  `campo_numerico`.
- **A conferência de comprimento do registro estava desligada nessas quatro remessas.** Cada uma
  justificava o `tamanho_registro = None` dizendo que *o layout do banco* usava 401, 402 ou 241
  posições. Nenhuma usava — era o `rjust` estourando o campo; o `None` transformou o sintoma em
  documentação e desligou o único aviso. As quatro voltam a conferir (o BRB com `(39, 400)`, pelo
  header DCB), e um teste exige que nenhuma remessa desligue a checagem.
- **Carteira desconhecida no Banco do Nordeste levantava `KeyError`**, de fora da hierarquia de
  erros do pacote: quem integra com `except PyCobrancaError` via o processo morrer. Vira
  `BoletoInvalido` dizendo quais combinações de carteira e emissão existem.
- **Revisão arquivo por arquivo da documentação**, que encontrou afirmações que o código já
  contradizia. A home dos docs anunciava **18 bancos** enquanto o README anunciava 19, e o mesmo
  número desatualizado aparecia em `04`, `16`, `20` e no roadmap — que ainda listava o **Inter
  (077) como fora de escopo**, depois de ele ter entrado. A matriz de remessa de `docs/bancos/`
  não tinha linha para Inter nem Safra; a de campos de `14` não tinha o Inter e oferecia a **CSB
  do HSBC**, retirada do código. Quatro páginas de banco descreviam registros de 401, 402 e 241
  posições como *quirk do layout do banco* — o diagnóstico que esta versão corrigiu —, e
  `15-novo-banco.md` **ensinava** `tamanho_registro = None`, hoje recusado por teste. Corrigidos
  também os totais de layout de retorno (16 dos 19, 14 em 400), de classes de remessa (28) e de
  logos empacotados (19).
- **Quatro testes novos prendem o que era mantido à mão:** todo banco do registro tem página; a
  contagem de bancos no texto bate com o registro; carteira retirada não é oferecida na
  documentação; e a tabela *Validação de campos* de cada banco lista **todo** campo com regra
  declarada — foi a ausência desses campos de uma posição que escondeu o defeito do campo livre.
- **Mensagens de erro nomeavam o atributo cru** em cinco campos: `digito_conta`, `digito_agencia`,
  `variacao`, `byte_idt` e a parcela do Sicoob saíam sem rótulo amigável. Agora saem como
  *"dígito da conta deve ter no máximo 1 dígitos"*, como os demais campos.
- **README anunciava os 18 logos como "alta resolução com transparência"**, e cinco são 150×40
  (quatro deles sem canal alfa). Não é defeito visível — o cabeçalho é branco e a faixa de marca
  não carrega o logo do banco —, mas pixelam na impressão. A frase passa a dizer quais, e um teste
  prende a lista ao que está em disco.

## [1.1.1] - 2026-08-24

### Adicionado

- **Banco Inter (077)** — 19º banco: boleto, remessa e retorno CNAB 400, e logo empacotado.
  Conforme o *Manual CNAB400* do banco (v2.2). **Só a carteira 110**: na 112 quem numera é o
  Inter, e o nosso número só existe no retorno — a 112 é recusada em `validar()`.
- **`RemessaInter400`** — remessa aprovada no **validador de layout do próprio Inter**.
  `nome_arquivo()` devolve `CI400_001_<sequencial>.REM`, que o manual exige igual ao header.
  Multa, juros e desconto em valor ou percentual; sem IOF e sem abatimento no layout.
  Não há CNAB 240 de cobrança no Inter — o que o banco publica em 240 é de *pagamentos*.
- **Retorno do Inter** — layout `077`: ocorrência em 90–91 e vencimento em 119–124, longe do
  comum. Sem ele o parser lia o "seu número" como código de ocorrência, sem aviso.
  `descreve_ocorrencia` passa a aceitar o banco: o `07` do Inter é *Cancelado*, não
  *Liquidação parcial*.
- **`Pagamento`**: `valor_multa`, `percentual_desconto` e `mensagem` — opcionais, exigidos pelo
  layout do Inter e ignorados pelos demais.
- **`tools/demo_gif.py`** — gera o GIF do README com os valores calculados pelo pacote. O
  anterior não tinha gerador e anunciava a versão 1.0.0.
- **`pix_copia_cola`** — payload EMV devolvido pelo banco ao registrar a cobrança. É o Bolepix de
  verdade: QR dinâmico, vinculado ao título, com baixa automática. Vai para o QR como veio, tem
  precedência sobre `pix_chave` e funciona em qualquer banco.
- **O QR avulso passa a sair identificado.** Sem `pix_txid`, o campo 62-05 recebe o nosso número —
  antes ia `***` e o crédito chegava órfão na conciliação por OFX. Sem nosso número o txid sai
  ausente, não derivado: zeros produziriam um identificador plausível e sem significado.
- **`pix_observacao`** — texto livre no campo 26-02 do BR Code (até 40), para descrever a cobrança
  a quem paga.
- **`openapi_de(paths, *, info, servers, schemas)`** — monta um documento OpenAPI com os paths de
  quem consome e os schemas daqui, sem cópia. A versão fica carimbada em `info["x-pycobranca"]` e
  colisão de nome levanta `ErroDeContrato`. `pix_copia_cola` e `pix_observacao` entram no
  `BoletoData`, e a resposta traz `pix_vinculado`.

### Corrigido

- **O QR do PIX montado da chave não liquida o boleto, e a documentação o chamava de Bolepix.**
  O payload de `pix_chave` é **estático**: paga a chave, mas o banco não sabe que aquele PIX quita
  este título — que fica em aberto, com risco de segunda cobrança ou protesto de título já pago.
  O Bolepix exige QR **dinâmico**, gerado pelo banco no registro. O comportamento antigo continua,
  agora nomeado pelo que é, e `contexto_render()["pix"]["vinculado"]` e
  `BoletoEmitido.pix_vinculado` dizem qual dos dois está no boleto.
- **Imagem do README invisível fora da `main`.** As referências ao repositório estavam fixadas em
  `.../main/...`, então uma captura nova só aparecia depois de promovida. O README passa a usar
  caminho relativo, e a conversão para URL absoluta — que o PyPI exige — acontece no
  empacotamento (`tools/_readme_urls.py`).
- **Matriz de bancos do README errada em três linhas**: dizia que Banco do Brasil e C6 não têm
  parser de retorno próprio (têm) e que o HSBC tem (não tem). Passou a ser derivada do código.
- **DAC do nosso número errado na carteira 112 do Itaú.** A composição longa era aplicada às sete
  carteiras aceitas, produzindo um código de barras estruturalmente válido com o dígito errado —
  passa em validador estrutural e só é detectado nas regras do Itaú. As demais não mudam.
  [#40](https://github.com/Maxwbh/pyCobranca/issues/40)
- **Paridade do Itaú presa por vetor**: as sete carteiras passam a ser conferidas byte a byte.
  O manual se contradiz sobre as escriturais; a decisão saiu da comparação com três outras
  implementações.
- **A faixa de encargos do boleto era impressa, e o total, calculado.** Desconto, deduções,
  mora/multa, acréscimos e valor cobrado são preenchidos **pelo caixa** no ato do pagamento. A
  1.1.0 imprimia o que o emissor informasse e somava o total, levando o pagador a pagar errado.
  As molduras continuam; o conteúdo não sai mais. `contexto_render()["totalizadores"]` e
  `BoletoEmitido.totalizadores` passam a vir sempre vazios.

## [1.1.0] - 2026-08-23

### Alterado

- **Boleto moderno redesenhado**: chips de Vencimento/Valor/Nosso Número com mais contraste,
  faixa de marca de 12 mm (logo-texto, empresa, parcela e rodapé), grade de 6 colunas alinhada
  ao eixo de Vencimento/Valor e linha de corte contínua. `modelo="moderno"` passa a renderizar
  este layout; o anterior sai.

### Adicionado

- **`boleto_de_api(payload)`** — caminho de volta do contrato REST: recebe `{"bank", "data"}`,
  valida, traduz os nomes divergentes, converte datas ISO e devolve o título. Com
  `tema_de_api(data)` para a faixa de marca, que o renderizador nomeia de outro jeito.
  A ida e volta `boleto_para_api` → `boleto_de_api` é testada nos 18 bancos.
- **`emite_boleto(boleto, modelo, tema=None)`** — PDF e dados numa chamada, montando o título uma
  vez só. Devolve `BoletoEmitido` com `.pdf`, `.linha_digitavel`, `.codigo_barras`,
  `.nosso_numero`, `.vencimento`, `.valor_documento`, `.pix_copia_cola`, `.totalizadores` e
  `.to_dict()`.
- **Campos específicos de banco no `BoletoData`**: `data_documento`, `digito_conta`,
  `digito_agencia`, `digito_convenio`, `variacao`, `incremento`, `portfolio`, `posto` e `byte_idt`
  (tupla `CAMPOS_POR_BANCO`). Sem eles o contrato não expressava 7 dos 18 bancos.
- **`NOTICE`** creditando pyboleto (BSD) e BrCobrança (MIT). Distribuído no wheel e no sdist via
  `license-files`; a `LICENSE` segue intacta.
- **Totalizadores do boleto**: `desconto_abatimento`, `outras_deducoes`, `mora_multa`,
  `outros_acrescimos` e `valor_cobrado`. O total é somado a partir dos quatro primeiros quando não
  informado. Em branco por padrão. Expostos também no contrato REST (`BoletoData`, com os mesmos
  nomes) e na tupla `TOTALIZADORES` de `pycobranca.contracts`.

### Corrigido

- **Contrato REST não expressava 7 dos 18 bancos.** Faltavam os campos que entram no campo livre
  ou são obrigatórios por regra do banco. Banco do Nordeste, Banestes e Unicred levantavam
  (campo livre com 24 dígitos); BRB, Safra e Sicredi barravam na validação; e o **Citibank
  produzia um código de barras diferente, sem erro** — estruturalmente válido, com o `portfolio`
  zerado e o destino errado.
- **`boleto_de_api` nomeava um banco que o chamador não mandou.** Um `bank` não-textual (`[]`)
  saía como `'0[]'` na mensagem, porque o código já vinha normalizado com zeros à esquerda. O erro
  passa a mostrar o valor como veio.
- **`agencia` e `conta_corrente` eram obrigatórios no `BoletoData`.** O Santander identifica o
  cedente pelo convênio e a Caixa pelo código do beneficiário: exigi-los tornava esses dois
  inexprimíveis no contrato. A exigência por banco continua em `validar()`.
- **`Retorno.ler` só aceitava caminho.** Passa a aceitar `bytes` e objeto com `.read()`, como
  `Extrato.ler` já fazia — um upload não precisa mais de arquivo temporário. A anotação dos dois
  passa a dizer isso (`FonteDeArquivo`): o pacote distribui `py.typed`, e a anotação estreita
  fazia o verificador de tipos acusar erro num uso que funciona.
- **`except PyCobrancaError` não cobria a biblioteca**, ao contrário do que a documentação
  prometia. Duas exceções (`InvalidBarcodeError`, `ErroDeContrato`) herdavam só de `ValueError`, e
  **14 pontos do pacote levantavam `ValueError`/`KeyError`/`RuntimeError` crus** — inclusive
  `banco_info()`, que usava `KeyError` enquanto `Bancos.find()` já usava `BancoNaoRegistrado`.
  Todas passam a herdar de `PyCobrancaError` **e** do erro embutido correspondente, nessa ordem:
  quem tratava pelo tipo embutido continua funcionando. Novas: `DadosInvalidos` (composição do
  título), `ModeloInvalido` (catálogo de renderização) e `DependenciaAusente` (reportlab/qrcode).
- **Entrada malformada escapava da fronteira do contrato.** Campo desconhecido no `BoletoData`
  virava `TypeError` do construtor; data fora do ISO, `ValueError` de `fromisoformat` sem dizer
  qual campo; `bool` passava por `number` (é subclasse de `int` em Python) e estourava em
  `Decimal("True")`; e `bank`/`modelo` não-hasheáveis derrubavam o acesso ao registro. Todos viram
  `ErroDeContrato`/`ModeloInvalido` nomeando o campo.

- **Texto longo vazava para fora do boleto.** Razão social ou endereço extensos atravessavam a
  borda da célula e saíam da página, num PDF válido em bytes e errado no papel — sem exceção.
  Agora o texto é cortado no limite da célula, com reticências, como o CNAB já faz nos registros.
- **Primeiro dígito da linha digitável cortado no boleto clássico.** A régua do cabeçalho passava
  por cima dele e o `3` era lido como `B`. O corpo caiu de 9,5 para 9,0, que é o maior que cabe
  no vão.
- **Nome do banco por cima do código-DV no boleto moderno.** "Caixa Econômica Federal" media
  145 pt para um vão de 115 e atravessava a régua do cabeçalho. O nome agora encolhe até caber.
- **Encargo de sete dígitos por cima do rótulo na faixa de totalizadores.** As faixas ganharam
  altura para o valor ter linha própria: 6,5 → 9,0 mm no recibo moderno e 30 → 40 mm no bloco de
  instruções do clássico. O bloco do clássico passa a comportar 8 linhas de instrução, contra 6.
- **Valores monetários alinhados à esquerda no boleto moderno.** Valor do documento, vencimento,
  quantidade, agência/código e nosso número passam a alinhar à direita, como no clássico.
- **Instrução longa saía pela lateral da página no boleto clássico.** O texto do bloco de
  instruções era desenhado sem corte — uma linha de 60 caracteres media 708 pt numa folha de
  595 — e não havia limite de linhas: da nona em diante o texto caía abaixo da moldura. Passa a
  ser cortado na largura do bloco e limitado ao que a altura comporta, como o moderno já fazia.
- **Rótulo encostando no valor nas células de 7 mm.** Rótulo com `g`, `p` ou `ç` — "Espécie",
  "Agência/Código Beneficiário" — descia até a borda superior do valor. O rótulo subiu 0,3 mm,
  sem mexer na altura de nenhuma célula.
- **`contexto_render()` estourava com `ValueError` em campo monetário atribuído depois da
  construção.** O `__post_init__` converte o que chega pelo construtor, mas os campos são públicos
  e mutáveis: um `boleto.mora_multa = "12.00"` quebrava a formatação. Agora reconverte, como
  `valor_centavos` já fazia, e valor inválido levanta `DadosInvalidos`.

## [1.0.3] - 2026-08-01

### Adicionado

- **Type hints expostos ao consumidor** (PEP 561): o pacote passa a distribuir `pycobranca/py.typed`
  — mypy e pyright leem as anotações da biblioteca sem stubs. Classifier `Typing :: Typed`.
- **Exemplos executáveis** em [`examples/`](https://github.com/Maxwbh/pyCobranca/tree/main/examples):
  10 scripts curtos cobrindo boleto, Bolepix,
  remessa 400/240, retorno, OFX, carnê, fatura (3 níveis), contrato REST e tratamento de erros.
  A CI roda todos a cada push (`python examples/executa_todos.py`), instalando o pacote **sem** as
  dependências de desenvolvimento — documentação que não envelhece e teste de fumaça do wheel.
- **Documentação publicada** em <https://maxwbh.github.io/pyCobranca/> (MkDocs Material, com busca
  e navegação), gerada do próprio `docs/` a cada push na `main`. Os documentos continuam legíveis
  no GitHub: o hook `mkdocs_hooks.py` reescreve os links relativos no site. Extra opcional
  `pip install "pycobranca[docs]"`.

### Alterado

- **`Development Status` de `2 - Pre-Alpha` para `5 - Production/Stable`** — o estágio anterior não
  refletia 18 bancos, remessa validada byte a byte e a suíte de testes atual.

## [1.0.2] - 2026-07-30

### Alterado

- **`requires-python` de `>=3.14` para `>=3.12`.** A 1.0.1 foi publicada antes desta mudança e só
  instalava em 3.14; a 1.0.2 corrige isso. O código não usa nenhum recurso acima de 3.10, e o piso
  3.12 acompanha o alvo de migração recomendado (suporte até out/2028). A CI roda a suíte em
  **matriz (3.12, 3.13 e 3.14)**, com lint/formatação em job próprio.

## [1.0.1] - 2026-07-30

### Adicionado

- **CNPJ alfanumérico** (IN RFB 2.229/2024; primeiras emissões a partir de **31/07/2026**):
  `validar_cnpj` aceita as 12
  primeiras posições com letras `A`–`Z` (DVs seguem numéricos, calculados com `ord(c) - 48`), e
  `formatar_cnpj` preserva as letras. Novos helpers `so_alfanumerico`, `cnpj_e_alfanumerico`,
  `dv_cnpj` e `formatar_documento`. O CPF continua exclusivamente numérico. No contrato REST, os
  campos de documento ganharam `pattern` (e o validador passou a suportá-lo), permitindo que um
  serviço HTTP rejeite formato inválido antes de chamar a engine.

- **Validação de campos por banco** (tamanho mín./máx. e conjunto de carteiras) na geração do boleto
  e **coerência de encargos** (mora/multa/desconto, `valor > 0`, UF/CEP) na remessa CNAB.
- **Validação de leitura**: `Extrato.ler` (OFX) levanta `OFXInvalido` para arquivo que não é OFX;
  `Retorno.ler` (CNAB) levanta `RetornoInvalido` para arquivo vazio/sem header — em vez de devolver
  resultado vazio silencioso.
- **Contrato de erros estruturado**: `BoletoInvalido` passa a carregar `.erros` (lista, um item por
  problema) além da mensagem única — pronto para uma camada REST tratar cada violação. Ver
  [`docs/14-validacao-campos.md`](docs/14-validacao-campos.md).
- **Docs por banco padronizados** num template único (18 bancos; inclui Banestes, HSBC e Safra) com
  seção de validação por banco. Novos guias: criação de banco (`docs/15-novo-banco.md`) e
  arquitetura/diretórios (`docs/16-arquitetura-diretorios.md`).
- **Fatura** (`render_fatura_pdf`): corpo livre + boleto na mesma página, em 3 níveis — `itens`
  (tabela pronta), `fatura.blocos` (corpo declarativo: tabela, campos, texto, total, separador,
  espaço) e `fatura.desenhar` (callable com liberdade total). Serve a várias modalidades sem
  engine de HTML; os níveis 1 e 2 entram no contrato REST existente (`ItemFatura`, `FaturaCorpo`,
  `BlocoFatura` em `BoletoData`).

### Corrigido

- **Empacotamento**: `license` migrado para expressão SPDX (PEP 639) com `license-files`,
  eliminando o aviso de depreciação do setuptools; o classifier de licença saiu (agora o
  metadado é `License-Expression`). Exige `setuptools>=77` no build. O diretório de logos
  passou a ser declarado em `packages`, removendo o aviso de pacote ausente — os arquivos
  já eram distribuídos e seguem no wheel.

- **Tipo de inscrição na remessa CNAB com CNPJ alfanumérico**: as letras eram descartadas e o
  documento acabava marcado como **CPF** (`01`) e truncado nos registros. Agora o documento é
  gravado íntegro e o tipo (`01`/`02`) sai correto.

### Alterado

- **`pycobranca.render` reorganizado**: o módulo único de 1183 linhas virou `comum` (primitivas),
  `tela` (canvas + cursor), `dados` (preenchimento), `blocos` (comuns) e `modelos/` — o catálogo dos
  documentos (boleto clássico, boleto moderno, carnê, fatura). Saída dos PDFs inalterada; a API
  pública mantém os mesmos nomes e ganha `render_fatura_pdf` e `desenha_boleto`.

## [1.0.0] - 2026-07-24

Primeira versão pública — cobrança bancária brasileira em Python 3.14+ puro, com **18 bancos** e um único `pip install`.

### Recursos

- **Boleto**: código de barras e linha digitável dos 18 bancos, em Python puro.
- **PDF (ReportLab)**: layouts `moderno`/`classico`, carnê e logo opt-in por banco.
- **PIX/Bolepix**: BR Code EMV + CRC16 e QR, no boleto e na remessa.
- **CNAB**: remessa 400 (12 bancos) e 240 (7 bancos); retorno 400/240.
- **Encargos na remessa**: juros/mora (valor/dia ou taxa mensal), multa e desconto 1º/2º/3º, IOF e abatimento.
- **OFX** (`pycobranca.ofx`): leitura de extrato (v1/v2) e conciliação com os boletos emitidos.
- **Contrato REST** (OpenAPI 3.0): serializadores e validador leve, sem dependência HTTP.
