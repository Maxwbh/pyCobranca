# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue
[SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [1.0.0] - 2026-07-24

Primeira versão pública — cobrança bancária brasileira em Python 3.14+ puro
(boleto, CNAB 240/400 e PIX/Bolepix), com **18 bancos** e um único `pip install`.

### Recursos

- **Boleto** dos 18 bancos: código de barras (44 posições) e linha digitável gerados
  em Python puro, com o campo livre e as regras de DV de cada banco.
- **PDF via ReportLab**: layouts `moderno` (padrão) e `classico`, carnê e **logo opt-in**
  por banco. Acompanham logos empacotados de **17 dos 18 bancos** (falta o Citibank) —
  origem e licença por arquivo em `pycobranca/render/logos/NOTICE.md`.
- **PIX/Bolepix**: BR Code EMV + CRC16 e QR Code, integrados ao boleto e à remessa
  (registro tipo 8 no CNAB 400; segmento Y no CNAB 240).
- **CNAB remessa** 400 (12 bancos) e 240 (7 bancos) e **CNAB retorno** 400/240 com
  parser posicional.
- **Contrato de dados REST** (OpenAPI 3.0): serializadores de boleto, pagamento, remessa
  e retorno, com validador leve — a engine não tem dependência HTTP.
- **`pycobranca.BANCOS` / `banco_info()`** derivam do registro único
  (`pycobranca.bancos.REGISTRO`) e cobrem os 18 bancos.
- **Instalação única**: `reportlab` e `qrcode` já vêm como dependências.

### Correções

- **CNAB 240 com PIX**: a contagem de registros do trailer de arquivo passa a incluir os
  segmentos Y, batendo com o total físico exigido no intake bancário.
- **Retorno CNAB 400**: o trailer (tipo 9) deixa de entrar em `registros` como título fantasma.

### Qualidade

- Validação FEBRABAN **independente do núcleo** (round-trip linha↔código, DVs módulo 10/11)
  aplicada aos 18 bancos e a boletos/retornos reais de terceiros.
- CNAB de remessa e retorno conferido **byte a byte** contra vetores de referência e por
  verificador estrutural que relê os arquivos posição a posição.

### Notas de escopo

- **Renderização exclusivamente via ReportLab** (templates Jinja2/WeasyPrint removidos do
  pacote); ~120× mais rápida que o backend HTML/CSS de referência.
- **Bancos suportados**: os 18 cobrem o conjunto com vetor oficial reproduzível. Bancos que
  emitem o boleto no lado da instituição (ex.: Inter/077), sem campo livre reproduzível
  client-side, entram mediante manual oficial com exemplo numérico validável.
