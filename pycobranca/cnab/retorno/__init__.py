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

from .base import RegistroRetorno
from .cnab240 import banco_do_arquivo_240, parse_cnab240
from .cnab400 import banco_do_arquivo_400, parse_cnab400
from .ocorrencias import descreve_ocorrencia

__all__ = ["Retorno", "RegistroRetorno", "descreve_ocorrencia"]


@dataclass
class Retorno:
    """Resultado da leitura de um arquivo de retorno CNAB."""

    layout: str  # "240" ou "400"
    codigo_banco: str
    registros: list[RegistroRetorno] = field(default_factory=list)

    @classmethod
    def ler(cls, caminho: str | Path, layout: str | None = None) -> Retorno:
        """Lê o arquivo de retorno em ``caminho``.

        ``layout`` (``"240"``/``"400"``) pode ser informado; por padrão é
        detectado pelo tamanho do primeiro registro.
        """
        texto = Path(caminho).read_text(encoding="latin-1")
        linhas = texto.splitlines()
        return cls.ler_linhas(linhas, layout=layout)

    @classmethod
    def ler_linhas(cls, linhas: list[str], layout: str | None = None) -> Retorno:
        primeira = next((linha for linha in linhas if linha.strip()), "")
        if layout is None:
            layout = "240" if len(primeira) <= 245 else "400"
        if layout == "240":
            codigo_banco = banco_do_arquivo_240(primeira)
            registros = parse_cnab240(linhas, codigo_banco)
        else:
            codigo_banco = banco_do_arquivo_400(primeira)
            registros = parse_cnab400(linhas, codigo_banco)
        return cls(layout=layout, codigo_banco=codigo_banco, registros=registros)

    def to_dict(self, compact: bool = True) -> list[dict]:
        return [registro.to_dict(compact=compact) for registro in self.registros]

    def descricao_ocorrencia(self, registro: RegistroRetorno) -> str | None:
        """Rótulo legível da ocorrência do ``registro`` (indicativo — ver docs)."""
        return descreve_ocorrencia(registro.codigo_ocorrencia, self.layout)

    def __iter__(self):
        return iter(self.registros)

    def __len__(self) -> int:
        return len(self.registros)
