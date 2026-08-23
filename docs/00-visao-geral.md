# 00 — Visão Geral

## Objetivo

A **PyCobrança** é uma biblioteca Python moderna para o ciclo completo de cobrança bancária
brasileira: emissão de boletos, geração e leitura de arquivos CNAB (remessa e retorno), PIX/Bolepix
e serialização dos artefatos para consumo via API REST.

O objetivo é oferecer uma plataforma única, coesa e testada banco a banco — em Python puro, sem
dependências de sistema — que sirva de **motor de cobrança** para ERPs, back-ends e serviços
financeiros.

## Princípios de design

1. **Python moderno primeiro.** Type hints expostos ao consumidor (PEP 561), `pyproject.toml`,
   piso em **Python 3.12** (suíte na matriz 3.12/3.13/3.14) e dependências puras em Python.
2. **Conformidade FEBRABAN verificável.** Cada regra (DV, fator de vencimento, campo livre, layout
   CNAB) é coberta por testes com valores conhecidos.
3. **Serialização JSON de primeira classe.** Os artefatos que atravessam a fronteira do processo
   — título, retorno CNAB, extrato OFX e conciliação — expõem `to_dict()`; o formato exato de uma
   API REST vem de `pycobranca.contracts`.
4. **Validação por banco explícita e testável.** Cada banco declara suas regras; falhas são erros
   de domínio claros, não exceções genéricas.
5. **Sem dependências de sistema.** A renderização é pura Python (ReportLab) — nada de cairo, Pango
   ou GhostScript.
6. **API enxuta e direta.** Uma única forma de fazer cada coisa, alinhada ao domínio bancário
   brasileiro.

## Uma biblioteca embutível

A PyCobrança é uma **biblioteca**, e isso é uma escolha de projeto — não uma etapa a caminho de
virar serviço. Na prática, para quem constrói em cima dela:

- **Roda dentro do seu processo.** Sem rede, sem estado, sem daemon, sem sidecar. Um `pip install`
  e as funções estão disponíveis; o que entra e o que sai é objeto Python.
- **Você decide a moldura.** Transporte, persistência, filas, agendamento e autenticação continuam
  seus. A biblioteca não escolhe framework web, ORM nem broker por você.
- **O contrato REST vem como dado, não como servidor.** `pycobranca.contracts` entrega a
  especificação OpenAPI 3.0, os serializadores e um validador leve —
  [sem dependência HTTP](04-api-rest.md). Você expõe do seu jeito, em FastAPI, Flask, Django ou o
  que preferir.
- **Licença BSD-3-Clause.** Permite embutir em **produto comercial fechado**, sem obrigação de
  abrir o seu código. Só é preciso manter o aviso de copyright.
- **Neutra em relação a quem consome.** A biblioteca não divulga, não privilegia e não depende de
  nenhum produto construído sobre ela. Se você criar um serviço, um SaaS ou uma API a partir da
  PyCobrança, não vai encontrar um concorrente na página inicial dela.

Essa neutralidade é deliberada: a direção da dependência é sempre `consumidor → biblioteca`, nunca
o contrário. É o que permite que produtos diferentes — inclusive concorrentes entre si — usem a
mesma engine sem conflito.

## Escopo

- Emissão de boletos em PDF (linha digitável, código de barras, layout), carnê e fatura.
- CNAB 240 e 400 — remessa (geração) e retorno (parsing → JSON).
- Leitura de extrato OFX e conciliação com os boletos emitidos.
- PIX/Bolepix: QR Code no boleto e segmento PIX no CNAB.
- Registro programático de bancos (`Bancos.todos`, `.find`, `.com_pix`).
- Validação de campos por banco.
- Contrato de dados serializável para API REST (OpenAPI 3.0).
- CI de validação (lint + testes em matriz de versões Python).

## Público-alvo

- Times Python que precisam emitir boletos, gerar/ler CNAB e produzir PIX.
- Integradores que precisam de emissão e conciliação (retorno) em Python.
- Produtos que querem uma engine de cobrança embutível, sem serviço externo.
- **Quem constrói serviço em cima**: APIs REST, SaaS de cobrança, gateways internos e plataformas
  multi-tenant — a licença BSD-3 e a neutralidade da biblioteca cobrem esse uso.

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Divergência nas regras bancárias por banco/carteira. | Testes com vetores de referência por banco/layout (linha digitável, código de barras, remessa byte a byte) e um validador FEBRABAN independente. |
| Dependências pesadas para renderização de PDF. | Renderização em Python puro (ReportLab), sem libs nativas — ver [11 — Renderização](11-renderizacao.md). |
| Divergência entre ambientes de validação e produção. | Contratos OpenAPI versionados e fixtures de referência congeladas. |
| Falta de dados reais para retorno/CNAB. | Fixtures anonimizadas e cenários mínimos por banco. |
| Lotes grandes causando estouro de memória. | `gera_arquivo()` monta o arquivo inteiro em memória; o custo está medido em [19 — Integração](19-integracao.md#lotes). |

## Definição de pronto (nível projeto)

- Conformidade FEBRABAN testada por banco (código de barras, linha digitável, remessa e retorno).
- CI verde em todas as versões Python suportadas (ver [08 — Testes](08-testes-e-qualidade.md)).
- Contrato de dados exercitado contra a especificação OpenAPI.
