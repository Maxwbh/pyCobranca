# 07 — PIX / Bolepix

O **Bolepix** é o boleto híbrido: um boleto tradicional com QR Code PIX impresso, pagável pelo
código ou pela linha digitável. A PyCobrança gera o payload PIX (BR Code), o QR Code e o segmento
PIX no CNAB de remessa.

## Dois QR diferentes — e a diferença custa dinheiro

!!! danger "Só o QR que o banco gerou liquida o boleto"
    | | Como nasce | O que acontece ao pagar |
    |---|---|---|
    | **Bolepix** (`pix_copia_cola`) | o **banco** gera no registro da cobrança; QR **dinâmico**, com o mesmo identificador do título | credita **e dá baixa no boleto**; duplicidade bloqueada |
    | **PIX avulso** (`pix_chave`) | montado aqui, a partir da chave; BR Code **estático** | credita a chave, mas **o título fica em aberto** |

    Pagar um QR avulso não quita o boleto: o banco não sabe que aquele PIX se refere a este
    título. Sem conciliação manual, o pagador pode ser cobrado de novo pelo código de barras, ou o
    título ir a protesto já pago.

    O contexto e o `BoletoEmitido` dizem qual é qual — **`vinculado` / `pix_vinculado`**. Se você
    expõe o QR a pagadores, use esse campo para decidir o que rotular.

### Identificando o QR avulso — e conciliando depois

Como o QR avulso não dá baixa, o identificador deixa de ser conveniência e vira **o que torna a
conciliação possível**. São dois campos, com papéis distintos:

| Campo | No payload | Limite | Para quê |
|---|:--:|:--:|---|
| `pix_txid` | 62-05 | 25, `A-Za-z0-9` | **identificar a transação** — costuma aparecer no memo do crédito no extrato |
| `pix_observacao` | 26-02 | 40, sem acentos | descrever a cobrança para quem paga |

**O QR avulso já sai identificado.** Sem `pix_txid`, o campo 62-05 é preenchido com o nosso
número (só `A-Za-z0-9`, cortado em 25) — `txid_do_titulo()`. Deixar isso na lembrança de quem
chama garantiria que uma parte dos boletos saísse sem identificador, e é justamente aí que o
recebimento fica órfão. Para abrir mão de propósito, informe `pix_txid="***"`, que é o *ausente*
do padrão EMV.

O valor também vai, no campo 54 — o pagador não digita, e portanto não digita errado.

!!! tip "Ainda não tem o nosso número?"
    Sem nosso número, o `txid` sai **ausente** (`***`) em vez de derivado: `nosso_numero_formatado()`
    completaria com zeros e ainda calcularia o dígito em cima deles, produzindo um identificador
    plausível e sem significado — que não casa com título nenhum na conciliação.

    E o **QR não depende do boleto**. Ele precisa de chave, nome, cidade e valor; o nosso número é
    exigência do **código de barras**, não do PIX. Para emitir o QR antes de ter o número, use o
    `PixPayload` direto:

    ```python
    from pycobranca.pix import PixPayload, qr_matrix

    payload = PixPayload(
        chave="11222333000181",
        nome="Empresa Exemplo LTDA",
        cidade="SAO PAULO",
        valor="127.50",
        info_adicional="Fatura 2026-0001",
    )
    copia_cola = payload.br_code()
    matriz = qr_matrix(copia_cola)
    ```

    Quando o nosso número chegar, monte o boleto normalmente — aí o `txid` passa a ser derivado e
    a conciliação fica possível.

Isso fecha o ciclo com a [conciliação OFX](13-ofx.md), que casa pelo memo:

```python
titulo = Bancos.find("341")(..., pix_chave="...", pix_txid="NN10912345678")
# o pagador lê o QR e paga; o credito entra no extrato com o txid no memo
resultado = concilia(extrato, ["NN10912345678"])
resultado.conciliadas  # o crédito PIX casado com o título
resultado.pendentes  # os que ainda não apareceram
```

Sem identificador, o recebimento fica órfão no extrato e o boleto parece não pago — que é
exatamente o risco do QR avulso.

O `pix_txid` é validado na composição: fora de `A-Za-z0-9` ou acima de 25 caracteres, levanta
`PixInvalido` aqui, e não vira recusa no banco.

### O caminho vinculado

A biblioteca **não registra** a cobrança: isso é chamada online ao PSP, fora do escopo
([00 — Visão geral](00-visao-geral.md)). Quem registra é você — pela API do banco ou pelo arquivo
retorno, onde o payload volta. Aí basta passá-lo:

```python
boleto = Bancos.find("341")(..., pix_copia_cola=payload_que_o_banco_devolveu)
ctx = boleto.contexto_render()  # ctx["pix"]["vinculado"] is True
```

O payload vai para o QR **exatamente como veio** — reescrevê-lo imprimiria um código que o banco
não reconhece. `pix_copia_cola` tem precedência sobre `pix_chave`, e funciona em **qualquer**
banco: `suporta_pix` restringe a geração local, não o que o banco produziu.

## Componentes

```
pix/
├── payload.py    # BR Code / EMV (copia-e-cola) + CRC16
└── qr.py         # matriz de módulos (qr_matrix) e SVG (qr_svg)
```

## BR Code (EMV)

O payload PIX segue o padrão EMV® QR Code do Banco Central. É uma string estruturada em
campos ID-Length-Value (TLV). Campos essenciais:

| ID | Campo | Observação |
|:--:|-------|-----------|
| 00 | Payload Format Indicator | Fixo `01`. |
| 26 | Merchant Account Information | Contém GUI `br.gov.bcb.pix` + chave + info adicional. |
| 52 | Merchant Category Code | MCC. |
| 53 | Transaction Currency | `986` (BRL). |
| 54 | Transaction Amount | Valor. |
| 58 | Country Code | `BR`. |
| 59 | Merchant Name | Beneficiário. |
| 60 | Merchant City | Cidade. |
| 62 | Additional Data | `txid`. |
| 63 | CRC16 | Checksum (CRC-CCITT). |

O `payload.py` monta a string, calcula o **CRC16-CCITT** e retorna o copia-e-cola.

## QR Code

`qr.py` gera a **matriz de módulos** do QR a partir do payload; o pacote `render/` a desenha
vetorialmente no PDF. A geração é pura Python (sem dependências de sistema).

> **Status: implementado** (`pycobranca/pix/`): payload EMV validado **byte a byte contra o
> exemplo canônico do manual do BCB** (CRC `1D3D`), QR real via `qrcode` (dependência do pacote) e
> round-trip verificado — o QR desenhado no PDF decodifica de volta ao copia-e-cola.

## API real

```python
from pycobranca.pix import PixPayload, qr_matrix, qr_svg

pix = PixPayload(
    chave="11222333000181",  # CNPJ do beneficiário
    nome="Empresa Exemplo LTDA",
    cidade="Sao Paulo",
    valor="127.50",
    txid="PYCOB0001",
)
copia_cola = pix.br_code()  # string EMV com CRC16
matriz = qr_matrix(copia_cola)  # matriz 0/1 (consumida pelo ReportLab)
svg = qr_svg(copia_cola)  # SVG para pré-visualização
```

No boleto, o QR Code (Bolepix) é posicionado na **Ficha de Compensação**, no modelo moderno — veja o exemplo visual em [`boleto-pix.png`](images/screenshots/boleto-pix.png) (saída real do ReportLab).

Ao emitir um boleto de banco com PIX habilitado, o Bolepix é montado automaticamente:

```python
boleto = Bancos.find("341")(..., pix_chave="11222333000181", pix_txid="PYCOB0001")
ctx = boleto.contexto_render()  # pix = {habilitado, copia_cola, qrcode_matrix}
pdf = render_boleto_pdf(ctx, modelo="moderno")  # QR real na ficha
```

## Segmento PIX no CNAB

Na remessa, os bancos com PIX exigem informações adicionais (ex.: segmento específico ou campos
no segmento R do CNAB 240). O subsistema CNAB inclui esses campos quando o boleto carrega dados
de PIX e o banco está em `Bancos.com_pix()`.

## Bancos com PIX

`suporta_pix = True` significa uma coisa precisa: **o segmento PIX do CNAB daquele banco está
implementado** — registro tipo 8 no 400, segmento Y-03 no 240. São eles que levam a chave DICT e o
`txid` ao banco, para que ele registre a cobrança e gere o QR vinculado. Consultável em
`Bancos.com_pix()`; hoje: Banco do Brasil, Santander, Caixa, Bradesco, C6, Itaú e Sicoob.

Nos demais bancos a ausência é de **segmento no layout**, não de capacidade PIX da instituição.
Fechar essa lacuna exige, por banco, o manual definindo o segmento — o mesmo critério de
[15 — Novo banco](15-novo-banco.md). E, em qualquer banco, `pix_copia_cola` já funciona: se você
tem o payload do banco, a biblioteca o imprime.

## Legibilidade do QR impresso

Payload correto não garante QR legível: entre a matriz de módulos e o papel está a rasterização,
onde os módulos caem em fração de pixel. `tests/test_pix_leitura.py` fecha esse ciclo —
**decodifica o QR do PDF renderizado e compara com o payload**, nos dois modelos e em todos os
bancos com PIX.

O que a medição mostra: **de 200 dpi para cima todos leem**; a 150 dpi dois dos sete payloads já
não são lidos. Boleto se imprime a 300 dpi, então a margem é confortável — mas se você gera
pré-visualização em resolução baixa, não a use para conferir leitura.

A matriz sai com `border=0`: a **zona de silêncio** da norma (4 módulos) vem do fundo branco do
boleto, já que o QR é posicionado com folga. Reutilizando `qr_matrix` em outro suporte, reserve
essa margem — sem ela o leitor não isola o símbolo do que estiver ao redor.

## Validação

- **CRC16** conferido em todos os payloads gerados.
- Testes de payload contra exemplos conhecidos (copia-e-cola de referência).
- Validação de tamanho e presença de campos obrigatórios do EMV.
