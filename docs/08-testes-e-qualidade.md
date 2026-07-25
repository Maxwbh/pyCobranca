# 08 — Testes e Qualidade

A qualidade da PyCobrança é sustentada por três pilares: **testes automatizados**, **lint/format
consistentes** e um **ambiente de homologação** na branch `hml`.

## Branch de homologação: `hml`

A branch **`hml`** é o foco dos testes de homologação. Ela funciona como o ambiente onde uma
mudança é validada de ponta a ponta antes de ser promovida.

### Fluxo de branches

```
feature/*  ──►  integracao/*  ──►  hml  ──►  main
   (dev)          (integração)     (homolog.)   (estável)
```

- **`feature/*`** — desenvolvimento de uma unidade de trabalho.
- **branch de integração** — onde a modernização é montada e revisada por PR.
- **`hml`** — homologação: recebe o conjunto validado e roda a suíte estendida (`hml.yml`).
- **`main`** — linha estável; só recebe o que passou pela homologação.

### O que roda em `hml`

O pipeline [`hml.yml`](../.github/workflows/hml.yml) executa, além da CI padrão:

- Suíte completa de testes em todas as versões Python suportadas.
- Testes marcados como `hml`/`integration` (quando existirem).
- Verificação de build do pacote (`python -m build`).
- Relatório de cobertura.

## Estratégia de testes

| Nível | Escopo | Ferramenta |
|-------|--------|-----------|
| Unitário | dígitos verificadores, datas, documentos, linha/barra | `pytest` |
| Por banco | valores conhecidos de linha digitável e código de barras | `pytest` + parametrização |
| CNAB | remessa byte-a-byte, parsing de retorno | `pytest` + fixtures |
| PIX | payload EMV, CRC16, QR Code | `pytest` |
| Contrato | artefatos vs. OpenAPI (contrato REST) | `pytest` |
| Renderização | geração de PDF sem erro, presença de elementos | `pytest` |

### Fixtures de referência

Arquivos de referência (código de barras, linha digitável, remessa e retorno) são a fonte
primária de fixtures. Cada banco portado deve trazer ao menos:

- Um caso de boleto com **linha digitável e código de barras conhecidos**.
- Fixtures de **remessa** (quando houver CNAB) para comparação byte-a-byte.
- Fixtures de **retorno** para validar o mapeamento de ocorrências.

## Ferramentas de qualidade

| Ferramenta | Papel |
|------------|-------|
| **pytest** | Execução de testes. |
| **ruff** | Lint + formatação (rápido, substitui flake8/isort/black). |
| **coverage / pytest-cov** | Cobertura. |
| **build** | Verificação de empacotamento (PEP 517). |

Configuração centralizada em [`pyproject.toml`](../pyproject.toml).

## Comandos locais

```bash
# instalar dependências de desenvolvimento
pip install -e ".[dev]"

# rodar testes
pytest

# rodar com cobertura
pytest --cov=pycobranca --cov-report=term-missing

# lint e formatação
ruff check .
ruff format --check .

# verificar build do pacote
python -m build
```

## Metas de cobertura

- **Fase 1:** cobertura ≥ 80% no núcleo (`core/`, `boleto/`).
- **Fases 2–4:** cada banco/layout portado entra com testes; sem regressão de cobertura.
- **Fase 6:** ampliação contínua da suíte de testes.

## Critérios de promoção para `main`

1. CI (`ci.yml`) verde em toda a matriz Python.
2. Homologação (`hml.yml`) verde na branch `hml`.
3. Cobertura dentro da meta da fase corrente.
4. Documentação atualizada para o recurso entregue.
