"""Parser de extrato bancário OFX (v1 SGML e v2 XML), em Python puro.

Lê o arquivo, normaliza o encoding (Latin-1 → UTF-8, comum nos bancos
brasileiros) e estrutura banco, conta, período, saldo e transações — com o
nosso número extraído do memo de cada transação. ``to_dict()`` devolve uma
estrutura JSON-friendly pronta para consumo via REST.

OFX v1 é *tag-soup* SGML (folhas sem fechamento: ``<TRNAMT>123.45``); v2 é XML
(``<TRNAMT>123.45</TRNAMT>``). O extrator de folhas por regex atende os dois.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from ..core.entrada import FonteDeArquivo
from ..exceptions import OFXInvalido
from .nosso_numero import extrair_nosso_numero

__all__ = ["Transacao", "Extrato"]

_LEAF = re.compile(r"<([A-Z0-9.]+)>\s*([^<\r\n]*)")


def _normaliza(raw: bytes) -> str:
    """Bytes → texto UTF-8 (tenta UTF-8; cai para Latin-1 como fazem os bancos BR)."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("iso-8859-1", errors="replace")


def _bloco(texto: str, tag: str) -> str:
    """Conteúdo do primeiro ``<TAG>...</TAG>`` (ou ``""``)."""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", texto, re.S)
    return m.group(1) if m else ""


def _valores(bloco: str) -> dict[str, str]:
    """Mapa tag→valor das folhas do bloco (primeira ocorrência não-vazia)."""
    out: dict[str, str] = {}
    for tag, val in _LEAF.findall(bloco):
        v = val.strip()
        if v and tag not in out:
            out[tag] = v
    return out


def _data(raw: str | None) -> date | None:
    """Data OFX (``YYYYMMDD[HHMMSS][tz]``) → ``date``."""
    if not raw:
        return None
    digitos = re.sub(r"\D", "", raw)[:8]
    if len(digitos) != 8:
        return None
    try:
        return datetime.strptime(digitos, "%Y%m%d").date()
    except ValueError:
        return None


def _dec(raw: str | None) -> Decimal:
    if raw in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(raw))
    except ArithmeticError:  # decimal.InvalidOperation
        return Decimal("0")


@dataclass
class Transacao:
    """Uma transação (lançamento) do extrato OFX."""

    fitid: str = ""
    tipo: str = "CREDIT"  # CREDIT | DEBIT (derivado do sinal do valor)
    data: date | None = None
    valor: Decimal = Decimal("0")  # sempre positivo (abs)
    memo: str = ""
    name: str = ""
    checknum: str = ""
    refnum: str = ""
    nosso_numero_extraido: str | None = None

    def to_dict(self) -> dict:
        return {
            "fitid": self.fitid,
            "tipo": self.tipo,
            "data": self.data.isoformat() if self.data else None,
            "valor": float(self.valor),
            "memo": self.memo,
            "name": self.name,
            "checknum": self.checknum,
            "refnum": self.refnum,
            "nosso_numero_extraido": self.nosso_numero_extraido,
        }


@dataclass
class Extrato:
    """Extrato bancário OFX estruturado."""

    org: str = ""
    fid: str = ""
    agencia: str = ""
    conta_numero: str = ""
    conta_tipo: str = ""
    saldo_valor: Decimal = Decimal("0")
    saldo_data: date | None = None
    transacoes: list[Transacao] = field(default_factory=list)

    # ---- leitura ----
    @classmethod
    def ler(cls, arquivo: FonteDeArquivo, *, somente_creditos: bool = False) -> Extrato:
        """Lê um OFX de um caminho, ``bytes`` ou objeto com ``.read()``."""
        if hasattr(arquivo, "read"):
            dados = arquivo.read()
        elif isinstance(arquivo, (bytes, bytearray)):
            dados = bytes(arquivo)
        else:
            with open(arquivo, "rb") as fh:
                dados = fh.read()
        if isinstance(dados, str):
            dados = dados.encode("utf-8", "replace")
        return cls.parse(_normaliza(dados), somente_creditos=somente_creditos)

    @classmethod
    def parse(cls, conteudo: str, *, somente_creditos: bool = False) -> Extrato:
        """Estrutura o conteúdo textual de um OFX.

        Levanta :class:`OFXInvalido` se o conteúdo não tiver a marcação de um OFX
        (``<OFX>`` ou o cabeçalho ``OFXHEADER``) — assim um consumidor distingue
        um **arquivo inválido** de um **extrato válido sem transações**.
        """
        if "<OFX>" not in conteudo and "OFXHEADER" not in conteudo.upper():
            raise OFXInvalido("conteúdo não parece um OFX (faltam <OFX>/OFXHEADER)")
        corpo = conteudo.split("<OFX>", 1)[-1]

        fi = _valores(_bloco(corpo, "FI"))
        org, fid = fi.get("ORG", ""), fi.get("FID", "")
        banco_id = org or fid

        conta = _valores(_bloco(corpo, "BANKACCTFROM"))
        bal = _valores(_bloco(corpo, "LEDGERBAL"))

        transacoes: list[Transacao] = []
        for bruto in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", corpo, re.S):
            v = _valores(bruto)
            valor = _dec(v.get("TRNAMT"))
            memo = v.get("MEMO", "")
            transacoes.append(
                Transacao(
                    fitid=v.get("FITID", ""),
                    tipo="CREDIT" if valor >= 0 else "DEBIT",
                    data=_data(v.get("DTPOSTED")),
                    valor=abs(valor),
                    memo=memo,
                    name=v.get("NAME", ""),
                    checknum=v.get("CHECKNUM", ""),
                    refnum=v.get("REFNUM", ""),
                    nosso_numero_extraido=extrair_nosso_numero(memo, banco_id),
                )
            )

        if somente_creditos:
            transacoes = [t for t in transacoes if t.tipo == "CREDIT"]

        return cls(
            org=org,
            fid=fid,
            agencia=conta.get("BRANCHID", ""),
            conta_numero=conta.get("ACCTID", ""),
            conta_tipo=conta.get("ACCTTYPE", "").upper(),
            saldo_valor=_dec(bal.get("BALAMT")),
            saldo_data=_data(bal.get("DTASOF")),
            transacoes=transacoes,
        )

    # ---- derivados ----
    @property
    def creditos(self) -> list[Transacao]:
        return [t for t in self.transacoes if t.tipo == "CREDIT"]

    @property
    def debitos(self) -> list[Transacao]:
        return [t for t in self.transacoes if t.tipo == "DEBIT"]

    @property
    def periodo(self) -> tuple[date | None, date | None]:
        datas = [t.data for t in self.transacoes if t.data]
        return (min(datas), max(datas)) if datas else (None, None)

    def to_dict(self) -> dict:
        """Contrato JSON-friendly (para consumo via REST)."""
        creditos, debitos = self.creditos, self.debitos
        inicio, fim = self.periodo
        return {
            "banco": {"org": self.org, "fid": self.fid},
            "conta": {
                "agencia": self.agencia,
                "numero": self.conta_numero,
                "tipo": self.conta_tipo,
            },
            "periodo": {
                "inicio": inicio.isoformat() if inicio else None,
                "fim": fim.isoformat() if fim else None,
            },
            "saldo": {
                "valor": float(self.saldo_valor),
                "data": self.saldo_data.isoformat() if self.saldo_data else None,
            },
            "transacoes": [t.to_dict() for t in self.transacoes],
            "resumo": {
                "total_transacoes": len(self.transacoes),
                "total_creditos": len(creditos),
                "total_debitos": len(debitos),
                "soma_creditos": float(sum((t.valor for t in creditos), Decimal("0"))),
                "soma_debitos": float(sum((t.valor for t in debitos), Decimal("0"))),
            },
        }
