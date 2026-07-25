# Changelog

Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versionamento [SemVer](https://semver.org/lang/pt-BR/).

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
