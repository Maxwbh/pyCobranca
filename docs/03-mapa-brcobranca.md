# 03 — Mapa de recursos

Catálogo dos recursos da **PyCobrança** e onde cada um vive no código. Serve como referência rápida
de cobertura funcional.

## 1. Emissão de boleto

| Recurso | Onde |
|---------|------|
| Geração de PDF (ReportLab) | `render/reportlab.py` |
| Linha digitável | `boleto/linha_digitavel.py` |
| Código de barras | `boleto/codigo_barras.py` |
| Carnê (3 boletos por A4) | `render/reportlab.py` (`render_carne_pdf`) |
| Temização (logo, cor, marca d'água) | opções de `render` |

## 2. Registro de bancos

| Recurso | API |
|---------|-----|
| Listar todos | `Bancos.todos()` |
| Buscar por código | `Bancos.find("756")` |
| Bancos com PIX | `Bancos.com_pix()` |
| Metadados por banco (código, dígito, nome) | atributos de `BancoBase` |

Auto-registro por código FEBRABAN em `bancos/__init__.py`.

## 3. CNAB

| Recurso | Onde |
|---------|------|
| Remessa CNAB 240 | `cnab/cnab240/*` |
| Remessa CNAB 400 | `cnab/cnab400/*` |
| Retorno CNAB 240/400 | `cnab/retorno/*` |
| Segmento PIX na remessa | `cnab/cnab400/pix.py`, `cnab/cnab240/pix.py` |

Layouts declarativos posicionais, testados contra vetores de referência.

## 4. PIX

| Recurso | Onde |
|---------|------|
| BR Code / EMV copia-e-cola | `pix/payload.py` |
| QR Code (Bolepix) | `pix/qr.py` + `render/reportlab.py` |
| Segmento PIX no CNAB | `cnab/*/pix.py` |
| Bancos com PIX | `Bancos.com_pix()` |

## 5. Validação

| Recurso | Onde |
|---------|------|
| Validação de campos por banco | métodos `validar()` em cada `Banco` |
| Dígitos verificadores | `core/dv.py` |
| Validador FEBRABAN independente | `tests/test_validacao_externa.py` |

Cada banco declara suas regras; erros são exceções de domínio em `exceptions.py`.

## 6. Serialização

| Recurso | Onde |
|---------|------|
| `to_dict()` / `to_json()` | `SerializableMixin` |
| Contrato REST (OpenAPI) | `pycobranca/contracts/` |

## Fora de escopo

- Integração direta com APIs proprietárias de bancos (C6/Sicoob) — foco é boleto registrado/CNAB.
- PostScript nativo.
- Parsing de OFX.
