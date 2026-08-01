"""Utilidades compartilhadas pelos exemplos (diretório de saída e títulos).

Não faz parte da biblioteca — é só para os exemplos ficarem curtos e legíveis.
"""

from __future__ import annotations

from pathlib import Path

#: raiz do diretório de exemplos
RAIZ = Path(__file__).resolve().parent

#: onde os exemplos gravam PDFs e arquivos CNAB (ignorado pelo git)
SAIDA = RAIZ / "saida"

#: dados de exemplo versionados (retorno CNAB e extrato OFX)
DADOS = RAIZ / "dados"


def titulo(texto: str) -> None:
    """Imprime um título de seção."""
    print(f"\n=== {texto} ===")


def grava(nome: str, conteudo: bytes | str) -> Path:
    """Grava ``conteudo`` em ``saida/<nome>`` e devolve o caminho."""
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / nome
    if isinstance(conteudo, bytes):
        destino.write_bytes(conteudo)
    else:
        destino.write_text(conteudo, encoding="latin-1", newline="")
    print(f"  -> saida/{nome} ({len(conteudo)} bytes)")
    return destino
