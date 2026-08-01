# 05 — Bancos Suportados

Matriz de bancos da PyCobrança. **Prioridade** indica a ordem de implementação no
[roadmap](02-roadmap-modernizacao.md).

## Legenda

- ✅ suportado
- ▫️ planejado (fase posterior)
- 🔶 apenas via CNAB (sem API proprietária nesta biblioteca)
- PIX = suporte a Bolepix

| Código | Banco | Boleto | Remessa | Retorno | PIX | Prioridade |
|:------:|-------|:------:|:-------:|:-------:|:---:|:----------:|
| 001 | Banco do Brasil | ✅ | ✅ | ✅ | ✅ | P1 |
| 033 | Santander | ✅ | ✅ | ✅ | ✅ | P1 |
| 041 | Banrisul | ✅ | ▫️ | ▫️ | ▫️ | P2 |
| 070 | BRB | ✅ | ▫️ | ▫️ | ▫️ | P2 |
| 104 | Caixa Econômica | ✅ | ✅ | ✅ | ✅ | P1 |
| 237 | Bradesco | ✅ | ✅ | ✅ | ✅ | P1 |
| 341 | Itaú | ✅ | ✅ | ✅ | ✅ | P1 |
| 336 | C6 Bank | 🔶 | ▫️ | ▫️ | ▫️ | P3 |
| 748 | Sicredi | ▫️ | ▫️ | ▫️ | ▫️ | P2 |
| 756 | Sicoob | ▫️ | ✅ | ✅ | ✅ | P2 |

> Estado atual: **emissão de boleto implementada para os 18 bancos** (campo livre, DVs, código de
> barras, linha digitável e PDF via ReportLab), todos **validados por vetores de referência** — ver
> [`docs/bancos/`](bancos/README.md). CNAB segue o roadmap.

## Bancos prioritários (P1)

Os cinco bancos abaixo são o foco inicial por cobrirem a maior parte do volume de emissão:

1. **Banco do Brasil (001)**
2. **Bradesco (237)**
3. **Itaú (341)**
4. **Santander (033)**
5. **Caixa Econômica (104)**

Para cada P1, a definição de pronto exige: emissão de boleto (PDF + linha digitável + código de
barras), remessa CNAB (240 e/ou 400 conforme o banco), parsing de retorno e — quando aplicável —
Bolepix.

## Contrato por banco (`BancoBase`)

Cada banco declara:

| Atributo/método | Descrição |
|-----------------|-----------|
| `codigo` | Código FEBRABAN (3 dígitos). |
| `nome` | Nome de exibição. |
| `digito_banco` | Dígito verificador do código do banco. |
| `carteiras` | Carteiras suportadas. |
| `campo_livre()` | 25 posições do código de barras específicas do banco. |
| `nosso_numero_formatado()` | Formatação do nosso número. |
| `agencia_conta_formatado()` | Formatação de agência/conta. |
| `validar()` | Regras de validação específicas. |
| `suporta_pix` | Flag de capacidade PIX. |

## Como adicionar um novo banco

1. Criar `bancos/<nome_banco>.py` herdando de `BancoBase`.
2. Implementar `campo_livre()`, `nosso_numero_formatado()` e `validar()`.
3. Declarar `codigo`, `nome`, `digito_banco`, `carteiras`, `suporta_pix`.
4. Registrar automaticamente (o `__init_subclass__` de `BancoBase` cuida disso).
5. Adicionar fixtures de teste (valor conhecido de linha digitável/código de barras).
6. Se houver CNAB, adicionar layout em `cnab/layouts/` e testes de remessa/retorno.

Detalhes em [10 — Contribuindo](10-contribuindo.md).
