# 09 — CI/CD

A validação automatizada da PyCobrança usa **GitHub Actions**: uma matriz de versões Python
com lint, testes e verificação de build.

## Pipelines

| Workflow | Arquivo | Gatilho | Objetivo |
|----------|---------|---------|----------|
| **CI** | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | push/PR em qualquer branch | Lint + testes + build. |
| **Homologação (HML)** | [`.github/workflows/hml.yml`](../.github/workflows/hml.yml) | push/PR na branch `hml` | Suíte estendida + cobertura + build. |

## CI (`ci.yml`)

Executado em cada push e pull request. Etapas:

1. **Checkout** do código.
2. **Python**: 3.14 (última versão estável).
3. **Instalação** de dependências (`pip install -e ".[dev]"`).
4. **Lint**: `ruff check .` e `ruff format --check .`.
5. **Testes**: `pytest`.
6. **Build** (job separado): `python -m build` para garantir empacotamento PEP 517 válido.

## Homologação (`hml.yml`)

Focado na branch `hml`, o ambiente de testes. Além do que a CI faz:

1. Roda a suíte **completa** na matriz Python.
2. Executa testes marcados como `hml`/`integration`, quando existirem.
3. Gera **relatório de cobertura** (`pytest --cov`).
4. Verifica o **build do pacote**.

Isso garante que só chega à `main` o que foi homologado. Ver
[08 — Testes e Qualidade](08-testes-e-qualidade.md).

## Convenções de commit

- Mensagens claras e descritivas, em português.
- Autoria atribuída a **@maxwbh**.
- Escopo enxuto por commit.

## Versionamento e release (planejado)

- **SemVer**: `MAJOR.MINOR.PATCH`.
- Versão declarada em `pycobranca/__init__.py` (`__version__`) e lida pelo `pyproject.toml`.
- `CHANGELOG.md` atualizado a cada release.
- Publicação no PyPI a partir da Fase 6 (workflow de release a ser adicionado quando houver
  pacote publicável).

## Segredos e ambiente

- Nenhum segredo é necessário para CI/HML nesta fase (sem publicação).
- Quando o release ao PyPI for habilitado, o token será configurado como secret do repositório
  (`PYPI_API_TOKEN`) e usado apenas no workflow de release.

## Como reproduzir a CI localmente

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest --cov=pycobranca --cov-report=term-missing
python -m build
```
