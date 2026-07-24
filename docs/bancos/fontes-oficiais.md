# Fontes oficiais para documentação bancária

Este arquivo registra as fontes oficiais usadas para preencher e revisar os documentos em `docs/bancos/*.md`.

## Fonte regulatória comum

- [Banco Central do Brasil — Lista de Participantes do STR](https://dadosabertos.bcb.gov.br/dataset/lista-de-participantes-do-str)
- [Banco Central do Brasil — Participantes do STR PDF](https://www.bcb.gov.br/content/estabilidadefinanceira/str1/ParticipantesSTR.pdf)
- [Banco Central do Brasil — Metadados da lista de participantes](https://www.bcb.gov.br/conteudo/dadosabertos/BCBDeban/Metadados_participantes.pdf)
- [Banco Central do Brasil — Área das instituições participantes no Pix](https://www.bcb.gov.br/estabilidadefinanceira/pix-participantes)

## Fontes oficiais por banco localizadas

| Banco | Fontes oficiais localizadas | Uso na documentação |
| --- | --- | --- |
| Banco do Brasil | [Leiautes de arquivos](https://bb.com.br/site/pro-seu-negocio/aplicativos-leiautes-de-arquivos/), [API de Cobrança](https://bb.com.br/site/developers/api-cobranca/) | Boleto, CNAB e API. |
| Bradesco | [Validador de leiautes](https://wspf.bradesco.com.br/wsValidadorUniversal/validadorgeral) | CNAB 240/400 e tabelas de ocorrência. |
| Itaú | [CNAB 400](https://download.itau.com.br/bankline/layout_cobranca_400bytes_cnab_itau.pdf), [CNAB 240](https://download.itau.com.br/bankline/cobranca_cnab240.pdf) | Cobrança bancária CNAB. |
| Santander | [Layout de arquivos](https://www.santander.com.br/layout-de-arquivos), [Cobrança 400 posições](https://cms.santander.com.br/sites/WPS/documentos/arq-layout-de-arquivos-download-cobr400ptbr/25-09-22_165104_layout-cobranca-400-posicoes-jul-2025-portugues.pdf), [Código de barras](https://cms.santander.com.br/sites/WPS/documentos/arq-cobranca-barras-port-jul22/25-05-06_134319_codigo-de%2Bbarras-santander-abril-2025-v36-ptbr.pdf) | CNAB e boleto/código de barras. |
| Caixa Econômica Federal | [CNAB 400](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_400.pdf), [CNAB 240](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_240.pdf), [Código de barras SIGCB](https://www.caixa.gov.br/Downloads/cobranca-caixa/ESP_COD_BARRAS_SIGCB_COBRANCA_CAIXA.pdf) | CNAB e boleto/código de barras. |
| C6 Bank | [Manual CNAB](https://cms-assets-p.c6bank.com.br/uploads/manual-cnab.pdf), [Boleto de Cobrança](https://www.c6bank.com.br/boletocobranca/), [Portal Developers](https://developers.c6bank.com.br/) | CNAB 400, boleto e APIs. |
| BTG Pactual | [Cobrança](https://developers.empresas.btgpactual.com/docs/cobran%C3%A7a), [CNAB Febraban 240](https://developers.empresas.btgpactual.com/docs/cnab-febraban-240-posi%C3%A7%C3%B5es), [Layouts suportados](https://developers.empresas.btgpactual.com/docs/layouts-suportados) | CNAB 240, cobrança e Bolepix. |
| Sicoob | [Validador CNAB](https://www.sicoob.com.br/web/sicoob/validador-cnab), [Transferência de arquivos](https://www.sicoob.com.br/documents/2222345/8131567/Manual%2B-%2BTransfer%C3%A8ncia%2Bde%2BArquivos%2Bde%2BCobran%C3%A7a%2BBanc%C3%A1ria%2B-%2BSicoobnet%2BEmpresarial.pdf/3b291702-b88a-e73e-11e6-a9c73b55e06f?download=true&t=1609175823383) | CNAB, validação e homologação. |
| Sicredi | [Cobrança para empresas](https://www.sicredi.com.br/site/recebimentos-para-empresa/cobranca/), [API Pix PJ](https://www.sicredi.com.br/site/pixpj/api-pix/) | CNAB, cobrança e Pix. |
| Banco Inter | [Orientação oficial sobre boleto, CNAB e API](https://blog.bancointer.com.br/boleto-como-o-mei-pode-emitir-sem-pagar/) | Boleto, CNAB e API. |

## Bancos pendentes de manual público localizado

Para os bancos abaixo, manter somente dados confirmados pelo Banco Central e preencher boleto/CNAB após obter manual oficial no portal do banco ou via canal de homologação:

- Banco da Amazônia
- Banco do Nordeste
- Banestes
- Banrisul
- Ailos
- Banco Mercantil
- Safra
- Daycoval

## Regra de preenchimento

- Não copiar regra bancária de fonte comunitária sem confirmação em manual oficial.
- Registrar no arquivo do banco a URL, versão do manual e data de consulta.
- Quando o manual for recebido por gerente/canal privado, registrar o nome do documento, versão e data, sem publicar dados sensíveis.
- Preferir preencher campos como `A confirmar` até existir evidência oficial.
