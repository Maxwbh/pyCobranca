---
# O `<title>` da home era só "PyCobrança" — um nome que ninguém procura. Quem
# busca digita "boleto python", "cnab 240 python". O front-matter `title` tem
# precedência sobre o `site_name` no tema, inclusive na home, e o nome do projeto
# entra como sufixo. O rótulo "Início" da navegação vem do `nav` e não muda.
title: Boleto bancário, CNAB 240/400 e PIX em Python
description: >-
  Gere boleto bancário, arquivos CNAB 240/400 e QR Code PIX em Python puro.
  18 bancos, sem dependência de API externa. pip install pycobranca.
---

# PyCobrança

**Boletos, CNAB 240/400 e PIX para 18 bancos — em Python puro, num único `pip install`.**

A PyCobrança é a plataforma Open Source de cobrança bancária brasileira em Python. Uma única
biblioteca cobre o ciclo completo: emite boletos (código de barras, linha digitável e PDF), gera e
lê arquivos CNAB (remessa e retorno 240/400), produz PIX/Bolepix e concilia o extrato OFX — sem
dependências de sistema.

```bash
pip install pycobranca
```

```python
from datetime import date
from pycobranca.bancos import Bancos
from pycobranca.render import render_boleto_pdf

Banco = Bancos.find("341")  # Itaú, pelo código FEBRABAN
boleto = Banco(
    valor="127.50",
    cedente="Empresa Exemplo LTDA",
    cedente_documento="11.222.333/0001-81",
    agencia="0057",
    conta="12345",
    carteira="109",
    nosso_numero="12345678",
    data_vencimento=date(2026, 8, 15),
    sacado="Cliente Final da Silva",
    sacado_documento="529.982.247-25",
)
boleto.validar()
print(boleto.linha_digitavel)

open("boleto.pdf", "wb").write(render_boleto_pdf(boleto.contexto_render()))
```

## Por onde começar

| Se você quer… | Comece por |
|---|---|
| Entender o escopo e a arquitetura | [Visão geral](00-visao-geral.md) · [Arquitetura](01-arquitetura.md) |
| **Avaliar se dá para confiar** | [Compatibilidade e validação](17-compatibilidade.md) |
| Saber o que cada banco suporta | [Bancos suportados](05-bancos-suportados.md) · [Docs por banco](bancos/README.md) |
| Gerar remessa e ler retorno | [CNAB](06-cnab.md) |
| Emitir Bolepix | [PIX](07-pix.md) |
| Personalizar o PDF (boleto, carnê, fatura) | [Renderização](11-renderizacao.md) |
| Expor a engine por HTTP | [Contrato REST](04-api-rest.md) |
| Tratar erros de validação | [Validação de campos](14-validacao-campos.md) |
| **Preparar-se para o CNPJ alfanumérico** | [CNPJ alfanumérico](18-cnpj-alfanumerico.md) |
| Conciliar o extrato | [OFX](13-ofx.md) |
| Emitir em lote | [Processamento em lote](12-processamento-lote.md) |
| Adicionar um banco novo | [Guia de novo banco](15-novo-banco.md) · [Contribuindo](10-contribuindo.md) |

## Exemplos executáveis

O repositório traz [exemplos executáveis](https://github.com/Maxwbh/pyCobranca/tree/main/examples)
cobrindo boleto, Bolepix, remessa 400/240, retorno, OFX, carnê, fatura, contrato REST e tratamento
de erros. A CI roda todos a cada push, então eles nunca ficam desatualizados:

```bash
python examples/executa_todos.py
```

## Links

- [PyPI](https://pypi.org/project/pycobranca/) · [GitHub](https://github.com/Maxwbh/pyCobranca)
- [Changelog](changelog.md) · [Licença BSD-3-Clause](https://github.com/Maxwbh/pyCobranca/blob/main/LICENSE)
