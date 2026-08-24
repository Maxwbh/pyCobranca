"""As três fronteiras que todo consumidor da biblioteca reescrevia.

Um serviço que embute a PyCobrança precisa de três coisas que ela não oferecia:
receber um ``BoletoData`` e construir o título (``boleto_de_api``), devolver PDF
e dados de uma vez (``emite_boleto``) e ler um retorno vindo de upload
(``Retorno.ler`` com bytes). Cada uma era reescrita fora, e errar o mapeamento
não dava erro — dava boleto errado.

O teste que importa é o de **ida e volta nos 18 bancos**: sem os campos
específicos de banco no contrato, o Citibank voltava com ``portfolio`` vazio e
um código de barras diferente, estruturalmente válido e com destino errado.
"""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pytest
from exemplos_boletos import EXEMPLOS

from pycobranca.cnab.retorno import Retorno
from pycobranca.contracts import (
    CAMPOS_POR_BANCO,
    CONTRATO,
    boleto_de_api,
    boleto_para_api,
    tema_de_api,
)
from pycobranca.contracts.contrato_rest import ErroDeContrato
from pycobranca.exceptions import BancoNaoRegistrado, ModeloInvalido, RetornoInvalido

# ---- fronteira 1: BoletoData -> título ------------------------------------


@pytest.mark.parametrize("nome", sorted(EXEMPLOS))
def test_ida_e_volta_reconstroi_o_mesmo_titulo(nome: str) -> None:
    """O payload precisa carregar tudo que o campo livre consome.

    Falhava em 7 dos 18: BNB, Banestes e Unicred levantavam (campo livre com 24
    dígitos), BRB, Safra e Sicredi barravam na validação — e o **Citibank
    passava calado**, com o boleto errado.
    """
    original = EXEMPLOS[nome]["boleto"]()
    refeito = boleto_de_api(boleto_para_api(original))
    assert refeito.codigo_barras == original.codigo_barras
    assert refeito.linha_digitavel == original.linha_digitavel
    assert refeito.nosso_numero_formatado() == original.nosso_numero_formatado()


def test_campos_por_banco_estao_no_schema() -> None:
    props = CONTRATO["schemas"]["BoletoData"]["properties"]
    ausentes = [c for c in CAMPOS_POR_BANCO if c not in props]
    assert not ausentes, f"campo consumido pelo campo livre e fora do contrato: {ausentes}"


def test_agencia_e_conta_nao_sao_obrigatorias() -> None:
    """Santander identifica o cedente pelo convênio; a Caixa, pelo código do
    beneficiário. Exigi-las no schema tornava esses dois inexprimíveis."""
    req = CONTRATO["schemas"]["BoletoData"]["required"]
    assert "agencia" not in req
    assert "conta_corrente" not in req


def test_traduz_os_nomes_que_divergem() -> None:
    """``documento_cedente``/``cedente_documento`` inverte as palavras."""
    boleto = boleto_de_api(
        {
            "bank": "itau",
            "data": {
                "agencia": "0057",
                "conta_corrente": "12345",
                "nosso_numero": "12345678",
                "valor": 127.50,
                "cedente": "EMPRESA EXEMPLO LTDA",
                "documento_cedente": "11.222.333/0001-81",
                "sacado": "CLIENTE LTDA",
                "sacado_documento": "529.982.247-25",
                "carteira": "109",
                "data_vencimento": "2026-08-15",
            },
        }
    )
    assert boleto.conta == "12345"
    assert boleto.cedente_documento == "11.222.333/0001-81"
    assert boleto.data_vencimento == date(2026, 8, 15)  # ISO virou date


def test_instrucoes_do_contrato_viram_a_lista_da_engine() -> None:
    dados = boleto_para_api(EXEMPLOS["itau"]["boleto"]())["data"]
    dados["instrucao1"] = "Não receber após o vencimento."
    dados["instrucao2"] = "Multa de 2%."
    boleto = boleto_de_api({"bank": "itau", "data": dados})
    assert boleto.instrucoes == ["Não receber após o vencimento.", "Multa de 2%."]


@pytest.mark.parametrize(
    ("rotulo", "muda"),
    [
        ("campo inventado", {"campo_inventado": "x"}),
        ("erro de digitação", {"nosso_numeroo": "12345678"}),
        ("data em formato brasileiro", {"data_vencimento": "15/08/2026"}),
        ("data impossível", {"data_documento": "2026-13-45"}),
        ("valor booleano", {"valor": True}),
    ],
)
def test_entrada_ruim_vira_erro_de_contrato_nomeando_o_campo(rotulo, muda) -> None:
    """A fronteira existe para não deixar ``TypeError``/``ValueError`` escaparem.

    ``additionalProperties`` é permissivo, então chave estranha atravessa o
    validador e chegava ao construtor como ``TypeError``; data fora do ISO
    virava ``ValueError`` de ``fromisoformat``, sem dizer qual campo; e ``bool``
    é subclasse de ``int``, então ``True`` passava por ``number`` e explodia em
    ``Decimal("True")``. Nenhum dos três era ``PyCobrancaError``.
    """
    dados = boleto_para_api(EXEMPLOS["itau"]["boleto"]())["data"]
    with pytest.raises(ErroDeContrato) as capturado:
        boleto_de_api({"bank": "itau", "data": {**dados, **muda}})
    campo = next(iter(muda))
    assert campo in str(capturado.value), f"a mensagem não nomeia {campo!r}"


def test_bank_nao_hasheavel_nao_derruba_a_chamada() -> None:
    """``bank`` vem de JSON e pode chegar como lista — ``dict.get`` levantaria."""
    dados = boleto_para_api(EXEMPLOS["itau"]["boleto"]())["data"]
    with pytest.raises(BancoNaoRegistrado):
        boleto_de_api({"bank": ["itau"], "data": dados})


def test_tema_precisa_ser_dicionario() -> None:
    pytest.importorskip("reportlab")
    from pycobranca.render import emite_boleto

    with pytest.raises(ModeloInvalido):
        emite_boleto(EXEMPLOS["itau"]["boleto"](), tema="azul")


@pytest.mark.parametrize("modelo", ["art-deco", "", None, 0, [], {}, ("moderno",)])
def test_modelo_estranho_vira_modelo_invalido(modelo) -> None:
    """O nome vem de JSON: lista e dicionário levantariam ``TypeError`` no
    acesso ao registro, antes de o ``except KeyError`` ter chance."""
    pytest.importorskip("reportlab")
    from pycobranca.render import emite_boleto

    with pytest.raises(ModeloInvalido):
        emite_boleto(EXEMPLOS["itau"]["boleto"](), modelo=modelo)


def test_campos_de_apresentacao_nao_quebram_a_construcao() -> None:
    """``cor_marca``, ``itens``, ``emv``… não são do construtor e não podem
    chegar nele — mas também não podem derrubar a chamada."""
    dados = boleto_para_api(EXEMPLOS["itau"]["boleto"]())["data"]
    dados.update(
        {
            "cor_marca": "#1B4F8A",
            "logo_empresa": "EXEMPLO",
            "emv": "0002010102…",
            "fonte_ttf": "Inter.ttf",
            "itens": [{"descricao": "Mensalidade", "valor": 99.9}],
        }
    )
    assert boleto_de_api({"bank": "itau", "data": dados}).codigo_barras


# ---- tema: o vocabulário que o renderizador usa ---------------------------


def test_tema_de_api_traduz_o_vocabulario() -> None:
    tema = tema_de_api(
        {
            "cor_marca": "#1B4F8A",
            "logo_empresa": "EXEMPLO",
            "rodape_contato": "0800 000 0000",
            "parcela_atual": 3,
            "total_parcelas": 12,
        }
    )
    assert tema == {
        "habilitado": True,
        "cor": "#1B4F8A",
        "logo_texto": "EXEMPLO",
        "empresa": "EXEMPLO",  # sem campo próprio no contrato, herda o logo
        "rodape": "0800 000 0000",
        "parcela_texto": "Parcela 3/12",
    }


def test_sem_campos_de_tema_nao_ha_faixa() -> None:
    assert tema_de_api({"agencia": "0057"}) is None


# ---- fronteira 2: PDF e dados numa chamada --------------------------------


def _emite(**extra):
    pytest.importorskip("reportlab")
    from pycobranca.bancos import Bancos
    from pycobranca.render import emite_boleto

    Banco = Bancos.find("341")
    boleto = Banco(
        valor="1279.50",
        cedente="EMPRESA EXEMPLO LTDA",
        cedente_documento="11.222.333/0001-81",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 9, 10),
        sacado="CLIENTE LTDA",
        sacado_documento="529.982.247-25",
        **extra,
    )
    return boleto, emite_boleto(boleto)


def test_emite_boleto_traz_pdf_e_dados_juntos() -> None:
    boleto, saida = _emite()
    assert saida.pdf.startswith(b"%PDF")
    assert saida.linha_digitavel == boleto.linha_digitavel
    assert saida.codigo_barras == boleto.codigo_barras
    assert saida.nosso_numero == boleto.nosso_numero_formatado()


def test_emite_boleto_monta_o_titulo_uma_vez_so() -> None:
    """O ponto da fronteira: buscar os derivados de volta no objeto roda
    ``validar()`` e monta o código de barras quatro vezes por requisição."""
    pytest.importorskip("reportlab")
    import pycobranca.bancos.base as base
    from pycobranca.render import emite_boleto

    chamadas = {"n": 0}
    original = base.montar_codigo_barras

    def conta(*a, **k):
        chamadas["n"] += 1
        return original(*a, **k)

    base.montar_codigo_barras = conta
    try:
        boleto, _ = _emite()
        chamadas["n"] = 0
        emite_boleto(boleto)
        de_uma_vez = chamadas["n"]

        chamadas["n"] = 0
        ctx = boleto.contexto_render()
        _ = (boleto.linha_digitavel, boleto.codigo_barras, boleto.nosso_numero_formatado())
        separado = chamadas["n"]
    finally:
        base.montar_codigo_barras = original

    assert de_uma_vez < separado, f"{de_uma_vez} montagens contra {separado}"
    assert ctx  # o contexto continua acessível a quem precisa dele


def test_to_dict_nao_carrega_o_pdf() -> None:
    _, saida = _emite()
    dados = saida.to_dict()
    assert "pdf" not in dados
    assert dados["linha_digitavel"] == saida.linha_digitavel


def test_pix_copia_cola_so_quando_ha_pix() -> None:
    _, sem = _emite()
    assert sem.pix_copia_cola is None
    _, com = _emite(pix_chave="11222333000181", pix_txid="PEDIDO123")
    assert com.pix_copia_cola and com.pix_copia_cola.startswith("0002")


def test_totalizadores_saem_vazios_porque_a_faixa_e_do_caixa() -> None:
    """``BoletoEmitido`` descreve o papel, e no papel a faixa vai em branco.

    Devolver ``"150,00"`` aqui faria o consumidor exibir, na tela ou no e-mail,
    um encargo que o boleto impresso não traz — e o total de um cálculo que
    ainda não aconteceu.
    """
    _, saida = _emite(desconto_abatimento="150.00", mora_multa="8.00")
    assert set(saida.totalizadores.values()) == {""}


def test_tema_chega_ao_desenho() -> None:
    pytest.importorskip("reportlab")
    from pycobranca.render import emite_boleto

    boleto, sem = _emite()
    com = emite_boleto(boleto, tema=tema_de_api({"cor_marca": "#1B4F8A", "marca_dagua": "X"}))
    assert len(com.pdf) > len(sem.pdf)  # faixa e marca d'água acrescentam desenho


# ---- fronteira 3: retorno de upload ---------------------------------------

_RET = Path(__file__).parent / "fixtures" / "retorno" / "CNAB400ITAU.RET"


def test_retorno_le_de_caminho_bytes_e_file_like() -> None:
    """Um serviço recebe upload, não caminho — como ``Extrato.ler`` já aceitava."""
    bruto = _RET.read_bytes()
    de_caminho = Retorno.ler(_RET)
    de_bytes = Retorno.ler(bruto)
    de_arquivo = Retorno.ler(io.BytesIO(bruto))

    assert de_caminho.codigo_banco == de_bytes.codigo_banco == de_arquivo.codigo_banco
    assert len(de_caminho.registros) == len(de_bytes.registros) == len(de_arquivo.registros)
    assert [r.nosso_numero for r in de_bytes.registros] == [
        r.nosso_numero for r in de_caminho.registros
    ]


def test_bytes_com_acento_latin1_nao_deslocam_o_registro() -> None:
    """O CNAB é posicional: byte perdido na decodificação desloca tudo à direita.

    Latin-1 mapeia os 256 bytes, então nunca levanta nem substitui — que é o
    motivo de ela ser a decodificação certa aqui, e não UTF-8 com ``replace``.
    """
    bruto = _RET.read_bytes()
    # injeta um acento no nome do sacado da primeira linha de detalhe
    linhas = bruto.split(b"\r\n") if b"\r\n" in bruto else bruto.split(b"\n")
    detalhe = bytearray(linhas[1])
    detalhe[40:51] = b"JOS\xc9 A\xc7\xdaCAR"  # JOSÉ AÇÚCAR em latin-1
    linhas[1] = bytes(detalhe)
    remendado = b"\r\n".join(linhas)

    lido = Retorno.ler(remendado)
    referencia = Retorno.ler(bruto)
    assert len(lido.registros) == len(referencia.registros)
    # o acento ocupa 1 byte e 1 caractere: as posições seguintes não se movem
    assert lido.registros[0].nosso_numero == referencia.registros[0].nosso_numero
    assert lido.registros[0].valor_titulo == referencia.registros[0].valor_titulo


def test_retorno_vazio_continua_levantando() -> None:
    with pytest.raises(RetornoInvalido):
        Retorno.ler(b"   \n  \n")
