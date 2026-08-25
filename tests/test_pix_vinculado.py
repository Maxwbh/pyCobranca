"""O QR do PIX tem duas naturezas, e confundi-las custa dinheiro.

O **Bolepix** de verdade é um QR **dinâmico**, gerado pelo banco no registro da
cobrança, que compartilha o identificador com o título — é isso que dá a baixa
automática e impede pagamento em duplicidade.

Um BR Code **estático**, montado da chave, é outra coisa: paga a chave, mas o
banco não sabe que aquele PIX quita este boleto. O título fica em aberto, e daí
sai segunda cobrança pelo código de barras ou protesto de título já pago.

A biblioteca faz os dois, e o contexto diz qual — é o que estes testes prendem.
"""

from __future__ import annotations

from datetime import date

import pytest

from pycobranca.bancos import Bancos
from pycobranca.exceptions import BoletoInvalido

#: Payload como o banco devolve: campo 25 (*location*), não a chave no campo 26.
PAYLOAD_DO_BANCO = (
    "00020101021226880014br.gov.bcb.pix2566qrcodepix.bb.com.br/pix/v2/abc123XYZ"
    "5204000053039865802BR5913EMPRESA TESTE6008BRASILIA62070503***6304ABCD"
)


def boleto(**kwargs):
    dados = dict(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        cedente_cidade="SAO PAULO",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    dados.update(kwargs)
    return Bancos.find("341")(**dados)


def test_payload_do_banco_vai_no_qr_como_veio() -> None:
    """Reescrever o payload do banco imprimiria um QR que ele não conhece."""
    pix = boleto(pix_copia_cola=PAYLOAD_DO_BANCO).contexto_render()["pix"]
    assert pix["habilitado"] is True
    assert pix["vinculado"] is True
    assert pix["copia_cola"] == PAYLOAD_DO_BANCO


def test_chave_monta_payload_estatico_e_o_contexto_avisa() -> None:
    """O QR da chave é pagável, mas não liquida — ``vinculado`` diz isso."""
    pix = boleto(pix_chave="11222333000181").contexto_render()["pix"]
    assert pix["habilitado"] is True
    assert pix["vinculado"] is False
    assert "br.gov.bcb.pix" in pix["copia_cola"]


def test_payload_do_banco_tem_precedencia_sobre_a_chave() -> None:
    """Com os dois informados, vale o do banco.

    Se o banco já registrou a cobrança e devolveu o payload, montar outro aqui
    trocaria um QR que liquida por um que não liquida — exatamente o defeito.
    """
    pix = boleto(pix_chave="11222333000181", pix_copia_cola=PAYLOAD_DO_BANCO).contexto_render()[
        "pix"
    ]
    assert pix["copia_cola"] == PAYLOAD_DO_BANCO
    assert pix["vinculado"] is True


def test_banco_sem_segmento_pix_aceita_payload_do_banco() -> None:
    """``suporta_pix`` gate a geração local, não o payload que o banco produziu.

    O Banrisul não tem segmento PIX implementado no CNAB, mas se o beneficiário
    obteve o payload por outro canal, imprimi-lo é legítimo — quem o gerou foi o
    banco.
    """
    banrisul = Bancos.find("041")(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="1102",
        conta="12345678",
        convenio="9000150",
        digito_convenio="46",
        carteira="2",
        nosso_numero="22832563",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
        pix_copia_cola=PAYLOAD_DO_BANCO,
    )
    pix = banrisul.contexto_render()["pix"]
    assert pix["habilitado"] is True
    assert pix["vinculado"] is True


def test_chave_em_banco_sem_pix_continua_recusada() -> None:
    """A geração local segue restrita aos bancos com segmento PIX."""
    with pytest.raises(BoletoInvalido):
        Bancos.find("041")(
            valor="127.50",
            cedente="Empresa Exemplo LTDA",
            cedente_documento="11222333000181",
            agencia="1102",
            conta="12345678",
            convenio="9000150",
            digito_convenio="46",
            carteira="2",
            nosso_numero="22832563",
            data_vencimento=date(2026, 8, 15),
            sacado="Cliente Final da Silva",
            sacado_documento="52998224725",
            pix_chave="11222333000181",
        ).contexto_render()


def test_sem_pix_nenhum_o_contexto_nao_promete_nada() -> None:
    pix = boleto().contexto_render()["pix"]
    assert pix == {"habilitado": False}


def test_boleto_emitido_carrega_a_natureza_do_qr() -> None:
    """Quem consome o resultado precisa saber se o QR liquida — não só que existe."""
    pytest.importorskip("reportlab")
    from pycobranca.render import emite_boleto

    vinculado = emite_boleto(boleto(pix_copia_cola=PAYLOAD_DO_BANCO))
    avulso = emite_boleto(boleto(pix_chave="11222333000181"))
    sem_pix = emite_boleto(boleto())

    assert vinculado.pix_vinculado is True
    assert avulso.pix_vinculado is False
    assert sem_pix.pix_vinculado is None
    assert vinculado.to_dict()["pix_vinculado"] is True


def test_payload_do_banco_trafega_no_contrato_rest() -> None:
    """Ida e volta: o payload não pode se perder ao virar JSON e voltar."""
    from pycobranca.contracts import boleto_de_api, boleto_para_api

    payload = boleto_para_api(boleto(pix_copia_cola=PAYLOAD_DO_BANCO))
    assert payload["data"]["pix_copia_cola"] == PAYLOAD_DO_BANCO
    assert boleto_de_api(payload).pix_copia_cola == PAYLOAD_DO_BANCO


# --- identificadores no QR avulso: é o que torna a conciliação possível ------


def test_txid_e_observacao_entram_no_payload_estatico() -> None:
    """Dois campos distintos, com papéis distintos.

    O ``txid`` (62-05) identifica a transação e é o que costuma aparecer no
    extrato; a observação (26-02) descreve a cobrança para quem paga.
    """
    pix = boleto(
        pix_chave="11222333000181",
        pix_txid="NN10912345678",
        pix_observacao="Fatura 2026-0001",
    ).contexto_render()["pix"]
    assert "NN10912345678" in pix["copia_cola"]
    assert "Fatura 2026-0001" in pix["copia_cola"]


def test_txid_recusa_o_que_o_padrao_nao_aceita() -> None:
    """``A-Za-z0-9``, até 25 — barra na composição, não no banco."""
    from pycobranca.pix import PixInvalido

    with pytest.raises(PixInvalido):
        boleto(pix_chave="11222333000181", pix_txid="NN 109/12345678").contexto_render()


def test_o_identificador_fecha_a_conciliacao_do_qr_avulso() -> None:
    """O QR avulso não dá baixa, mas o identificador permite reconhecer o crédito.

    É o caminho manual completo: o ``txid`` vai no QR, reaparece no memo do
    crédito PIX no extrato, e ``concilia`` casa com o título — sem isso, o
    recebimento fica órfão e o boleto parece não pago.
    """
    from decimal import Decimal

    from pycobranca.ofx import concilia
    from pycobranca.ofx.parser import Extrato, Transacao

    titulo = boleto(pix_chave="11222333000181", pix_txid="NN10912345678")
    txid = "NN10912345678"
    assert txid in titulo.contexto_render()["pix"]["copia_cola"]

    extrato = Extrato(
        transacoes=[
            Transacao(tipo="CREDIT", valor=Decimal("127.50"), memo=f"PIX RECEBIDO {txid} CLIENTE"),
            Transacao(tipo="CREDIT", valor=Decimal("300.00"), memo="TED RECEBIDA OUTRO CLIENTE"),
        ]
    )
    resultado = concilia(extrato, [txid, "NN10999999999"])
    assert [nn for _, nn in resultado.conciliadas] == [txid]
    assert resultado.pendentes == ["NN10999999999"]


def test_qr_avulso_sai_identificado_mesmo_sem_txid_informado() -> None:
    """O padrão identifica, porque esquecer o txid custa o recebimento.

    Sem identificador, o crédito PIX entra no extrato sem nada que o amarre ao
    título: fica órfão, e o boleto parece não pago. Deixar isso na lembrança de
    quem chama garante que uma parte dos boletos saia assim.
    """
    titulo = boleto(pix_chave="11222333000181")
    assert titulo.nosso_numero_formatado() == "109/12345678-0"
    assert titulo.txid_do_titulo() == "109123456780"  # sem "/" nem "-"
    assert "109123456780" in titulo.contexto_render()["pix"]["copia_cola"]


def test_txid_informado_tem_precedencia_sobre_o_derivado() -> None:
    pix = boleto(pix_chave="11222333000181", pix_txid="FATURA2026").contexto_render()["pix"]
    assert "FATURA2026" in pix["copia_cola"]
    assert "109123456780" not in pix["copia_cola"]


def test_da_para_abrir_mao_do_identificador_de_proposito() -> None:
    """``"***"`` é o "ausente" do padrão EMV — explícito, não por esquecimento."""
    pix = boleto(pix_chave="11222333000181", pix_txid="***").contexto_render()["pix"]
    assert "0503***" in pix["copia_cola"]


def test_o_valor_vai_no_qr_avulso() -> None:
    """Campo 54: sem ele o pagador digita o valor, e digita errado."""
    pix = boleto(pix_chave="11222333000181").contexto_render()["pix"]
    assert "5406127.50" in pix["copia_cola"]  # id 54, tamanho 06, "127.50"


@pytest.mark.parametrize("nome", ["itau", "bradesco", "caixa", "santander", "sicoob"])
def test_txid_derivado_e_valido_em_todos_os_bancos(nome: str) -> None:
    """O nosso número varia muito de banco para banco — o txid tem de sobreviver.

    Formatos com ``/``, ``-`` e ``.`` aparecem em vários; o padrão só aceita
    ``A-Za-z0-9`` até 25.
    """
    from exemplos_boletos import EXEMPLOS

    txid = EXEMPLOS[nome]["boleto"]().txid_do_titulo()
    assert txid.isalnum() and 1 <= len(txid) <= 25, f"{nome}: txid inválido {txid!r}"


def test_sem_nosso_numero_o_txid_e_ausente_e_nao_inventado() -> None:
    """Zeros de preenchimento não são identificador.

    ``nosso_numero_formatado()`` completa com zeros e ainda calcula o dígito em
    cima deles: sem nosso número sairia ``109000000008``, plausível e sem
    significado. Na conciliação isso não casa com título nenhum — ou casa com o
    errado, se outro boleto legitimamente tiver esse número.
    """
    titulo = boleto(nosso_numero="", pix_chave="11222333000181")
    assert titulo.nosso_numero_formatado() == "109/00000000-8"  # o que o zfill produz
    assert titulo.txid_do_titulo() == "***"  # ausente, no padrão EMV


def test_qr_do_pix_dispensa_boleto_e_nosso_numero() -> None:
    """Quem ainda não tem o nosso número monta o QR direto pelo ``PixPayload``.

    O QR do PIX precisa de chave, nome, cidade e valor — nada disso depende do
    nosso número. O boleto exige o nosso número porque **o código de barras**
    exige, não porque o PIX exija.
    """
    from decimal import Decimal

    from pycobranca.pix import PixPayload, qr_matrix

    copia_cola = PixPayload(
        chave="11222333000181",
        nome="Empresa Exemplo LTDA",
        cidade="SAO PAULO",
        valor=Decimal("127.50"),
        info_adicional="Fatura 2026-0001",
    ).br_code()

    assert "5406127.50" in copia_cola  # valor vai
    assert "0503***" in copia_cola  # txid ausente, declarado
    assert len(qr_matrix(copia_cola)) > 0  # QR sai
