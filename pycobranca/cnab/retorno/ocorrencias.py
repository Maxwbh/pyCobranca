"""Rótulos legíveis para os códigos de ocorrência do retorno CNAB.

O retorno traz apenas os **códigos**; este módulo é uma camada de
conveniência que traduz os códigos mais comuns do padrão FEBRABAN para texto.
Os mapas são **indicativos**: alguns bancos atribuem significados próprios a
determinados códigos — na dúvida, consulte o manual do banco (ver
``docs/bancos/``). Esta tradução não interfere no parsing dos registros.
"""

from __future__ import annotations

__all__ = ["OCORRENCIAS_400", "OCORRENCIAS_240", "descreve_ocorrencia"]

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


def descreve_ocorrencia(codigo: str | None, layout: str = "400") -> str | None:
    """Rótulo legível para um código de ocorrência (``None`` se desconhecido)."""
    if not codigo:
        return None
    mapa = OCORRENCIAS_240 if str(layout) == "240" else OCORRENCIAS_400
    return mapa.get(str(codigo).strip())
