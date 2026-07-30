# 10 — Contribuindo

Obrigado por contribuir com a PyCobrança. Este guia resume o fluxo de trabalho, os padrões de
código e como adicionar novos bancos e layouts.

## Fluxo de trabalho

1. Crie uma branch a partir da branch base do repositório.
2. Faça mudanças pequenas e coesas, com testes.
3. Rode a validação local (lint + testes) antes de abrir o PR.
4. Abra um Pull Request; a CI deve estar verde (ver [08 — Testes](08-testes-e-qualidade.md)).

## Ambiente de desenvolvimento

```bash
git clone https://github.com/Maxwbh/pycobranca.git
cd pycobranca
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Padrões de código

- **Python 3.14** (última versão estável) com type hints.
- **ruff** para lint e formatação (`ruff check .`, `ruff format .`).
- **Decimal** para valores monetários (nunca `float`).
- Nomes de domínio em português (`sacado`, `cedente`, `nosso_numero`) para alinhamento com o
  domínio bancário brasileiro.
- Docstrings objetivas; comentários só quando agregam.

## Mensagens de commit

- Em português, claras e descritivas.
- Uma unidade lógica por commit.
- Autoria atribuída a **@maxwbh**.

## Adicionando um novo banco

1. Crie `pycobranca/bancos/<banco>.py` herdando de `BancoBase`.
2. Declare `codigo`, `nome`, `digito_banco`, `carteiras`, `suporta_pix`.
3. Implemente `campo_livre()`, `nosso_numero_formatado()`, `agencia_conta_formatado()` e `validar()`.
4. O auto-registro (`__init_subclass__`) coloca o banco em `Bancos.todos()`.
5. Adicione testes com **valores conhecidos** de linha digitável e código de barras.
6. Atualize a matriz em [05 — Bancos Suportados](05-bancos-suportados.md).

## Adicionando um layout CNAB

1. Defina o layout posicional em `pycobranca/cnab/layouts/<layout>/<banco>.py`.
2. Implemente a remessa em `pycobranca/cnab/remessa/` e/ou o retorno em `pycobranca/cnab/retorno/`.
3. Adicione fixtures de remessa/retorno e testes (comparação byte-a-byte / mapeamento de ocorrências).
4. Atualize [06 — CNAB](06-cnab.md) se o layout trouxer particularidades.

## Checklist de PR

- [ ] Testes adicionados/atualizados e passando.
- [ ] `ruff check .` e `ruff format --check .` sem erros.
- [ ] Cobertura dentro da meta da fase.
- [ ] Documentação atualizada (`docs/` e/ou matriz de bancos).
- [ ] Sem segredos ou dados sensíveis no diff.

## Referências

- Manuais de layout CNAB (FEBRABAN) e EMV QR Code (Banco Central) por banco.
