# Caixa Econômica Federal (104)

Documento de referência para conferir a implementação do Caixa Econômica Federal no PyCobrança, cobrindo boleto, CNAB e validações complementares por banco.

> Escopo inicial: mapear regras vigentes do banco, criar fixtures de boleto e CNAB, validar renderização pelo `ReportLabBackend` e registrar pendências de homologação em HML.

## Identificação

| Item | Valor |
| --- | --- |
| Banco | Caixa Econômica Federal |
| Código COMPE | `104` |
| Boleto | A confirmar no manual vigente |
| CNAB 240 | A confirmar no manual vigente |
| CNAB 400 | A confirmar no manual vigente |
| PIX/Bolepix | A confirmar no manual vigente e/ou API do banco |

## Fontes oficiais para preenchimento

- [Banco Central — Lista de Participantes do STR](https://dadosabertos.bcb.gov.br/dataset/lista-de-participantes-do-str)
- [CAIXA — CNAB 400 cobrança](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_400.pdf)
- [CAIXA — CNAB 240 cobrança](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_240.pdf)
- [CAIXA — Código de barras SIGCB](https://www.caixa.gov.br/Downloads/cobranca-caixa/ESP_COD_BARRAS_SIGCB_COBRANCA_CAIXA.pdf)

> As regras específicas deste arquivo devem ser preenchidas somente a partir dessas fontes oficiais, do manual vigente recebido no processo de homologação ou de evidência formal do banco.
## Campos obrigatórios do boleto

| Campo PyCobrança | Tipo | Tamanho | Obrigatório | Observação |
| --- | --- | ---: | :---: | --- |
| `agencia` | string | A confirmar | Sim | Agência conforme manual do banco. |
| `conta` | string | A confirmar | Sim | Conta do beneficiário conforme convênio. |
| `convenio` | string | A confirmar | Sim | Código do beneficiário/convênio/cedente fornecido pelo banco. |
| `carteira` | string | A confirmar | Sim | Carteiras suportadas devem ser catalogadas em fixtures. |
| `nosso_numero` | string | A confirmar | Sim | Regra e DV variam por banco/carteira. |
| `valor` | decimal | - | Sim | Valor nominal do boleto. |
| `data_vencimento` | date | - | Sim | Data de vencimento do título. |
| `cedente` | string | - | Sim | Nome do beneficiário. |
| `documento_cedente` | string | 11/14 | Sim | CPF/CNPJ do beneficiário. |
| `sacado` | string | - | Sim | Nome do pagador. |
| `sacado_documento` | string | 11/14 | Sim | CPF/CNPJ do pagador. |

## Carteiras e convênios

| Carteira | Nome operacional | Emissão | Nosso número | Situação |
| --- | --- | --- | --- | --- |
| A confirmar | A confirmar | Banco ou cliente | A confirmar | Pendente de manual/fixture |

## Campo livre do código de barras

| Posição no código de barras | Tamanho | Conteúdo | Situação |
| ---: | ---: | --- | --- |
| A confirmar | A confirmar | Composição específica do Caixa Econômica Federal. | Pendente de manual/fixture |

## Dígito verificador

| Item | Regra | Situação |
| --- | --- | --- |
| DV do nosso número | A confirmar por carteira. | Pendente |
| DV do código de barras | Módulo 11 padrão FEBRABAN, salvo exceções do banco. | Confirmar |
| DV da linha digitável | Conforme blocos da linha digitável. | Confirmar |

## CNAB

| Item | Regra |
| --- | --- |
| Layouts previstos | CNAB 240 e/ou CNAB 400, conforme manual vigente. |
| Header | Conferir campos de banco, empresa, convênio, sequencial e data de geração. |
| Detalhe | Conferir nosso número, carteira, valor, vencimento, documento e instruções. |
| Trailer | Conferir quantidade de registros, totais e sequenciais. |
| Agrupamento | Não misturar banco, layout, convênio, carteira, agência ou conta incompatível no mesmo arquivo. |
| Auditoria | Guardar arquivo gerado de forma imutável com hash e manifesto do job. |

## PIX/Bolepix

- Confirmar se o Caixa Econômica Federal suporta Bolepix por CNAB, API bancária ou ambos.
- Confirmar exigências de chave PIX, `txid`, QR Code, vencimento e valor.
- Não ativar PIX/Bolepix sem evidência de homologação do banco.

## Exemplo de boleto

```python
boleto = BoletoCaixaEconomica(
    agencia="0000",
    conta="0000000",
    convenio="000000000000",
    carteira="A_CONFIRMAR",
    nosso_numero="0000000000",
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
    layout="A_CONFIRMAR",
    convenio="000000000000",
    carteira="A_CONFIRMAR",
    sequencial_remessa="0000001",
    pagamentos=[pagamento],
)
```

## Checklist de conferência do boleto

- [ ] Confirmar manual e versão usados como referência.
- [ ] Validar campos obrigatórios por carteira/convênio.
- [ ] Validar composição do campo livre.
- [ ] Validar fator de vencimento e valor no código de barras.
- [ ] Validar DV geral do código de barras.
- [ ] Validar linha digitável contra o código de barras.
- [ ] Validar DV do nosso número.
- [ ] Validar PDF gerado pelo `ReportLabBackend` em A4.
- [ ] Validar leitura de código de barras e QR Code após renderização.

## Checklist de conferência do CNAB

- [ ] Validar header de arquivo/lote.
- [ ] Validar registros detalhe obrigatórios.
- [ ] Validar posições de nosso número, carteira, agência, conta e convênio.
- [ ] Validar instruções, ocorrências e códigos de movimento.
- [ ] Validar trailer, totais e quantidade de registros.
- [ ] Validar retorno CNAB com arquivo de homologação.
- [ ] Validar hash e manifesto do artefato gerado.

## Pendências para homologação

- [ ] Conferir manual vigente do Caixa Econômica Federal e versionar a referência usada.
- [ ] Criar fixture mínima de boleto válido.
- [ ] Criar fixture de remessa CNAB válida.
- [ ] Criar fixture de retorno CNAB.
- [ ] Catalogar carteiras suportadas.
- [ ] Catalogar variações por convênio/agência/conta.
- [ ] Confirmar suporte real a PIX/Bolepix no fluxo escolhido.
