"""``openapi_de`` — cola os paths de quem consome com os schemas daqui.

A PyCobrança não tem endpoints, então não publica um OpenAPI completo: seria
inventar rotas que ela não serve. O que ela tem são os **schemas de dados**,
versionados junto com o código que os implementa.

O valor do helper é evitar a cópia. Um schema copiado para o repositório da API
envelhece em silêncio quando a biblioteca sobe de versão — o mesmo tipo de
divergência que este projeto trata como defeito.
"""

from __future__ import annotations

import pytest

from pycobranca import __version__
from pycobranca.contracts import CONTRATO, ErroDeContrato, openapi_de

PATHS = {
    "/boletos": {
        "post": {
            "summary": "Emite um boleto",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["bank", "data"],
                            "properties": {
                                "bank": {"type": "string"},
                                "data": {"$ref": "#/components/schemas/BoletoData"},
                            },
                        }
                    }
                },
            },
            "responses": {"201": {"description": "PDF e dados"}},
        }
    }
}


def test_documento_tem_as_tres_partes() -> None:
    """Paths de quem chama, schemas da biblioteca, e o cabeçalho por cima."""
    doc = openapi_de(PATHS, info={"title": "cobranca_api", "version": "2.0.0"})
    assert doc["openapi"] == "3.0.3"
    assert doc["info"]["title"] == "cobranca_api"
    assert doc["paths"] == PATHS
    assert set(doc["components"]["schemas"]) == set(CONTRATO["schemas"])


def test_a_versao_da_biblioteca_fica_carimbada() -> None:
    """Quem abre o Swagger precisa saber de qual engine veio o contrato.

    Sem isso, um schema desatualizado é indistinguível de um atual.
    """
    doc = openapi_de(PATHS)
    assert doc["info"]["x-pycobranca"] == __version__
    assert __version__ in doc["info"]["description"]


def test_a_descricao_de_quem_chama_e_preservada() -> None:
    doc = openapi_de(PATHS, info={"description": "API interna de cobrança."})
    assert doc["info"]["description"].startswith("API interna de cobrança.")
    assert __version__ in doc["info"]["description"]


def test_referencia_aos_schemas_resolve() -> None:
    """O ``$ref`` do path tem de apontar para algo que existe no documento."""
    doc = openapi_de(PATHS)
    ref = doc["paths"]["/boletos"]["post"]["requestBody"]["content"]["application/json"]["schema"][
        "properties"
    ]["data"]["$ref"]
    assert ref == "#/components/schemas/BoletoData"
    assert ref.rsplit("/", 1)[-1] in doc["components"]["schemas"]


def test_schemas_proprios_sao_somados() -> None:
    doc = openapi_de(PATHS, schemas={"ErroDaMinhaApi": {"type": "object"}})
    assert "ErroDaMinhaApi" in doc["components"]["schemas"]
    assert "BoletoData" in doc["components"]["schemas"]


def test_colisao_de_nome_e_recusada() -> None:
    """Sobrescrever ``BoletoData`` em silêncio devolveria o problema evitado.

    Quem redefine um schema da biblioteca acha que documentou a API e na verdade
    documentou outra coisa — e a engine continua aceitando o formato antigo.
    """
    with pytest.raises(ErroDeContrato) as erro:
        openapi_de(PATHS, schemas={"BoletoData": {"type": "object"}})
    assert "BoletoData" in str(erro.value)


def test_mutar_o_documento_nao_corrompe_o_contrato_do_pacote() -> None:
    """``CONTRATO`` é um dict de módulo, compartilhado por todo o processo.

    Sem cópia, um consumidor que ajustasse o schema no seu documento mudaria o
    contrato que a engine usa para validar — em todo o processo, sem aviso.
    """
    doc = openapi_de(PATHS)
    doc["components"]["schemas"]["BoletoData"]["properties"]["valor"]["type"] = "sabotado"
    assert CONTRATO["schemas"]["BoletoData"]["properties"]["valor"]["type"] != "sabotado"


def test_servers_e_opcional() -> None:
    assert "servers" not in openapi_de(PATHS)
    doc = openapi_de(PATHS, servers=[{"url": "https://api.exemplo.com.br"}])
    assert doc["servers"] == [{"url": "https://api.exemplo.com.br"}]


def test_documento_serializa_para_json_e_yaml() -> None:
    """O helper devolve dados puros: quem serializa é quem publica."""
    import json

    doc = openapi_de(PATHS, info={"title": "cobranca_api", "version": "1.0.0"})
    assert json.loads(json.dumps(doc)) == doc  # sem objetos não serializáveis
