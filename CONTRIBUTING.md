# Contribuindo com a PyCobrança

Obrigado pelo interesse! PyCobrança é um projeto **novo** e aberto a contribuições — de correções
pequenas a novos layouts de banco. Este guia mostra como preparar o ambiente, o padrão de código e
como enviar sua mudança.

## Ambiente de desenvolvimento

Requer **Python 3.12+**.

```bash
git clone https://github.com/Maxwbh/pyCobranca.git
cd pyCobranca
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

O extra `dev` instala tudo o que a suíte precisa (ReportLab, qrcode, pytest, ruff, build).

## Antes de abrir o Pull Request

Rode localmente — o PR precisa passar nestes três comandos:

```bash
ruff check .            # lint
ruff format --check .   # formatação
pytest                  # testes
```

## Padrões

- **Estilo:** `ruff` cuida de lint e formatação (config no `pyproject.toml`). Rode
  `ruff format .` antes de commitar.
- **Nomes em pt-BR:** o domínio (bancos, CNAB, boleto) usa a nomenclatura canônica em português;
  mantenha o padrão dos módulos vizinhos.
- **Testes:** toda mudança de comportamento vem com teste. Regras de banco/CNAB devem ser cobertas
  por um caso com valores conhecidos.
- **Commits:** mensagens claras e descritivas, em português, no imperativo
  (ex.: `Adiciona carteira 51 ao Banco do Nordeste`).
- **Docs:** ao alterar uma regra de banco, atualize o documento correspondente em
  [`docs/bancos/`](docs/bancos/).

## Fluxo de contribuição

1. Faça um _fork_ e crie um branch para a sua mudança.
2. Implemente com testes e documentação.
3. Garanta que `ruff` e `pytest` passam.
4. Abra o Pull Request descrevendo **o quê** e **por quê**. Para mudanças grandes, abra uma
   _issue_ antes para alinharmos o desenho.

## Como adicionar um banco

1. Crie a classe do banco em `pycobranca/bancos/<banco>.py` (herda de `BancoBase`): código
   FEBRABAN, carteiras, regra do nosso número/DV e composição do campo livre.
2. Adicione um teste com um **exemplo oficial validável** (código de barras + linha digitável de
   referência do manual do banco) — é o critério para aceitar um banco novo.
3. Documente o layout em `docs/bancos/NNN-<banco>.md`.
4. Para CNAB, adicione a remessa/retorno correspondente e o respectivo teste.

## Boas primeiras contribuições

- Novos bancos com exemplo oficial de código de barras/linha digitável.
- Casos de teste de retorno reais (anonimizados) para ampliar a cobertura de ocorrências.
- Melhorias de documentação e exemplos.

## Reportando problemas

Ao abrir uma _issue_, inclua: versão da PyCobrança e do Python, banco/carteira envolvidos, o dado
de entrada (anonimizado) e o resultado esperado × obtido. Para arquivos CNAB, anexe apenas linhas
anonimizadas.

## Licença

Ao contribuir, você concorda que sua contribuição será licenciada sob a
[BSD-3-Clause](LICENSE) do projeto.
