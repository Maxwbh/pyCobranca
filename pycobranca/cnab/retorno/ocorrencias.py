"""Rótulos legíveis para os códigos de ocorrência do retorno CNAB.

O retorno traz apenas os **códigos**; este módulo é uma camada de
conveniência que traduz os códigos mais comuns do padrão FEBRABAN para texto.
Os mapas são **indicativos**: alguns bancos atribuem significados próprios a
determinados códigos — na dúvida, consulte o manual do banco (ver
``docs/bancos/``). Esta tradução não interfere no parsing dos registros.
"""

from __future__ import annotations

__all__ = [
    "OCORRENCIAS_400",
    "OCORRENCIAS_240",
    "OCORRENCIAS_400_POR_BANCO",
    "descreve_ocorrencia",
]

#: Códigos de ocorrência do retorno CNAB 400 (padrão CBR643/FEBRABAN).
OCORRENCIAS_400: dict[str, str] = {
    "02": "Entrada confirmada",
    "03": "Entrada rejeitada",
    "04": "Transferência de carteira/entrada",
    "05": "Transferência de carteira/baixa",
    "06": "Liquidação normal",
    "07": "Liquidação por conta/parcial",
    "08": "Liquidação por saldo",
    "09": "Baixa",
    "10": "Baixa solicitada",
    "11": "Títulos em carteira (em ser)",
    "12": "Confirmação de recebimento de instrução de abatimento",
    "13": "Confirmação de recebimento de instrução de cancelamento de abatimento",
    "14": "Confirmação de recebimento de instrução de alteração de vencimento",
    "15": "Liquidação em cartório",
    "16": "Confirmação de recebimento de instrução de protesto",
    "17": "Confirmação de recebimento de instrução de sustação de protesto",
    "18": "Acerto de depositária",
    "19": "Confirmação de recebimento de instrução de protesto",
    "20": "Confirmação de recebimento de instrução de sustação de protesto",
    "21": "Acerto do controle do participante",
    "22": "Título com pagamento cancelado",
    "23": "Encaminhado a protesto",
    "24": "Confirmação de recebimento de instrução de não protestar",
    "25": "Alegação do sacado",
    "28": "Débito de tarifas/custas",
    "30": "Alteração de dados rejeitada",
    "32": "Instrução rejeitada",
    "40": "Baixa por ter sido liquidado",
    "42": "Alteração de nosso número",
    "44": "Título pago com cheque devolvido",
    "51": "Título DDA reconhecido pelo sacado",
    "52": "Título DDA não reconhecido pelo sacado",
    "53": "Título DDA recusado pela CIP",
}

#: Códigos de ocorrência do retorno CNAB 240 (padrão FEBRABAN, segmento T).
OCORRENCIAS_240: dict[str, str] = {
    "02": "Entrada confirmada",
    "03": "Entrada rejeitada",
    "04": "Transferência de carteira/entrada",
    "05": "Transferência de carteira/baixa",
    "06": "Liquidação",
    "07": "Confirmação do recebimento da instrução de desconto",
    "08": "Confirmação do recebimento da instrução de cancelamento de desconto",
    "09": "Baixa",
    "11": "Títulos em carteira (em ser)",
    "12": "Confirmação de recebimento de instrução de abatimento",
    "13": "Confirmação de recebimento de instrução de cancelamento de abatimento",
    "14": "Confirmação de recebimento de instrução de alteração de vencimento",
    "15": "Franco de pagamento",
    "17": "Liquidação após baixa ou liquidação de título não registrado",
    "19": "Confirmação de recebimento de instrução de protesto",
    "20": "Confirmação de recebimento de instrução de sustação de protesto",
    "23": "Remessa a cartório (aponte em cartório)",
    "24": "Retirada de cartório e manutenção em carteira",
    "25": "Protestado e baixado (baixa por ter sido protestado)",
    "26": "Instrução rejeitada",
    "27": "Confirmação do pedido de alteração de outros dados",
    "28": "Débito de tarifas/custas",
    "29": "Ocorrências do sacado",
    "30": "Alteração de dados rejeitada",
    "36": "Confirmação de envio de e-mail/SMS",
    "37": "Envio de e-mail/SMS rejeitado",
}


#: Bancos que redefinem códigos do CNAB 400. Consultado **antes** do mapa padrão.
#:
#: O Inter usa sete códigos, e **três** colidem de frente com a FEBRABAN:
#:
#: - ``07`` — no padrão é *Liquidação por conta/parcial*; no Inter, **Cancelado**;
#: - ``15`` — no padrão é *Liquidação em cartório*; no Inter, **alteração do valor
#:   nominal realizada**;
#: - ``16`` — no padrão é *Confirmação de instrução de protesto*; no Inter,
#:   **alteração de valor e vencimento realizada**.
#:
#: Nos três, o rótulo do padrão é plausível e diz o oposto do que aconteceu: um
#: título cancelado vira parcialmente liquidado, uma edição de valor vira
#: liquidação em cartório, outra edição vira protesto. É o tipo de erro que
#: atravessa uma conciliação sem nenhum sinal.
#:
#: O Safra tem colisão da mesma natureza no ``40``: no padrão é *Baixa por ter
#: sido liquidado* — título pago — e no Safra é **baixa de título protestado**.
#: Os pares 42/44 e 51/52/53 divergem pelo mesmo motivo.
OCORRENCIAS_400_POR_BANCO: dict[str, dict[str, str]] = {
    "077": {  # Banco Inter — Manual CNAB 400 V9 (06/07/2026), seção 5.2, item 14
        "02": "Em aberto",
        "03": "Erro",
        "06": "Pago",
        "07": "Cancelado",
        "14": "Alteração da data de vencimento realizada",
        "15": "Alteração do valor nominal do título realizada",
        "16": "Alteração do valor nominal e da data de vencimento realizada",
    },
    "422": {  # Banco Safra — Leiaute de Arquivos, Cobrança CNAB 400, nota 6.2.2
        "02": "Entrada confirmada",
        "03": "Entrada rejeitada",
        "04": "Transferência de carteira (entrada)",
        "05": "Transferência de carteira (baixa)",
        "06": "Liquidação normal",
        "09": "Baixado automaticamente",
        "10": "Baixado conforme instruções",
        "11": "Títulos em ser (arquivo mensal)",
        "12": "Abatimento concedido",
        "13": "Abatimento cancelado",
        "14": "Vencimento alterado",
        "15": "Liquidação em cartório",
        "19": "Confirmação de instrução de protesto",
        "20": "Confirmação de sustar protesto",
        "21": "Transferência de beneficiário",
        "23": "Título enviado a cartório",
        "40": "Baixa de título protestado",
        "41": "Liquidação de título baixado",
        "42": "Título retirado do cartório",
        "43": "Despesa de cartório",
        "44": "Aceite do título DDA pelo pagador",
        "45": "Não aceite do título DDA pelo pagador",
        "51": "Valor do título alterado",
        "52": "Acerto de data de emissão",
        "53": "Acerto de código de espécie de documento",
        "54": "Alteração de seu número",
        "56": "Instrução de negativação aceita",
        "57": "Instrução de baixa de negativação aceita",
        "58": "Instrução de não negativar aceita",
    },
}


def descreve_ocorrencia(
    codigo: str | None, layout: str = "400", banco: str | None = None
) -> str | None:
    """Rótulo legível para um código de ocorrência (``None`` se desconhecido).

    ``banco`` permite que instituições com códigos próprios sobreponham o mapa
    padrão. Sem ele, o comportamento é o de sempre.
    """
    if not codigo:
        return None
    codigo = str(codigo).strip()
    if banco and str(layout) != "240":
        proprio = OCORRENCIAS_400_POR_BANCO.get(str(banco).zfill(3))
        if proprio and codigo in proprio:
            return proprio[codigo]
    mapa = OCORRENCIAS_240 if str(layout) == "240" else OCORRENCIAS_400
    return mapa.get(codigo)
