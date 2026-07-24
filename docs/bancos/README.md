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

## Bancos documentados inicialmente

| Código | Banco | Documento | Escopo inicial |
| --- | --- | --- | --- |
| 336 | C6 Bank | [c6.md](c6.md) | Boleto, CNAB 400 e validações PIX/Bolepix. |

## Como usar na homologação

1. Preencher os exemplos com dados de homologação do banco.
2. Gerar boleto e CNAB pelo PyCobrança.
3. Conferir campo livre, linha digitável, código de barras e remessa contra o manual vigente do banco.
4. Registrar evidências no job ou ticket de HML.
5. Atualizar este diretório sempre que uma regra bancária for alterada.
