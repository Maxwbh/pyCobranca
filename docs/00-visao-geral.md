# 00 — Visão Geral

## Objetivo

A **PyCobrança** é uma biblioteca Python moderna para o ciclo completo de cobrança bancária
brasileira: emissão de boletos, geração e leitura de arquivos CNAB (remessa e retorno), PIX/Bolepix
e serialização dos artefatos para consumo via API REST.

O objetivo é oferecer uma plataforma única, coesa e testada banco a banco — em Python puro, sem
dependências de sistema — que sirva de **motor de cobrança** para ERPs, back-ends e serviços
financeiros.

## Princípios de design

1. **Python moderno primeiro.** Type hints, `pyproject.toml`, última versão estável do Python
   (3.14) e dependências puras em Python.
2. **Conformidade FEBRABAN verificável.** Cada regra (DV, fator de vencimento, campo livre, layout
   CNAB) é coberta por testes com valores conhecidos.
3. **Serialização JSON de primeira classe.** Todo objeto de domínio expõe `to_dict()` para consumo
   por APIs e microsserviços.
4. **Validação por banco explícita e testável.** Cada banco declara suas regras; falhas são erros
   de domínio claros, não exceções genéricas.
5. **Sem dependências de sistema.** A renderização é pura Python (ReportLab) — nada de cairo, Pango
   ou GhostScript.
6. **API enxuta e direta.** Uma única forma de fazer cada coisa, alinhada ao domínio bancário
   brasileiro.

## Escopo

- Emissão de boletos em PDF (linha digitável, código de barras, layout), carnê e fatura.
- CNAB 240 e 400 — remessa (geração) e retorno (parsing → JSON).
- Leitura de extrato OFX e conciliação com os boletos emitidos.
- PIX/Bolepix: QR Code no boleto e segmento PIX no CNAB.
- Registro programático de bancos (`Bancos.todos`, `.find`, `.com_pix`).
- Validação de campos por banco.
- Contrato de dados serializável para API REST (OpenAPI 3.0).
- CI de validação (lint + testes em matriz de versões Python).

## Não-objetivos

- Suporte a formatos de impressão exóticos (PostScript nativo).

## Público-alvo

- Times Python que precisam emitir boletos, gerar/ler CNAB e produzir PIX.
- Integradores que precisam de emissão e conciliação (retorno) em Python.
- Produtos que querem uma engine de cobrança embutível, sem serviço externo.

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Divergência nas regras bancárias por banco/carteira. | Testes com vetores de referência por banco/layout (linha digitável, código de barras, remessa byte a byte) e um validador FEBRABAN independente. |
| Dependências pesadas para renderização de PDF. | Renderização em Python puro (ReportLab), sem libs nativas — ver [11 — Renderização](11-renderizacao.md). |
| Divergência entre ambientes de validação e produção. | Contratos OpenAPI versionados e fixtures de referência congeladas. |
| Falta de dados reais para retorno/CNAB. | Fixtures anonimizadas e cenários mínimos por banco. |
| Lotes grandes causando timeout/estouro de memória. | Processamento assíncrono por job — ver [12 — Processamento em Lote](12-processamento-lote.md). |

## Definição de pronto (nível projeto)

- Conformidade FEBRABAN testada por banco (código de barras, linha digitável, remessa e retorno).
- CI verde em todas as versões Python suportadas (ver [08 — Testes](08-testes-e-qualidade.md)).
- Contrato de dados exercitado contra a especificação OpenAPI.
