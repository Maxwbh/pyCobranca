# Fixtures de retorno externos

Arquivos de retorno CNAB **reais**, de terceiros, usados como testes de regressão
independentes (além dos fixtures próprios em `tests/fixtures/retorno/`). Servem para
exercitar o parser e o validador estrutural (`tests/test_retorno_externos.py`) contra
dados que não geramos.

| Arquivo | Banco | Layout |
|---------|-------|--------|
| `caixa_cnab240.ret`   | Caixa (104)   | CNAB 240 |
| `hsbc_cnab400.ret`    | HSBC (399)    | CNAB 400 |
| `sicredi_cnab400.ret` | Sicredi (748) | CNAB 400 |

## Origem e licença

Extraídos da suíte de testes do projeto **laravel-boleto**, sob **licença MIT**:

- Repositório: https://github.com/eduardokum/laravel-boleto
- Caminho original: `tests/Retorno/files/{cnab400,cnab240}/`

```
MIT License

Copyright (c) 2016 Eduardo Gusmão (https://github.com/eduardokum)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
