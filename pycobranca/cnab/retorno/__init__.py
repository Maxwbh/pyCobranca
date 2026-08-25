"""Leitura de arquivos de retorno CNAB.

Auto-detecta o layout (240 ou 400) pelo tamanho do registro e o banco pelo
header, e devolve uma lista de :class:`RegistroRetorno`. Validado campo a campo
contra vetores de referência para as fixtures ``.RET`` (ver ``tests/test_cnab_retorno.py``).

    from pycobranca.cnab.retorno import Retorno

    retorno = Retorno.ler("arquivo.ret")
    for registro in retorno.registros:
        print(registro.nosso_numero, registro.codigo_ocorrencia, registro.valor_recebido)
    dados = retorno.to_dict()  # list[dict] JSON-friendly
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...core.entrada import FonteDeArquivo
from ...exceptions import RetornoInvalido
from .base import RegistroRetorno
from .cnab240 import banco_do_arquivo_240, parse_cnab240
from .cnab400 import banco_do_arquivo_400, parse_cnab400
from .ocorrencias import OCORRENCIAS_400_POR_BANCO, descreve_ocorrencia

__all__ = ["Retorno", "RegistroRetorno", "descreve_ocorrencia", "OCORRENCIAS_400_POR_BANCO"]


@dataclass
class Retorno:
    """Resultado da leitura de um arquivo de retorno CNAB."""

    layout: str  # "240" ou "400"
    codigo_banco: str
    registros: list[RegistroRetorno] = field(default_factory=list)

    @classmethod
    def ler(cls, arquivo: FonteDeArquivo, layout: str | None = None) -> Retorno:
        """Lê um retorno de um caminho, ``bytes`` ou objeto com ``.read()``.

        Aceitar bytes é o que permite tratar um upload sem passar por arquivo
        temporário — a mesma tolerância de :meth:`pycobranca.ofx.Extrato.ler`.

        ``layout`` (``"240"``/``"400"``) pode ser informado; por padrão é
        detectado pelo tamanho do primeiro registro.
        """
        if hasattr(arquivo, "read"):
            dados = arquivo.read()
        elif isinstance(arquivo, (bytes, bytearray)):
            dados = bytes(arquivo)
        else:
            dados = Path(arquivo).read_bytes()
        if isinstance(dados, str):  # objeto aberto em modo texto
            texto = dados
        else:
            # Latin-1 mapeia todo byte 0–255, então nunca levanta: o CNAB é
            # posicional e um byte perdido deslocaria o registro inteiro.
            texto = dados.decode("latin-1")
        return cls.ler_linhas(texto.splitlines(), layout=layout)

    @classmethod
    def ler_linhas(cls, linhas: list[str], layout: str | None = None) -> Retorno:
        primeira = next((linha for linha in linhas if linha.strip()), "")
        if not primeira:
            raise RetornoInvalido("arquivo de retorno vazio (nenhuma linha com conteúdo)")
        if layout is None:
            layout = "240" if len(primeira) <= 245 else "400"
        if layout == "240":
            codigo_banco = banco_do_arquivo_240(primeira)
            registros = parse_cnab240(linhas, codigo_banco)
        else:
            codigo_banco = banco_do_arquivo_400(primeira)
            registros = parse_cnab400(linhas, codigo_banco)
        if not (codigo_banco or "").strip().isdigit():
            raise RetornoInvalido(
                "não foi possível identificar o banco no header do retorno "
                "(arquivo não parece um retorno CNAB válido)"
            )
        return cls(layout=layout, codigo_banco=codigo_banco, registros=registros)

    def to_dict(self, compact: bool = True) -> list[dict]:
        return [registro.to_dict(compact=compact) for registro in self.registros]

    def descricao_ocorrencia(self, registro: RegistroRetorno) -> str | None:
        """Rótulo legível da ocorrência do ``registro`` (indicativo — ver docs)."""
        return descreve_ocorrencia(registro.codigo_ocorrencia, self.layout, self.codigo_banco)

    def __iter__(self):
        return iter(self.registros)

    def __len__(self) -> int:
        return len(self.registros)
