# Fontes oficiais para documentação bancária

Este arquivo registra as fontes oficiais usadas para preencher e revisar os documentos em
`docs/bancos/*.md`. A regra é: **não copiar regra bancária de fonte comunitária sem confirmação
em manual oficial**; ao usar um manual, registrar a URL, a versão e a data de consulta.

## Fonte regulatória comum

- [Banco Central do Brasil — Lista de Participantes do STR](https://dadosabertos.bcb.gov.br/dataset/lista-de-participantes-do-str)
- [Banco Central do Brasil — Participantes do STR (PDF)](https://www.bcb.gov.br/content/estabilidadefinanceira/str1/ParticipantesSTR.pdf)
- [Banco Central do Brasil — Manual do BR Code / Pix (Bolepix)](https://www.bcb.gov.br/estabilidadefinanceira/pix)

## Fontes oficiais por banco

| Banco | Fontes oficiais | Uso na documentação |
|-------|-----------------|---------------------|
| Banco do Brasil (001) | [Leiautes de arquivos](https://bb.com.br/site/pro-seu-negocio/aplicativos-leiautes-de-arquivos/) · [API de Cobrança](https://bb.com.br/site/developers/api-cobranca/) · Manual CNAB 240 (ago/2017) e Especificação de Boleto (jan/2016) | Boleto, CNAB 240/400 e API. |
| Bradesco (237) | [Validador de leiautes](https://wspf.bradesco.com.br/wsValidadorUniversal/validadorgeral) · Layout CNAB 240 e 400 posições · Especificação de Boleto (ago/2015) | CNAB 240/400 e tabelas de ocorrência. |
| Itaú (341) | [CNAB 400](https://download.itau.com.br/bankline/layout_cobranca_400bytes_cnab_itau.pdf) · [CNAB 240](https://download.itau.com.br/bankline/cobranca_cnab240.pdf) · Especificação de Boleto (mar/2015) | Cobrança bancária CNAB. |
| Santander (033) | [Layout de arquivos](https://www.santander.com.br/layout-de-arquivos) · Cobrança 400 posições H7800 (v2.33, jun/2024) · CNAB 240 H7815 (Multibanco) · Código de barras (v34, set/2021) | CNAB e boleto/código de barras. |
| Caixa (104) | [CNAB 400](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_400.pdf) · [CNAB 240](https://www.caixa.gov.br/Downloads/cobranca-caixa/Manual_de_Leiaute_de_Arquivo_Eletronico_CNAB_240.pdf) · Manual de Boleto (2020) · Código de barras SIGCB | CNAB e boleto SIGCB. |
| C6 Bank (336) | [Manual CNAB](https://cms-assets-p.c6bank.com.br/uploads/manual-cnab.pdf) · [Boleto de Cobrança](https://www.c6bank.com.br/boletocobranca/) · [Developers](https://developers.c6bank.com.br/) | CNAB 400, boleto e APIs. |
| Sicoob (756) | [Validador CNAB](https://www.sicoob.com.br/web/sicoob/validador-cnab) · Manual de Layout Sicoob (Cobrança) · Sicoobnet Empresarial | CNAB 240/400 e homologação. |
| Sicredi (748) | [Cobrança para empresas / manuais CNAB](https://www.sicredi.com.br/site/recebimentos-para-empresa/cobranca/) · Manual CNAB 240 e CNAB 400 (ago/2019) · [API Pix PJ](https://www.sicredi.com.br/site/pixpj/api-pix/) | CNAB 240/400 e Pix. |
| Banco do Nordeste (004) | [Cobrança BNB](https://www.bnb.gov.br/cobranca-bancaria) · Cobrança Eletrônica BNB · Padrão BNB CNAB 400 | CNAB 400. |
| Banrisul (041) | [Cobrança Banrisul](https://www.banrisul.com.br/) · Layout Cobrança CNAB 400 e CNAB 240 posições | CNAB 240/400. |
| Ailos (085) | [Cooperativas Ailos](https://ailos.coop.br/) · Manual Técnico de Cobrança Bancária — 240 Posições | CNAB 240. |
| Unicred (136) | [Unicred](https://www.unicred.com.br/) · Manual de Cobrança Unicred (leiautes CNAB 240 e CNAB 400) | CNAB 240/400. |

## Bancos pendentes de manual público localizado

Para os bancos abaixo, manter apenas os dados confirmados pelo Banco Central e o layout **portado
por comparação byte a byte com os vetores de referência**, complementando com manual oficial quando obtido no
portal do banco ou via canal de homologação:

- Banestes (021)
- Banco de Brasília / BRB (070) — layout DCB obtido via canal de homologação
- Banco Inter (077) — *Manual CNAB400 — Emissão boletos de cobrança*, v2.2 (26/08/2024),
  publicado pelo banco em `developers.inter.co/docs/cnab/manuais`. Seções usadas: 6 (carteiras
  110 e 112), 7.1.3 (campo livre) e 7.3 (DV do nosso número, com exemplo resolvido)
- CrediSIS (097) — *Padronização Boletos de Pagamento*, Cooperativa Central de Crédito Noroeste
  Brasileiro Ltda., v1.0 (maio/2017): define a composição do nosso número
  `097XAAAACCCCCCSSSSSS` (com `X` = módulo 11 do CPF/CNPJ do beneficiário). **Anterior à
  IN RFB 2.229/2024** — não cobre CNPJ alfanumérico.
- Citibank (745) — layout Citibank de cobrança 400 posições
- Safra (422)

## Regra de preenchimento

- Registrar no arquivo do banco a URL, a versão do manual e a data de consulta.
- Quando o manual for recebido por gerente/canal privado, registrar nome do documento, versão e
  data, sem publicar dados sensíveis.
- Enquanto não houver evidência oficial de uma regra, a fonte de verdade é a **paridade byte a
  byte com vetores de referência** (fixtures em `tests/fixtures/`), explicitamente anotada nos documentos.

## Fixtures de retorno externos (regressão)

Além dos vetores próprios, o parser e o validador estrutural são exercitados contra retornos CNAB
**reais de terceiros**, em `tests/fixtures/retorno/externos/` (Caixa 240, HSBC 400, Sicredi 400).
Extraídos do projeto **[laravel-boleto](https://github.com/eduardokum/laravel-boleto)** sob **licença
MIT** — atribuição completa em [`externos/NOTICE.md`](../../tests/fixtures/retorno/externos/NOTICE.md).
