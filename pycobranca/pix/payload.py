"""BR Code PIX — payload EMV® (copia-e-cola) com CRC16-CCITT.

Implementa o payload estático do PIX conforme o Manual de Padrões para
Iniciação do PIX (BCB), validado contra o vetor canônico do manual
(CRC ``1D3D``). Estrutura TLV (ID + tamanho + valor):

| ID | Campo |
|----|-------|
| 00 | Payload Format Indicator (``01``) |
| 26 | Merchant Account Information (GUI ``br.gov.bcb.pix`` + chave [+ info]) |
| 52 | Merchant Category Code (``0000``) |
| 53 | Moeda (``986`` = BRL) |
| 54 | Valor (opcional) |
| 58 | País (``BR``) |
| 59 | Nome do recebedor (≤25) |
| 60 | Cidade (≤15, maiúsculas) |
| 62 | Additional Data (``txid``, ``***`` se ausente) |
| 63 | CRC16-CCITT-FALSE (4 hex) |
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from ..exceptions import PyCobrancaError

__all__ = ["PixPayload", "crc16_ccitt", "PixInvalido"]


class PixInvalido(PyCobrancaError, ValueError):
    """Dados de PIX inválidos para montagem do BR Code."""


def crc16_ccitt(dados: str) -> str:
    """CRC16-CCITT-FALSE (poly 0x1021, init 0xFFFF), em 4 hex maiúsculos."""
    crc = 0xFFFF
    for byte in dados.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def _sem_acentos(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def _campo(id_: str, valor: str) -> str:
    if len(valor) > 99:
        raise PixInvalido(f"campo EMV {id_} excede 99 caracteres: {len(valor)}")
    return f"{id_}{len(valor):02d}{valor}"


@dataclass
class PixPayload:
    """Payload estático do PIX (Bolepix).

    Args:
        chave: chave PIX do recebedor (e-mail, CPF/CNPJ, telefone ou EVP).
        nome: nome do recebedor (truncado em 25, sem acentos).
        cidade: cidade do recebedor (truncada em 15, maiúsculas, sem acentos).
        valor: valor da cobrança (opcional; 2 casas decimais).
        txid: identificador da transação (``A-Za-z0-9``, ≤25; ``***`` se vazio).
        info_adicional: texto livre opcional no campo 26.
    """

    chave: str
    nome: str
    cidade: str
    valor: Decimal | str | float | None = None
    txid: str = "***"
    info_adicional: str = ""

    def _validar(self) -> None:
        if not self.chave:
            raise PixInvalido("chave PIX é obrigatória")
        if not self.nome:
            raise PixInvalido("nome do recebedor é obrigatório")
        if not self.cidade:
            raise PixInvalido("cidade do recebedor é obrigatória")
        txid = self.txid or "***"
        if txid != "***" and (len(txid) > 25 or not txid.isalnum()):
            raise PixInvalido(f"txid inválido (A-Za-z0-9, até 25): {txid!r}")

    def br_code(self) -> str:
        """Monta o copia-e-cola completo (com CRC)."""
        self._validar()
        conta = _campo("00", "br.gov.bcb.pix") + _campo("01", self.chave)
        if self.info_adicional:
            conta += _campo("02", _sem_acentos(self.info_adicional)[:40])
        payload = (
            _campo("00", "01") + _campo("26", conta) + _campo("52", "0000") + _campo("53", "986")
        )
        if self.valor is not None:
            centavos = Decimal(str(self.valor)).quantize(Decimal("0.01"))
            if centavos <= 0:
                raise PixInvalido(f"valor deve ser positivo: {self.valor!r}")
            payload += _campo("54", f"{centavos}")
        payload += (
            _campo("58", "BR")
            + _campo("59", _sem_acentos(self.nome)[:25])
            + _campo("60", _sem_acentos(self.cidade).upper()[:15])
            + _campo("62", _campo("05", self.txid or "***"))
            + "6304"
        )
        return payload + crc16_ccitt(payload)
