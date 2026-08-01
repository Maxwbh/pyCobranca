# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Alterado

- **Créditos de origem corrigidos** no `NOTICE`, no README e na página de compatibilidade: a
  **pyboleto** (BSD, © 2011 Eduardo Cereto Carvalho e contribuidores) é a **inspiração original** do
  projeto e passa a vir primeiro; a **BrCobrança** é o **elo adicional**, que entrou depois para
  ampliar o escopo (CNAB, mais bancos e layouts), simplificar soluções e servir de referência de
  verificação. A ordem anterior invertia a genealogia.
- Fica registrado por que a pyboleto não serve como vetor de conferência: o último lançamento é de
  2016 e o pacote não instala em Python moderno (`error: invalid command 'dist_info'`).

### Adicionado

- **Página de compatibilidade e validação** ([`docs/17-compatibilidade.md`](docs/17-compatibilidade.md)):
  torna pública a evidência que já existia na suíte — paridade com a BrCobrança nos 18 bancos,
  verificador FEBRABAN independente do núcleo e as 26 fixtures de remessa comparadas byte a byte,
  com o passo a passo para reproduzir. Resumo no README.
- **Guia do CNPJ alfanumérico** ([`docs/18-cnpj-alfanumerico.md`](docs/18-cnpj-alfanumerico.md)):
  página dedicada com o que muda, o cálculo do DV (`ord(c) - 48`), **onde os sistemas quebram** (a
  limpeza que descarta letras e o tipo de inscrição que sai errado no CNAB) e um checklist de
  auditoria. O conteúdo estava disperso em validação de campos e contrato REST.
- **Meta `description` nas 18 páginas por banco**, gerada a partir dos dados reais do registro
  (carteiras aceitas, layouts CNAB, suporte a PIX) — é o texto que aparece no resultado de busca.
- **Posicionamento explícito como biblioteca embutível e neutra** (README e visão geral): roda no
  processo do consumidor (sem rede, estado ou daemon), não impõe framework, entrega o contrato REST
  como dado, e a licença BSD-3 permite embutir em produto comercial fechado. A biblioteca não
  divulga nem depende de nenhum produto construído sobre ela — a dependência é sempre
  `consumidor → biblioteca`.

- **Arquivo [`NOTICE`](NOTICE)** com reconhecimento à **BrCobrança** (MIT, © 2009 Kivanio Barbosa)
  e à **pyboleto** (BSD, © 2011 Eduardo Cereto Carvalho e contribuidores), em português e inglês.
  Registra que a fonte normativa são os manuais FEBRABAN, dos bancos e do Banco Central, e que a
  menção não implica endosso. A `LICENSE` segue intacta (BSD-3-Clause) — o crédito em arquivo
  separado preserva a detecção automática da licença; `license-files` passa a incluir os dois, então
  ambos viajam no wheel e no sdist. Resumo também no README.

### Corrigido

- **Documentação afirmava suporte a CNAB 444, que não existe.** `docs/06-cnab.md` dizia que a
  biblioteca "suporta os três layouts" e `docs/01-arquitetura.md` descrevia geração e parsing como
  "240/400/444" em quatro pontos — mas não há uma linha de 444 no código. Os textos passam a
  refletir os **dois layouts realmente implementados** (240 e 400), e o 444 fica marcado como
  pendente, com registro no [roadmap](docs/02-roadmap-modernizacao.md) explicando o que é (variante
  do Itaú: o 400 com 44 posições de mensagem) e o critério para entrar.
- **README com caminhos relativos quebrava na página do PyPI.** O README é a `long_description` do
  pacote, e o PyPI não resolve caminhos relativos: as **8 imagens** (banner, GIF de demonstração,
  diagrama de arquitetura e as 4 capturas de boleto) não apareciam e **25 links** apontavam para
  lugar nenhum. Agora imagens usam `raw.githubusercontent.com`, páginas de documentação apontam
  para o site publicado e arquivos do repositório para o `blob`/`tree` — funciona igual no GitHub,
  no PyPI e em qualquer lugar que renderize o README. Efeito visível na próxima versão publicada.
- **Visão geral afirmava Python 3.14 como alvo** — desatualizado desde a mudança do piso para 3.12
  na 1.0.2. Agora reflete o piso real e a matriz da CI.

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
