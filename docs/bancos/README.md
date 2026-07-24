# Documentação por banco

Este diretório centraliza a documentação técnica por banco para conferir geração de boleto, PIX/Bolepix, remessa CNAB e retorno CNAB durante a modernização do PyCobrança.

## Padrão de documentação

Cada banco deve possuir um arquivo próprio contendo:

- Identificação do banco, código COMPE/ISPB quando aplicável e escopo homologado.
- Campos obrigatórios e opcionais para boleto.
- Regras de carteira, convênio, agência, conta, nosso número e dígitos verificadores.
- Composição do campo livre, linha digitável e código de barras.
- Layouts CNAB suportados, diferenças por carteira e campos críticos.
- Suporte PIX/Bolepix e restrições de homologação.
- Exemplos de entrada e checklist de conferência.


## Fontes oficiais

- [Fontes oficiais para documentação bancária](fontes-oficiais.md)

## Bancos documentados inicialmente

| Código | Banco | Documento | Escopo inicial |
| --- | --- | --- | --- |
| 001 | Banco do Brasil | [banco-do-brasil.md](banco-do-brasil.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 003 | Banco da Amazônia | [banco-da-amazonia.md](banco-da-amazonia.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 004 | Banco do Nordeste | [banco-do-nordeste.md](banco-do-nordeste.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 021 | Banestes | [banestes.md](banestes.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 033 | Santander | [santander.md](santander.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 041 | Banrisul | [banrisul.md](banrisul.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 077 | Banco Inter | [inter.md](inter.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 085 | Ailos | [ailos.md](ailos.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 104 | Caixa Econômica Federal | [caixa.md](caixa.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 208 | BTG Pactual | [btg-pactual.md](btg-pactual.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 237 | Bradesco | [bradesco.md](bradesco.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 336 | C6 Bank | [c6.md](c6.md) | Boleto, CNAB 400 e validações PIX/Bolepix. |
| 341 | Itaú | [itau.md](itau.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 389 | Banco Mercantil | [mercantil.md](mercantil.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 422 | Safra | [safra.md](safra.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 707 | Daycoval | [daycoval.md](daycoval.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 748 | Sicredi | [sicredi.md](sicredi.md) | Boleto, CNAB e PIX/Bolepix a conferir. |
| 756 | Sicoob | [sicoob.md](sicoob.md) | Boleto, CNAB e PIX/Bolepix a conferir. |

## Como usar na homologação

1. Preencher os exemplos com dados de homologação do banco.
2. Gerar boleto e CNAB pelo PyCobrança.
3. Conferir campo livre, linha digitável, código de barras e remessa contra o manual vigente do banco.
4. Registrar evidências no job ou ticket de HML.
5. Atualizar este diretório sempre que uma regra bancária for alterada.
