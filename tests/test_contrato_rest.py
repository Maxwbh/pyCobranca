"""Testes de contrato REST (OpenAPI 3.0).

Garantem que os artefatos da engine (boleto, remessa, retorno) serializam para
os schemas do OpenAPI 3.0 — validados pelo contrato vendorizado
em ``pycobranca/contracts/contrato_rest.json``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from pycobranca.bancos import Bancos
from pycobranca.cnab.retorno import Retorno
from pycobranca.contracts import (
    SLUG_POR_CODIGO,
    boleto_para_api,
    pagamento_para_api,
    remessa_para_api,
    retorno_item_para_api,
    valida_contrato,
)
from pycobranca.contracts.contrato_rest import ErroDeContrato

FIXTURES = Path(__file__).parent / "fixtures"


def _boleto(cls):
    return cls(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="12345678000190",
        agencia="1234",
        conta="56789",
        carteira=(cls.carteiras[0] if getattr(cls, "carteiras", None) else "01"),
        nosso_numero="12345678",
        numero_documento="NF-2026-001",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
        convenio="1234567",
    )


@pytest.mark.parametrize("cls", Bancos.todos(), ids=lambda c: c.codigo)
def test_boleto_serializa_no_contrato_boletodata(cls) -> None:
    # Sem ``.get(cls.codigo, cls.codigo)``: o padrão devolvia o próprio código
    # quando o slug faltava, e a asserção virava ``"077" == "077"``. A guarda
    # tinha um atalho exatamente no caso que ela existe para pegar — o Inter
    # ficou fora de ``SLUG_POR_CODIGO`` e nenhum teste acusou.
    payload = boleto_para_api(_boleto(cls))
    assert payload["bank"] == SLUG_POR_CODIGO[cls.codigo]
    valida_contrato(payload["data"], "BoletoData")


def test_todo_banco_do_registro_tem_slug_no_contrato() -> None:
    """O contrato REST não pode conhecer menos bancos que o registro.

    Um banco sem slug é invisível para quem consome a API pelo nome: a ida
    devolvia o código no lugar do slug e a volta recusava o slug documentado —
    as duas pontas com verdades diferentes, e nenhuma delas errada o bastante
    para levantar.
    """
    sem_slug = [f"{b.codigo} ({b.nome})" for b in Bancos.todos() if b.codigo not in SLUG_POR_CODIGO]
    assert sem_slug == [], f"bancos sem slug em SLUG_POR_CODIGO: {sem_slug}"


def test_slug_nunca_e_o_proprio_codigo() -> None:
    """Slug igual ao código é o sintoma de quem só preencheu para calar o teste."""
    iguais = [cod for cod, slug in SLUG_POR_CODIGO.items() if slug == cod]
    assert iguais == []


@pytest.mark.parametrize("cls", Bancos.todos(), ids=lambda c: c.codigo)
def test_o_slug_devolvido_na_ida_e_aceito_na_volta(cls) -> None:
    """Fecha o ciclo pelo **slug**, não pelo código.

    A ida e volta já era testada, mas passava pelo valor que a ida devolvia —
    e com o Inter esse valor era ``"077"``, que a volta aceita por tolerância.
    Testar o par consigo mesmo não prova que o slug documentado funciona.
    """
    from pycobranca.contracts import boleto_de_api

    slug = SLUG_POR_CODIGO[cls.codigo]
    original = _boleto(cls)
    payload = boleto_para_api(original)
    assert payload["bank"] == slug
    assert boleto_de_api({"bank": slug, "data": payload["data"]}).codigo == cls.codigo


def test_boleto_data_tem_campos_obrigatorios() -> None:
    from pycobranca.bancos.itau import Itau

    data = boleto_para_api(_boleto(Itau))["data"]
    for campo in ("agencia", "conta_corrente", "nosso_numero", "valor", "cedente"):
        assert campo in data
    assert isinstance(data["valor"], float)


def test_pagamento_serializa_no_contrato() -> None:
    from pycobranca.cnab import Pagamento

    pagamento = Pagamento(
        valor=199.90,
        data_vencimento=date(2026, 8, 15),
        nosso_numero="12345678",
        numero="DOC0001",
        documento_sacado="52998224725",
        nome_sacado="Cliente Final",
        endereco_sacado="Rua das Flores, 100",
        bairro_sacado="Centro",
        cep_sacado="30110000",
        cidade_sacado="Belo Horizonte",
        uf_sacado="MG",
    )
    dados = pagamento_para_api(pagamento)
    valida_contrato(dados, "Pagamento")
    assert dados["nome_sacado"] == "Cliente Final"
    assert dados["numero_documento"] == "DOC0001"
    assert isinstance(dados["valor"], float)


def test_remessa_serializa_no_contrato_remessarequest() -> None:
    from pycobranca.cnab import Pagamento, RemessaItau400

    remessa = RemessaItau400(
        pagamentos=[
            Pagamento(
                valor=199.90,
                data_vencimento=date(2026, 8, 15),
                nosso_numero="12345678",
                numero="DOC0001",
                documento_sacado="52998224725",
                nome_sacado="Cliente Final",
                endereco_sacado="Rua das Flores, 100",
                bairro_sacado="Centro",
                cep_sacado="30110000",
                cidade_sacado="Belo Horizonte",
                uf_sacado="MG",
            )
        ],
        empresa_mae="Empresa Exemplo LTDA",
        documento_cedente="11222333000181",
        agencia="0057",
        conta_corrente="12345",
        digito_conta="7",
        carteira="109",
    )
    dados = remessa_para_api(remessa)
    valida_contrato(dados, "RemessaRequest")  # também valida cada Pagamento via $ref
    assert dados["pagamentos"][0]["nosso_numero"] == "12345678"
    assert isinstance(dados["sequencial_remessa"], int)


def test_retorno_item_serializa_no_contrato() -> None:
    retorno = Retorno.ler(FIXTURES / "retorno" / "CNAB400ITAU.RET")
    item = retorno_item_para_api(retorno.registros[0], layout=retorno.layout)
    valida_contrato(item, "RetornoItem")
    # centavos -> reais em float
    assert item["valor_titulo"] == 40.00
    assert item["valor_pago"] == 37.90
    assert item["motivo_ocorrencia"] == "Liquidação normal"


def test_retorno_todos_os_itens_validos() -> None:
    for arq in ("CNAB400BRADESCO.RET", "CNAB240SICOOB.RET"):
        retorno = Retorno.ler(FIXTURES / "retorno" / arq)
        for registro in retorno.registros:
            item = retorno_item_para_api(registro, layout=retorno.layout)
            valida_contrato(item, "RetornoItem")


def test_validador_rejeita_obrigatorio_ausente() -> None:
    with pytest.raises(ErroDeContrato):
        valida_contrato({"agencia": "1234"}, "BoletoData")


def test_validador_rejeita_tipo_incorreto() -> None:
    dados = {
        "agencia": "1234",
        "conta_corrente": "56789",
        "nosso_numero": "1",
        "valor": "127.50",  # deveria ser number, não string
        "cedente": "X",
        "documento_cedente": "1",
        "sacado": "Y",
        "sacado_documento": "1",
    }
    with pytest.raises(ErroDeContrato):
        valida_contrato(dados, "BoletoData")


def test_todo_alias_do_contrato_existe_no_schema() -> None:
    """O mapa de nomes e o schema OpenAPI têm de descrever o mesmo contrato.

    São dois lugares distintos — ``NOMES_DO_CONTRATO`` traduz nome externo para atributo,
    o JSON descreve o que a API aceita. Um campo novo em só um dos dois passa
    despercebido: ou o cliente gerado do schema não conhece o campo, ou a API
    aceita algo que a documentação não anuncia.
    """
    from pycobranca.contracts.contrato_rest import CONTRATO, NOMES_DO_CONTRATO

    propriedades = set(CONTRATO["schemas"]["BoletoData"]["properties"])
    ausentes = sorted(set(NOMES_DO_CONTRATO) - propriedades)
    assert ausentes == [], f"aliases fora do schema OpenAPI: {ausentes}"


def test_campos_de_pix_do_boleto_estao_no_contrato() -> None:
    """Os dois caminhos do QR precisam trafegar por JSON.

    Sem ``pix_copia_cola`` no contrato, quem expõe a biblioteca por REST não
    consegue receber o payload que o banco devolveu — sobra só o QR estático,
    que não liquida o título.
    """
    from pycobranca.contracts.contrato_rest import CONTRATO

    propriedades = CONTRATO["schemas"]["BoletoData"]["properties"]
    assert "pix_copia_cola" in propriedades
    assert "pix_observacao" in propriedades
    assert propriedades["txid"]["maxLength"] == 25  # limite do padrão EMV


def test_retorno_item_traduz_a_ocorrencia_pelo_banco() -> None:
    """O tradutor do contrato precisa saber de que banco veio o registro.

    ``descreve_ocorrencia`` ganhou o parâmetro ``banco`` porque há código que
    inverte de sentido — e o serializador da API não o repassava. No retorno real
    do Safra, o ``40`` saía como *"Baixa por ter sido liquidado"* (o padrão
    FEBRABAN) quando o manual do banco diz **baixa de título protestado**. Título
    pago contra título protestado, numa conciliação, com o rótulo plausível.
    """
    retorno = Retorno.ler(FIXTURES / "retorno_safra_cnab400.ret")
    assert retorno.codigo_banco == "422"
    registro = next(r for r in retorno.registros if r.codigo_ocorrencia == "40")

    sem_banco = retorno_item_para_api(registro, layout=retorno.layout)
    com_banco = retorno_item_para_api(registro, layout=retorno.layout, banco=retorno.codigo_banco)

    assert sem_banco["motivo_ocorrencia"] == "Baixa por ter sido liquidado"
    assert com_banco["motivo_ocorrencia"] == "Baixa de título protestado"
    valida_contrato(com_banco, "RetornoItem")


def test_retorno_item_do_inter_nao_descreve_edicao_como_protesto() -> None:
    """Os três códigos do Inter que colidem com a FEBRABAN, pelo caminho da API."""
    from pycobranca.cnab.retorno.base import RegistroRetorno

    esperado = {
        "07": ("Liquidação por conta/parcial", "Cancelado"),
        "15": ("Liquidação em cartório", "Alteração do valor nominal do título realizada"),
        "16": (
            "Confirmação de recebimento de instrução de protesto",
            "Alteração do valor nominal e da data de vencimento realizada",
        ),
    }
    for codigo, (padrao, inter) in esperado.items():
        registro = RegistroRetorno(codigo_ocorrencia=codigo)
        assert retorno_item_para_api(registro, "400")["motivo_ocorrencia"] == padrao
        assert retorno_item_para_api(registro, "400", "077")["motivo_ocorrencia"] == inter
