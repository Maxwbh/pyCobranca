# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [1.0.1] - 2026-07-30

### Adicionado

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
