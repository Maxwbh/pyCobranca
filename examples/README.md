# Exemplos executáveis

Scripts curtos e **executáveis** que cobrem o ciclo completo da PyCobrança. A CI roda todos a cada
push (`python examples/executa_todos.py`), então eles não envelhecem em relação à API.

```bash
pip install pycobranca            # ou: pip install -e ".[dev]" no clone
python examples/01_boleto_pdf.py  # um exemplo
python examples/executa_todos.py  # todos, em sequência
```

Os PDFs e arquivos CNAB gerados vão para `examples/saida/` (ignorado pelo git).

| Exemplo | O que mostra | Doc |
|---|---|---|
| [`01_boleto_pdf.py`](01_boleto_pdf.py) | Boleto: linha digitável, código de barras, PDF *moderno*/*clássico* e logo do banco | [11](../docs/11-renderizacao.md) |
| [`02_bolepix.py`](02_bolepix.py) | Bolepix: BR Code (EMV + CRC16) e QR embutido no PDF | [07](../docs/07-pix.md) |
| [`03_remessa_cnab400.py`](03_remessa_cnab400.py) | Remessa CNAB 400 com juros, multa e desconto | [06](../docs/06-cnab.md) |
| [`04_remessa_cnab240.py`](04_remessa_cnab240.py) | Remessa CNAB 240 com segmento PIX (Y-03) | [06](../docs/06-cnab.md) |
| [`05_retorno_cnab.py`](05_retorno_cnab.py) | Leitura do retorno (banco e layout autodetectados) e tradução das ocorrências | [06](../docs/06-cnab.md) |
| [`06_ofx_conciliacao.py`](06_ofx_conciliacao.py) | Extrato OFX + conciliação pelo nosso número | [13](../docs/13-ofx.md) |
| [`07_carne.py`](07_carne.py) | Carnê de 12 parcelas (3 por A4) | [11](../docs/11-renderizacao.md) |
| [`08_fatura.py`](08_fatura.py) | Fatura nos 3 níveis: `itens`, `fatura.blocos` e `fatura.desenhar` | [11](../docs/11-renderizacao.md) |
| [`09_contrato_rest.py`](09_contrato_rest.py) | Serialização JSON e validação contra o contrato OpenAPI | [04](../docs/04-api-rest.md) |
| [`10_validacao_erros.py`](10_validacao_erros.py) | `BoletoInvalido.erros` — uma lista com um item por violação | [14](../docs/14-validacao-campos.md) |

## Dados de exemplo

`examples/dados/` traz um retorno CNAB 400 e um extrato OFX reais (dados fictícios), para que os
exemplos de leitura rodem sem depender de arquivos do seu banco.
