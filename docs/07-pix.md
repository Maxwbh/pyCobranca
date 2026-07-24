# 07 — PIX / Bolepix

O **Bolepix** é o boleto híbrido: um boleto tradicional com um QR Code PIX impresso, permitindo
pagamento por leitura do código ou pela linha digitável. A PyCobrança implementa a geração do
payload PIX (BR Code), o QR Code, e o segmento PIX no CNAB de remessa.

## Componentes

```
pix/
├── payload.py    # BR Code / EMV (copia-e-cola)
└── qrcode.py     # geração da imagem do QR Code
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

`qrcode.py` gera a imagem do QR Code a partir do payload, para embutir no PDF do boleto
(`render/pdf.py`). A geração é pura Python (sem dependências de sistema).

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

No boleto, o QR Code (Bolepix) é posicionado na **Ficha de Compensação**, no modelo moderno — veja o exemplo visual em [`exemplos/boleto-demo.html`](exemplos/boleto-demo.html).

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

A capacidade é declarada por banco (`suporta_pix = True`) e consultável via
`Bancos.com_pix()`. Bancos-alvo prioritários com PIX: **Banco do Brasil, Bradesco, Itaú,
Santander, Caixa** (ver [05 — Bancos](05-bancos-suportados.md)).

## Validação

- **CRC16** conferido em todos os payloads gerados.
- Testes de payload contra exemplos conhecidos (copia-e-cola de referência).
- Validação de tamanho e presença de campos obrigatórios do EMV.
