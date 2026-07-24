# Caixa Econômica Federal (104)

Documento de referência para conferir a implementação da Caixa Econômica Federal no PyCobrança, cobrindo boleto SIGCB, CNAB 240, CNAB 400 e validações complementares.

> Escopo inicial: boleto de cobrança CAIXA/SIGCB, CNAB 240, CNAB 400, composição do código de barras, campo livre, linha digitável, validação de PDF pelo `ReportLabBackend` e homologação técnica pela CAIXA.

## Identificação

| Item | Valor |
| --- | --- |
| Banco | Caixa Econômica Federal |
| Código COMPE | `104` |
| Boleto | Sim — Cobrança Bancária CAIXA/SIGCB |
| CNAB 240 | Sim — Manual de Leiaute de Arquivo Eletrônico CNAB 240 |
| CNAB 400 | Sim — Manual de Leiaute de Arquivo Eletrônico CNAB 400 |
| PIX/Bolepix | Sim para cobrança híbrida, a validar conforme canal/API/contrato de homologação CAIXA |

## Fontes oficiais para preenchimento

- [Banco Central — Lista de Participantes do STR](https://dadosabertos.bcb.gov.br/dataset/lista-de-participantes-do-str)
- [CAIXA — CNAB 400 cobrança](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_400.pdf)
- [CAIXA — CNAB 240 cobrança](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_240.pdf)
- [CAIXA — Código de barras SIGCB](https://www.caixa.gov.br/Downloads/cobranca-caixa/ESP_COD_BARRAS_SIGCB_COBRANCA_CAIXA.pdf)
- [CAIXA — Webservice XML Cobrança Bancária](https://www.caixa.gov.br/Downloads/cobranca-caixa/WEBSERVICE-XML-COBRANCA-BANCARIA.pdf)

> As regras específicas deste arquivo devem ser preenchidas somente a partir dessas fontes oficiais, do manual vigente recebido no processo de homologação ou de evidência formal da CAIXA. Consulta realizada em 2026-07-24.

## Campos obrigatórios do boleto

| Campo PyCobrança | Tipo | Tamanho | Obrigatório | Observação |
| --- | --- | ---: | :---: | --- |
| `codigo_banco` | string | 3 | Sim | `104`. |
| `moeda` | string | 1 | Sim | `9` para Real. |
| `codigo_beneficiario` | string | 6 ou 7 | Sim | Código fornecido pela agência CAIXA; quando estiver nas faixas de 6 dígitos, compõe o campo livre com DV. |
| `codigo_beneficiario_dv` | string | 1 | Condicional | Calculado por módulo 11 quando o código do beneficiário exigir DV. |
| `agencia` | string | A confirmar | Sim | Agência de relacionamento do beneficiário. |
| `carteira` | string | 2 | Sim | Primeiras posições do nosso número SIGCB; exemplo registrado com emissão pelo beneficiário usa `14`. |
| `nosso_numero` | string | 17 | Sim | Nosso número SIGCB: 2 posições iniciais de carteira/entrega + 15 posições livres do beneficiário. |
| `valor` | decimal | 10 no código de barras | Sim | Valor nominal em centavos, sem separador, no código de barras. |
| `data_vencimento` | date | 4 no fator | Sim | Usada para fator de vencimento, exceto cenários específicos previstos no manual. |
| `cedente` | string | - | Sim | Nome do beneficiário. |
| `documento_cedente` | string | 11/14 | Sim | CPF/CNPJ do beneficiário. |
| `sacado` | string | - | Sim | Nome do pagador. |
| `sacado_documento` | string | 11/14 | Sim | CPF/CNPJ do pagador. |

## Carteiras e convênios

| Carteira | Nome operacional | Emissão | Nosso número | Situação |
| --- | --- | --- | --- | --- |
| `14` | Registrada com emissão pelo beneficiário | Beneficiário | 17 posições, sendo `1` como tipo de cobrança registrada e `4` como identificador de emissão pelo beneficiário | Confirmada para campo livre SIGCB nas fontes oficiais |
| A confirmar | Demais variações SIGCB/SICOB/SINCO | Banco ou beneficiário | Confirmar manual/contrato | Pendente de homologação específica |

## Código de barras

O código de barras da cobrança CAIXA possui 44 posições.

| Posição | Tamanho | Conteúdo |
| ---: | ---: | --- |
| 01-03 | 3 | Identificação do banco: `104`. |
| 04 | 1 | Código da moeda: `9`. |
| 05 | 1 | DV geral do código de barras. |
| 06-09 | 4 | Fator de vencimento. |
| 10-19 | 10 | Valor do documento. |
| 20-44 | 25 | Campo livre CAIXA/SIGCB. |

## Campo livre do código de barras

O campo livre contém 25 posições e deve ser gerado de forma determinística para testes de regressão.

| Posição no código de barras | Tamanho | Conteúdo | Observação |
| ---: | ---: | --- | --- |
| 20-25 | 6 | Código do beneficiário | Quando o código estiver na faixa de 6 posições. |
| 26 | 1 | DV do código do beneficiário | Calculado por módulo 11 quando aplicável. |
| 27-29 | 3 | Nosso número — sequência 1 | 3ª a 5ª posição do nosso número. |
| 30 | 1 | Constante 1 | 1ª posição do nosso número; tipo de cobrança. Para registrada: `1`. |
| 31-33 | 3 | Nosso número — sequência 2 | 6ª a 8ª posição do nosso número. |
| 34 | 1 | Constante 2 | 2ª posição do nosso número; emissão do boleto. Para beneficiário: `4`. |
| 35-43 | 9 | Nosso número — sequência 3 | 9ª a 17ª posição do nosso número. |
| 44 | 1 | DV do campo livre | Módulo 11; admite `0`. |

## Dígitos verificadores

| Item | Regra | Situação |
| --- | --- | --- |
| DV geral do código de barras | Módulo 11 com pesos de 2 a 9; não admite `0`. | Confirmado nas especificações CAIXA SIGCB. |
| DV do código do beneficiário | Módulo 11 para códigos de beneficiário nas faixas indicadas no manual; admite `0`. | Confirmar faixa do beneficiário em homologação. |
| DV do campo livre | Módulo 11; resultado maior que 9 vira `0`; admite `0`. | Confirmado nas especificações CAIXA SIGCB. |
| DV do nosso número | Conforme anexo específico do manual de código de barras SIGCB. | Implementar fixture dedicada. |
| DV da linha digitável | Conforme os três blocos da representação numérica FEBRABAN/CAIXA. | Confirmado nas especificações CAIXA SIGCB. |

## CNAB

| Item | Regra |
| --- | --- |
| Layouts previstos | CNAB 240 e CNAB 400 para Cobrança Bancária CAIXA/SIGCB. |
| Código do beneficiário | Fornecido pela agência CAIXA e usado nos registros de remessa/retorno. |
| Nosso número | Quando a CAIXA for responsável pela emissão, campos de carteira/nosso número podem seguir regra de preenchimento com zeros conforme layout; quando emissão é do beneficiário, enviar conforme nosso número calculado. |
| Header | Conferir banco `104`, empresa, convênio/código do beneficiário, sequencial e data de geração. |
| Detalhe | Conferir nosso número, carteira, valor, vencimento, documento, instruções e ocorrências. |
| Trailer | Conferir quantidade de registros, totais e sequenciais. |
| Agrupamento | Não misturar banco, layout, convênio/código do beneficiário, carteira, agência ou conta incompatível no mesmo arquivo. |
| Auditoria | Guardar arquivo gerado de forma imutável com hash e manifesto do job. |

## PIX/Bolepix

- A CAIXA possui documentação oficial de Webservice XML de Cobrança Bancária com cobrança híbrida.
- Validar se o fluxo escolhido será CNAB, Webservice XML, API bancária ou integração da cobrança_api.
- Confirmar exigências de chave PIX, `txid`, QR Code, vencimento e valor no contrato de homologação.
- Não ativar PIX/Bolepix sem evidência de homologação da CAIXA para o canal utilizado.

## Exemplo de boleto

```python
boleto = BoletoCaixaEconomica(
    codigo_banco="104",
    moeda="9",
    agencia="0000",
    codigo_beneficiario="005507",
    codigo_beneficiario_dv="7",
    carteira="14",
    nosso_numero="14222333777777777",
    valor="100.00",
    data_vencimento="2026-08-22",
    cedente="Minha Empresa LTDA",
    documento_cedente="12345678000100",
    sacado="Cliente Teste",
    sacado_documento="12345678900",
)
```

## Exemplo de remessa CNAB

```python
remessa = RemessaCnabCaixaEconomica(
    banco="104",
    layout="240",  # ou "400", conforme contrato CAIXA
    codigo_beneficiario="005507",
    codigo_beneficiario_dv="7",
    carteira="14",
    sequencial_remessa="0000001",
    pagamentos=[pagamento],
)
```

## Checklist de conferência do boleto

- [ ] Confirmar manual CAIXA/SIGCB e versão usados como referência.
- [ ] Validar código do beneficiário e DV conforme faixa do contrato.
- [ ] Validar nosso número SIGCB com 17 posições.
- [ ] Validar composição do código de barras nas 44 posições.
- [ ] Validar campo livre nas posições 20-44.
- [ ] Validar fator de vencimento e valor no código de barras.
- [ ] Validar DV geral do código de barras.
- [ ] Validar DV do campo livre.
- [ ] Validar linha digitável contra o código de barras.
- [ ] Validar PDF gerado pelo `ReportLabBackend` em A4.
- [ ] Enviar amostras para homologação técnica da CAIXA antes de produção.
- [ ] Validar leitura de código de barras e QR Code após renderização.

## Checklist de conferência do CNAB

- [ ] Validar header de arquivo/lote para CNAB 240.
- [ ] Validar header de arquivo para CNAB 400.
- [ ] Validar código do beneficiário fornecido pela CAIXA.
- [ ] Validar registros detalhe obrigatórios.
- [ ] Validar posições de nosso número, carteira, agência, conta e convênio/código do beneficiário.
- [ ] Validar instruções, ocorrências e códigos de movimento.
- [ ] Validar trailer, totais e quantidade de registros.
- [ ] Validar retorno CNAB com arquivo de homologação.
- [ ] Validar hash e manifesto do artefato gerado.

## Pendências para homologação

- [ ] Registrar a versão exata dos manuais CAIXA usados no teste.
- [ ] Criar fixture mínima de boleto SIGCB registrado com emissão pelo beneficiário.
- [ ] Criar fixture de remessa CNAB 240 válida.
- [ ] Criar fixture de remessa CNAB 400 válida.
- [ ] Criar fixture de retorno CNAB.
- [ ] Criar teste para DV do código do beneficiário.
- [ ] Criar teste para DV do campo livre admitindo `0`.
- [ ] Criar teste para linha digitável a partir do código de barras.
- [ ] Confirmar suporte real a PIX/Bolepix no fluxo escolhido.
