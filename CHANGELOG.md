# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Alterado

- **Boleto moderno redesenhado**: chips de Vencimento/Valor/Nosso Número com mais contraste,
  faixa de marca de 12 mm (logo-texto, empresa, parcela e rodapé), grade de 6 colunas alinhada
  ao eixo de Vencimento/Valor e linha de corte contínua. `modelo="moderno"` passa a renderizar
  este layout; o anterior sai.

### Adicionado

- **`NOTICE`** creditando pyboleto (BSD) e BrCobrança (MIT). Distribuído no wheel e no sdist via
  `license-files`; a `LICENSE` segue intacta.
- **Totalizadores do boleto**: `desconto_abatimento`, `outras_deducoes`, `mora_multa`,
  `outros_acrescimos` e `valor_cobrado`. O total é somado a partir dos quatro primeiros quando não
  informado. Em branco por padrão.

### Corrigido

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
