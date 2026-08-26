# 17 — Compatibilidade e validação

Trocar a biblioteca que emite cobrança é uma decisão de risco: o arquivo vai para o banco, e um
byte errado numa posição vira título rejeitado. Esta página mostra **como a PyCobrança é
verificada** — o método, o que exatamente é comparado e como você reproduz tudo na sua máquina.

Nada aqui é auto-declarado: todas as afirmações correspondem a testes que rodam na CI a cada push
e que você pode executar localmente.

## As três camadas de verificação

| Camada | O que responde | Onde |
|---|---|---|
| **Vetores de referência** | "o resultado bate com o de implementações já em produção?" | [`test_validacao_cruzada.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/test_validacao_cruzada.py) |
| **Verificador FEBRABAN independente** | "um sistema externo aceitaria este título?" | [`test_validacao_externa.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/test_validacao_externa.py) |
| **Remessa byte a byte** | "o arquivo enviado ao banco é idêntico?" | [`test_cnab_remessa.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/test_cnab_remessa.py) |

---

## De onde a PyCobrança veio

Dois projetos influenciaram esta biblioteca, em momentos diferentes. Ambos estão creditados no
[`NOTICE`](https://github.com/Maxwbh/pyCobranca/blob/main/NOTICE):

| Projeto | Licença | Papel |
|---|---|---|
| [**pyboleto**](https://github.com/eduardocereto/pyboleto) (Python) | BSD, © 2011 Eduardo Cereto Carvalho e contribuidores | **A inspiração original** — mostrou que emitir boleto brasileiro em Python puro era possível |
| [**BrCobrança**](https://github.com/kivanio/brcobranca) (Ruby) | MIT · © 2009 Kivanio Barbosa | **Elo adicional** — ampliou o escopo (CNAB, mais bancos e layouts) e simplificou soluções |

A **pyboleto** veio primeiro: é dela a ideia de que o problema merecia uma biblioteca Python
dedicada. A PyCobrança nasceu desse caminho. A **BrCobrança** entrou depois, para ampliar o
alcance.

O crédito acima é obrigação das licenças BSD e MIT, e está no
[`NOTICE`](https://github.com/Maxwbh/pyCobranca/blob/main/NOTICE) distribuído no pacote. Nada aqui
descreve a verificação: os vetores da seção 1 vêm de implementações em produção, e quais são elas
não muda o que o teste prova.

---

## 1. Vetores de referência

Para **18 dos 19 bancos**, os valores esperados dos testes foram **gerados por implementações
de cobrança já em produção**, com **exatamente os mesmos dados de entrada**, e conferidos campo a
campo:

- **código de barras** (44 posições)
- **linha digitável** (47 posições)
- **nosso número formatado**

Esses valores vivem em
[`tests/exemplos_boletos.py`](https://github.com/Maxwbh/pyCobranca/blob/main/tests/exemplos_boletos.py)
como fixtures permanentes: qualquer regressão futura que altere um código de barras quebra o teste.

!!! info "Vetor não é prova de correção"
    Duas implementações concordarem prova que concordam, não que ambas estejam certas. É por isso
    que existe a camada seguinte, que não usa nenhum código do núcleo, e por isso que divergência
    contra **manual oficial** é tratada como bug mesmo quando o vetor externo concorda com a saída
    atual.

---

## 2. Verificador FEBRABAN independente

Esta camada **não usa nenhum código do núcleo**
(`pycobranca.core.dv`, `pycobranca.boleto`): ela reimplementa do zero o que um sistema externo faz
ao **receber** um boleto — um app de banco lendo a linha digitável, um PSP conferindo o código de
barras.

Para cada um dos 19 bancos, a partir do que a PyCobrança emitiu:

1. o código de barras tem 44 dígitos e o **DV geral (módulo 11)** confere;
2. a linha digitável tem 47 dígitos e os **três DVs de campo (módulo 10)** conferem;
3. a linha digitável **reconstrói exatamente** o código de barras (round-trip);
4. o **fator de vencimento** decodifica de volta à data de vencimento do título;
5. o **valor** embutido bate com o valor do título;
6. **banco** e **moeda** (Real = 9) batem.

Se a PyCobrança e esse verificador independente concordam, o título é aceito por qualquer sistema
conforme à FEBRABAN.

O **Inter (077)** é a exceção da camada 1: ele não existe em nenhuma implementação aberta
conhecida, então não há vetor cruzado para ele. A saída do boleto vem do manual do próprio banco —
com o dígito do nosso número conferido contra o exemplo resolvido da seção 7.3 — e a **remessa foi
submetida ao validador de layout do próprio Inter**, que a aprovou. Para esse banco, portanto, a
verificação externa está nas camadas 2 e 3, não na 1.

O Itaú entra aqui com **as sete carteiras aceitas**, não só a do exemplo: a composição do dígito do
nosso número muda por carteira, e conferir uma só deixaria as outras seis apoiadas apenas no vetor
externo — que prova concordância, não correção.

---

## 3. Remessa CNAB byte a byte

A remessa é onde o risco é maior: posição fixa, sem tolerância. A suíte compara o arquivo gerado
com **27 fixtures** de referência, **byte a byte**:

| Layout | Fixtures |
|---|---|
| CNAB 400 | 17 |
| CNAB 240 | 10 |

Cobrindo 16 bancos — Ailos, Banco do Brasil, BRB/Brasília, C6, Banco do Nordeste, Banrisul,
Bradesco, Caixa, Citibank, CrediSIS, Inter, Itaú, Santander, Sicoob, Sicredi e Unicred — incluindo
as variantes **com segmento PIX**.

A fixture do Inter é a única **auto-gerada** — não existe implementação de referência que produza
remessa dele. Em compensação, o arquivo foi submetido ao **validador de layout do próprio banco**,
que o aprovou; ali a verificação externa vem do emissor, não de um segundo gerador.

Essas fixtures atravessaram todas as refatorações do projeto (reorganização do `render`, mudança de
piso do Python, CNPJ alfanumérico) **sem alteração de um único byte**.

O **retorno** tem 11 arquivos de referência (240 e 400), mais arquivos externos reais anonimizados.

---

## 4. Reproduza você mesmo

```bash
git clone https://github.com/Maxwbh/pyCobranca.git
cd pyCobranca
pip install -e ".[dev]"

# as duas camadas de validação do boleto (43 testes)
pytest tests/test_validacao_cruzada.py tests/test_validacao_externa.py -v

# remessa byte a byte
pytest tests/test_cnab_remessa.py -v

# a suíte completa (1056 testes)
pytest
```

A CI roda os 1056 testes em **Python 3.12, 3.13 e 3.14** a cada push, mais os
[exemplos executáveis](https://github.com/Maxwbh/pyCobranca/tree/main/examples), que instalam o
pacote **sem** as dependências de desenvolvimento — o que também valida o conteúdo do wheel.

---

## 5. Escopo da PyCobrança

Paridade de saída não significa paridade de escopo: as implementações usadas como vetor servem para
**conferir o número que sai**, não como alvo de comparação de recursos.

O que a PyCobrança entrega, para você avaliar contra a sua solução atual (seja qual for):

| Recurso | Status |
|---|---|
| Boleto — código de barras, linha digitável, PDF | 19 bancos |
| CNAB 400 — remessa · retorno | 14 · parsing por banco |
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
esperada — de preferência com o boleto que o **banco** emitiu, que é o único árbitro quando o
manual é ambíguo.

Divergência contra manual oficial é tratada como bug. Divergência cosmética conhecida fica
registrada na página do banco em [`docs/bancos/`](bancos/README.md) — é o caso do nosso número do
Santander, impresso com 13 posições conforme o layout oficial.
