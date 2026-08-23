"""As três fronteiras de quem embute a engine num serviço.

    python examples/11_servico_rest.py

Um serviço REST precisa de três coisas: construir o título a partir do payload
que recebeu, devolver PDF **e** dados numa resposta só, e ler o arquivo de
retorno que chegou por upload. As três são chamadas da biblioteca — nenhuma
precisa ser reescrita do lado de fora.

A PyCobrança continua sem falar HTTP: aqui não há framework, rota nem servidor.
"""

from __future__ import annotations

import json
from base64 import b64encode

from _comum import DADOS, grava, titulo

from pycobranca.cnab.retorno import Retorno
from pycobranca.contracts import boleto_de_api, boleto_para_api, tema_de_api
from pycobranca.exceptions import PyCobrancaError
from pycobranca.render import emite_boleto

#: o que chegaria no corpo de um POST /boleto
REQUISICAO = {
    "bank": "itau",
    "data": {
        "agencia": "0057",
        "conta_corrente": "12345",
        "nosso_numero": "12345678",
        "valor": 1279.50,
        "cedente": "Empresa Exemplo LTDA",
        "documento_cedente": "11.222.333/0001-81",
        "sacado": "Cliente Final da Silva",
        "sacado_documento": "529.982.247-25",
        "carteira": "109",
        "data_vencimento": "2026-09-10",
        # faixa FEBRABAN: informada na emissão porque o desconto já é conhecido
        "desconto_abatimento": 150.00,
        "mora_multa": 8.00,
        # faixa de marca — o renderizador usa outro vocabulário, tema_de_api traduz
        "cor_marca": "#1B4F8A",
        "logo_empresa": "EXEMPLO",
        "rodape_contato": "financeiro@exemplo.com.br · 0800 000 0000",
    },
}


def main() -> None:
    titulo("1. payload do contrato → título")
    boleto = boleto_de_api(REQUISICAO)
    print(f"  banco: {boleto.nome} ({boleto.codigo})")
    print(f"  conta: {boleto.conta} — o contrato chama de 'conta_corrente'")

    titulo("2. PDF e dados numa chamada")
    saida = emite_boleto(boleto, modelo="moderno", tema=tema_de_api(REQUISICAO["data"]))
    grava("11_servico_rest.pdf", saida.pdf)

    resposta = {"pdf_base64": b64encode(saida.pdf).decode()[:24] + "…", **saida.to_dict()}
    print(json.dumps(resposta, indent=2, ensure_ascii=False))

    titulo("3. a ida e volta fecha")
    refeito = boleto_de_api(boleto_para_api(boleto))
    print(f"  código de barras idêntico: {refeito.codigo_barras == boleto.codigo_barras}")

    titulo("4. retorno vindo de upload (bytes, sem arquivo temporário)")
    conteudo = (DADOS / "retorno-itau.ret").read_bytes()
    retorno = Retorno.ler(conteudo)
    print(
        f"  layout {retorno.layout}, banco {retorno.codigo_banco}, "
        f"{len(retorno.registros)} registros"
    )

    titulo("5. erro de contrato é PyCobrancaError como todo o resto")
    try:
        boleto_de_api({"bank": "itau", "data": {"valor": 10}})
    except PyCobrancaError as erro:
        print(f"  {type(erro).__name__}: {erro}")


if __name__ == "__main__":
    main()
