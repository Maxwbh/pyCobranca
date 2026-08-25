# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

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

### Corrigido

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
