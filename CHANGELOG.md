# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue
[SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado

- **Leitura de extrato OFX + conciliação** (`pycobranca.ofx`): parser em Python puro de OFX
  **v1 (SGML)** e **v2 (XML)** — `Extrato.ler()` estrutura banco, conta, período, saldo e
  transações, com normalização de encoding Latin‑1→UTF‑8. Extrai o **nosso número** do memo por
  banco (Sicoob, Itaú, BB, Bradesco, Caixa, genérico) e oferece `concilia()` para casar as
  transações do extrato com os boletos emitidos (fechando emissão → retorno CNAB → OFX).
  `to_dict()` devolve uma estrutura JSON-friendly (schemas `ExtratoOFX`/`TransacaoOFX`) pronta para
  consumo via REST — sem dependência de HTTP no pacote.
- **Encargos completos na remessa CNAB.** `Pagamento` ganhou `percentual_mora` (juros por **taxa
  mensal**, `tipo_mora="2"`, conforme FEBRABAN) e o **3º desconto** (`cod_terceiro_desconto`/
  `data_terceiro_desconto`/`valor_terceiro_desconto`). No **CNAB 240**, o segmento P passa a emitir
  juros **percentual** quando `tipo_mora="2"`, e o segmento R passa a preencher o **2º e o 3º
  desconto** a partir do `Pagamento` (antes eram zerados fixos).
- **Encargos na API/contrato REST.** O schema `Pagamento` ganhou o objeto `encargos`
  (`mora`/`multa`/`descontos`/`iof`/`abatimento`), com os schemas `Encargos`, `Mora`, `Multa` e
  `Desconto`; `pagamento_para_api` serializa os encargos quando presentes (payload inalterado quando
  não há encargo).
- **Testes de encargos** (`tests/test_cnab_encargos.py`): juros/multa/desconto com valores reais,
  conferidos **posição a posição** (240 P/R e Sicoob 400) e no contrato — cobertura que os vetores
  byte a byte (todos zerados) não exercitavam.
- **Validação por sistema independente** (`tests/test_cnab_encargos_externo.py`): um decodificador
  FEBRABAN lê a remessa por posições absolutas do padrão e **reconstrói** os encargos (round-trip
  encode→arquivo→decode), cruzado em três bancos 240 (BB, Caixa, Santander) e no Sicoob 400, mais o
  aceite pelo validador estrutural independente.
- Documentação de encargos em `docs/06-cnab.md` (matriz valor×percentual e datas por layout) e
  `docs/04-api-rest.md`.

### Corrigido

- **CNAB 240 — datas de multa/mora efetivas.** As datas passam a usar os campos
  `Pagamento.data_multa`/`data_mora` quando informados (antes eram sempre derivadas do vencimento);
  na ausência, mantêm o fallback do padrão (vencimento, ou vencimento+1 na Caixa/Sicredi/Unicred).
- **Clareza da multa.** `formata_valor_multa` agora é um alias explícito de `formata_percentual_multa`
  (no padrão FEBRABAN a multa é sempre percentual; não há valor monetário de multa). O Sicoob 400
  passou a usar `formata_percentual_multa` — saída byte a byte inalterada.

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
