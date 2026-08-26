"""Formatação de campos CNAB (padrão FEBRABAN)."""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "remover_acentos",
    "format_size",
    "format_valor",
    "campo_numerico",
    "confere_tamanhos",
    "avisa_carteira_ignorada",
]


def remover_acentos(texto: str) -> str:
    """Remove acentos (normaliza para ASCII) nos campos do arquivo CNAB."""
    return unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")


def format_size(texto: str, tamanho: int) -> str:
    """Equivalente ao ``format_size`` (``formatacao_string.rb``).

    Remove acentos, colapsa espaços e **depois** remove símbolos (por isso um
    ``&`` vira espaço duplo, como no Ruby); trunca ou completa com espaços.
    """
    limpo = remover_acentos(texto or "").strip()
    limpo = re.sub(r"\s+", " ", limpo)
    limpo = re.sub(r"[^A-Za-z0-9 ]", "", limpo)
    return limpo[:tamanho] if len(limpo) > tamanho else limpo.ljust(tamanho)


def format_valor(valor, tamanho: int = 13) -> str:
    """Equivalente ao ``format_value``: ``%.2f`` sem o ponto, zeros à esquerda."""
    return f"{float(valor):.2f}".replace(".", "").rjust(tamanho, "0")


def campo_numerico(valor, tamanho: int, campo: str) -> str:
    """Alinha ``valor`` à direita em ``tamanho`` posições, sem estourar o campo.

    ``str.rjust`` **preenche mas nunca corta**: um valor mais longo que o campo
    atravessa para a posição seguinte, e o CNAB é posicional — todo o resto do
    registro desloca. O arquivo sai com 401 ou 402 posições e o banco o recusa,
    ou pior, lê os campos trocados.

    Aqui zeros à esquerda são descartados quando sobram (``"000"`` num campo de
    dois vira ``"00"``: mesmo valor), mas **dígito significativo que não cabe
    levanta erro** em vez de ser cortado em silêncio — truncar um nosso número
    produziria um título com outro número.
    """
    from ..exceptions import BoletoInvalido

    digitos = "".join(c for c in str(valor or "") if c.isdigit())
    significativos = digitos.lstrip("0")
    if len(significativos) > tamanho:
        raise BoletoInvalido(
            f"{campo}: {digitos!r} não cabe em {tamanho} posições "
            f"({len(significativos)} dígitos significativos)"
        )
    return significativos.rjust(tamanho, "0")


def confere_tamanhos(linhas, tamanho: int | tuple[int, ...] | None) -> None:
    """Recusa o arquivo se algum registro não tiver o tamanho do layout.

    É a rede que pega o que nenhum limite por campo pegou. O CNAB é posicional:
    um caractere a mais em qualquer campo empurra todos os seguintes, e o
    arquivo continua parecendo válido — o banco é que lê o vencimento no lugar
    do valor. Melhor recusar aqui, com o número do registro, do que entregar um
    arquivo deslocado.

    ``tamanho`` aceita uma tupla para os layouts que misturam tamanhos.
    """
    from ..exceptions import BoletoInvalido

    if tamanho is None:
        return
    aceitos = (tamanho,) if isinstance(tamanho, int) else tuple(tamanho)
    esperado = " ou ".join(str(t) for t in aceitos)
    for i, linha in enumerate(linhas):
        if len(linha) not in aceitos:
            raise BoletoInvalido(
                f"registro {i + 1} com {len(linha)} posições (esperado {esperado})"
            )


def avisa_carteira_ignorada(remessa) -> None:
    """Avisa quando ``carteira`` foi informada e este layout não a grava.

    O campo está na base, então **toda** remessa o aceita — mas oito layouts não
    têm carteira: a CrediSIS e o Santander no 400, e seis dos sete 240, onde a
    FEBRABAN separa o *código da carteira* (posição 58 do segmento P) da
    *modalidade* do banco. Nesses, informar ``carteira`` não fazia nada, em
    silêncio, e quem monta a remessa com o mesmo dicionário do boleto acreditava
    ter escolhido a carteira.
    """
    import warnings

    from ..exceptions import CampoIgnorado

    alvo = getattr(remessa, "campo_de_carteira", None)
    if alvo is None or not str(getattr(remessa, "carteira", "") or "").strip():
        return
    onde = f"use {alvo!r}" if alvo else "este layout não tem campo de carteira"
    warnings.warn(
        f"{type(remessa).__name__}: `carteira` não é gravada neste layout ({onde}). "
        "O arquivo sai correto, mas sem a carteira que você informou.",
        CampoIgnorado,
        stacklevel=3,
    )
