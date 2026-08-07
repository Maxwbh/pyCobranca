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
git clone https://github.com/Maxwbh/pyCobranca.git
cd pyCobranca
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

### Documentação (MkDocs)

O site publicado em <https://maxwbh.github.io/pyCobranca/> é gerado do próprio `docs/`:

```bash
pip install -e ".[docs]"
cp CHANGELOG.md docs/changelog.md   # o changelog vive na raiz e é copiado no build
mkdocs serve                        # pré-visualização em http://127.0.0.1:8000
mkdocs build --strict               # o mesmo que a CI roda (falha em link quebrado)
```

Os documentos são escritos para serem lidos **também no GitHub**, com links relativos
(`../pycobranca/render/tela.py`). O hook `mkdocs_hooks.py` reescreve esses links no site — para a
URL do arquivo no repositório quando apontam para fora de `docs/`, e para o caminho relativo
correto quando apontam para outra página. Páginas novas entram na `nav` do `mkdocs.yml`.

## Padrões de código

- **Python 3.12+** com type hints; a CI roda a suíte em 3.12, 3.13 e 3.14.
- A biblioteca é **tipada** (PEP 561, `pycobranca/py.typed`): mantenha as anotações em dia — elas
  chegam ao mypy/pyright de quem consome o pacote.
- **ruff** para lint e formatação (`ruff check .`, `ruff format .`).
- **Decimal** para valores monetários (nunca `float`).
- Nomes de domínio em português (`sacado`, `cedente`, `nosso_numero`) para alinhamento com o
  domínio bancário brasileiro.
- Docstrings objetivas; comentários só quando agregam.

## Mensagens de commit

- Em português, claras e descritivas, no imperativo
  (ex.: `Adiciona carteira 51 ao Banco do Nordeste`).
- Uma unidade lógica por commit.
- **A autoria é de quem escreveu o commit** — mantenha o seu `user.name` e `user.email`.
- **Sem atribuição a ferramenta de IA**, nem na mensagem nem na identidade de autor/committer:
  rodapés de geração automática, `Co-authored-by` de assistentes e afins. O mesmo vale para o
  título, o corpo e os comentários do PR. A checagem `Guarda de fluxo` reprova o PR quando
  encontra alguma dessas marcas.

## Adicionando um novo banco

1. Crie `pycobranca/bancos/<banco>.py` herdando de `BancoBase`.
2. Declare `codigo`, `nome`, `digito_banco`, `carteiras`, `suporta_pix`.
3. Implemente `campo_livre()`, `nosso_numero_formatado()`, `agencia_conta_formatado()` e `validar()`.
4. O auto-registro (`__init_subclass__`) coloca o banco em `Bancos.todos()`.
5. Adicione testes com **valores conhecidos** de linha digitável e código de barras.
6. Atualize a matriz em [05 — Bancos Suportados](05-bancos-suportados.md).

## Adicionando um layout CNAB

1. Defina o layout posicional em `pycobranca/cnab/cnab400/<banco>.py` ou
   `pycobranca/cnab/cnab240/<banco>.py`.
2. A remessa fica no próprio módulo do layout; o retorno, em `pycobranca/cnab/retorno/`.
3. Adicione fixtures de remessa/retorno e testes (comparação byte-a-byte / mapeamento de ocorrências).
4. Atualize [06 — CNAB](06-cnab.md) se o layout trouxer particularidades.

## Checklist de PR

- [ ] Testes adicionados/atualizados e passando.
- [ ] `ruff check .` e `ruff format --check .` sem erros.
- [ ] `python examples/executa_todos.py` verde (os exemplos acompanham a API).
- [ ] Cobertura dentro da meta da fase.
- [ ] Documentação atualizada (`docs/` e/ou matriz de bancos).
- [ ] Sem segredos ou dados sensíveis no diff.

## Referências

- Manuais de layout CNAB (FEBRABAN) e EMV QR Code (Banco Central) por banco.
