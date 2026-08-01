# 08 — Testes e Qualidade

A qualidade da PyCobrança é sustentada por dois pilares: **testes automatizados** e
**lint/format consistentes**, verificados na CI a cada mudança.

## Estratégia de testes

| Nível | Escopo | Ferramenta |
|-------|--------|-----------|
| Unitário | dígitos verificadores, datas, documentos, linha/barra | `pytest` |
| Por banco | valores conhecidos de linha digitável e código de barras | `pytest` + parametrização |
| CNAB | remessa byte-a-byte, parsing de retorno | `pytest` + fixtures |
| PIX | payload EMV, CRC16, QR Code | `pytest` |
| Contrato | artefatos vs. OpenAPI (contrato REST) | `pytest` |
| Renderização | geração de PDF sem erro, presença de elementos | `pytest` |
| Exemplos | os scripts de `examples/` rodam ponta a ponta | `examples/executa_todos.py` |

> A leitura voltada para quem está **avaliando adotar** a biblioteca — método de verificação,
> paridade com a BrCobrança e como reproduzir — está em
> [17 — Compatibilidade e validação](17-compatibilidade.md).

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

# exemplos executáveis (documentação que não envelhece)
python examples/executa_todos.py

# verificar build do pacote
python -m build
```

### Exemplos como teste de fumaça

`examples/` reúne scripts curtos que exercitam a API pública — boleto, Bolepix, remessa 400/240,
retorno, OFX, carnê, fatura, contrato REST e tratamento de erros. A CI executa todos a cada push
(job **Exemplos executáveis**), instalando o pacote **sem** as dependências de desenvolvimento:
quebra de API pública, dado de exemplo defasado ou arquivo faltando no wheel aparecem ali antes de
chegar ao usuário.

## Metas de cobertura

- **Núcleo** (`core/`, `boleto/`): cobertura ≥ 80%.
- Cada banco/layout portado entra com testes; sem regressão de cobertura.
- Ampliação contínua da suíte.

## Critérios para aceitar uma mudança

1. CI verde em toda a matriz Python.
2. Testes cobrindo o comportamento novo (e as fixtures de referência intactas).
3. Cobertura dentro da meta.
4. Documentação atualizada para o recurso entregue.
