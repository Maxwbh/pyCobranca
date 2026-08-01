# 17 — Compatibilidade e validação

Trocar a biblioteca que emite cobrança é uma decisão de risco: o arquivo vai para o banco, e um
byte errado numa posição vira título rejeitado. Esta página mostra **como a PyCobrança é
verificada** — o método, o que exatamente é comparado e como você reproduz tudo na sua máquina.

Nada aqui é auto-declarado: todas as afirmações correspondem a testes que rodam na CI a cada push
e que você pode executar localmente.

## As três camadas de verificação

| Camada | O que responde | Onde |
|---|---|---|
| **Paridade com a BrCobrança** | "o resultado é o mesmo de uma referência consagrada?" | [`test_validacao_cruzada.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/test_validacao_cruzada.py) |
| **Verificador FEBRABAN independente** | "um sistema externo aceitaria este título?" | [`test_validacao_externa.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/test_validacao_externa.py) |
| **Remessa byte a byte** | "o arquivo enviado ao banco é idêntico?" | [`test_cnab_remessa.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/test_cnab_remessa.py) |

---

## 1. Paridade com a BrCobrança (Ruby)

A [BrCobrança](https://github.com/kivanio/brcobranca) (MIT, © 2009 Kivanio Barbosa) é a referência
de cobrança bancária brasileira desde 2009 — e está creditada no
[`NOTICE`](https://github.com/Maxwbh/pyCobranca/blob/main/NOTICE) do projeto.
Para cada um dos **18 bancos**, os valores esperados dos testes foram
**gerados pela BrCobrança** (Ruby 3.3) com **exatamente os mesmos dados de entrada** e conferidos
campo a campo:

- **código de barras** (44 posições)
- **linha digitável** (47 posições)
- **nosso número formatado**

Esses valores vivem em
[`tests/exemplos_boletos.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/exemplos_boletos.py)
como fixtures permanentes: qualquer regressão futura que altere um código de barras quebra o teste.

!!! info "Divergência conhecida — Santander (033)"
    O nosso número do Santander é impresso com **13 posições** (12 dígitos + DV) no layout oficial.
    A PyCobrança segue o manual; a BrCobrança omite os zeros à esquerda (`1234567-9`). É uma
    diferença **cosmética de exibição** — o **código de barras é idêntico** nos dois sistemas, e é
    ele que o banco lê. A divergência está documentada, não é um bug silencioso.

---

## 2. Verificador FEBRABAN independente

Paridade com outra biblioteca prova que duas implementações concordam — não que ambas estejam
certas. Por isso existe uma segunda camada que **não usa nenhum código do núcleo**
(`pycobranca.core.dv`, `pycobranca.boleto`): ela reimplementa do zero o que um sistema externo faz
ao **receber** um boleto — um app de banco lendo a linha digitável, um PSP conferindo o código de
barras.

Para cada um dos 18 bancos, a partir do que a PyCobrança emitiu:

1. o código de barras tem 44 dígitos e o **DV geral (módulo 11)** confere;
2. a linha digitável tem 47 dígitos e os **três DVs de campo (módulo 10)** conferem;
3. a linha digitável **reconstrói exatamente** o código de barras (round-trip);
4. o **fator de vencimento** decodifica de volta à data de vencimento do título;
5. o **valor** embutido bate com o valor do título;
6. **banco** e **moeda** (Real = 9) batem.

Se a PyCobrança e esse verificador independente concordam, o título é aceito por qualquer sistema
conforme à FEBRABAN.

---

## 3. Remessa CNAB byte a byte

A remessa é onde o risco é maior: posição fixa, sem tolerância. A suíte compara o arquivo gerado
com **26 fixtures** de referência, **byte a byte**:

| Layout | Fixtures |
|---|---|
| CNAB 400 | 16 |
| CNAB 240 | 10 |

Cobrindo 15 bancos — Ailos, Banco do Brasil, BRB/Brasília, C6, Banco do Nordeste, Banrisul,
Bradesco, Caixa, Citibank, CrediSIS, Itaú, Santander, Sicoob, Sicredi e Unicred — incluindo as
variantes **com segmento PIX**.

Essas fixtures atravessaram todas as refatorações do projeto (reorganização do `render`, mudança de
piso do Python, CNPJ alfanumérico) **sem alteração de um único byte**.

O **retorno** tem 11 arquivos de referência (240 e 400), mais arquivos externos reais anonimizados.

---

## 4. Reproduza você mesmo

```bash
git clone https://github.com/Maxwbh/pyCobranca.git
cd pyCobranca
pip install -e ".[dev]"

# as duas camadas de validação do boleto (36 testes)
pytest tests/test_validacao_cruzada.py tests/test_validacao_externa.py -v

# remessa byte a byte
pytest tests/test_cnab_remessa.py -v

# a suíte completa (346 testes)
pytest
```

A CI roda os 346 testes em **Python 3.12, 3.13 e 3.14** a cada push, mais os
[exemplos executáveis](https://github.com/Maxwbh/pyCobranca/tree/main/examples), que instalam o
pacote **sem** as dependências de desenvolvimento — o que também valida o conteúdo do wheel.

---

## 5. Escopo da PyCobrança

Paridade de saída não significa paridade de escopo — e a BrCobrança é usada aqui como **referência
de verificação**, não como alvo de comparação. Ela tem 17 anos de campo e uma comunidade grande;
é exatamente por isso que serve de vetor de conferência.

O que a PyCobrança entrega, para você avaliar contra a sua solução atual (seja qual for):

| Recurso | Status |
|---|---|
| Boleto — código de barras, linha digitável, PDF | 18 bancos |
| CNAB 400 — remessa · retorno | 12 · parsing por banco |
| CNAB 240 — remessa · retorno | 7 · parsing por banco |
| Encargos na remessa | mora (valor/dia ou % mensal), multa, desconto 1º/2º/3º, IOF, abatimento |
| PIX / Bolepix | BR Code EMV + CRC16, QR no PDF e segmento PIX na remessa |
| OFX | leitura (v1/v2) e conciliação pelo nosso número |
| CNPJ alfanumérico | ✅ IN RFB 2.229/2024 |
| Contrato REST | OpenAPI 3.0 + validador leve, sem dependência HTTP |
| Documentos | boleto clássico e moderno, carnê (3/A4) e fatura |
| **Dependências de sistema** | **nenhuma** — ReportLab e qrcode são Python puro, um `pip install` |

O último item é o que mais costuma pesar na prática: sem cairo, Pango, GhostScript ou wkhtmltopdf,
o container fica pequeno e o deploy não quebra por biblioteca nativa faltando.

> Comparando com outra biblioteca? Confira o escopo dela na documentação oficial do próprio
> projeto — a lista acima descreve só a PyCobrança, e recursos de terceiros mudam a cada versão.

## Achou uma divergência?

Se algum banco gerar saída diferente do que o seu sistema atual produz,
[abra uma issue](https://github.com/Maxwbh/pyCobranca/issues) com os dados de entrada e a saída
esperada. Divergência com manual oficial é tratada como bug; divergência cosmética documentada
(como a do Santander) fica registrada nesta página.
