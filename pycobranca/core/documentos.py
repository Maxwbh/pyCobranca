"""Validação e formatação de CPF e CNPJ (numérico e **alfanumérico**).

O CNPJ alfanumérico (IN RFB 2.229/2024) mantém as
14 posições, mas as **12 primeiras podem conter letras** (``A``–``Z`` maiúsculas)
além dos dígitos; os **2 últimos continuam numéricos** (os DVs).

O cálculo dos DVs é o mesmo módulo 11 de sempre, com uma diferença: o valor de
cada caractere é o **código ASCII menos 48** (``"0"`` → 0 … ``"9"`` → 9,
``"A"`` → 17 … ``"Z"`` → 42). Para um CNPJ puramente numérico o resultado é
idêntico ao cálculo antigo, então nada muda para quem já usava.

O **CPF continua exclusivamente numérico**.
"""

from __future__ import annotations

__all__ = [
    "so_digitos",
    "so_alfanumerico",
    "normaliza_documento",
    "validar_cpf",
    "validar_cnpj",
    "cnpj_e_alfanumerico",
    "formatar_cpf",
    "formatar_cnpj",
    "formatar_documento",
]


def so_digitos(valor: str) -> str:
    """Remove tudo que não for dígito (use para CPF e campos numéricos)."""
    return "".join(ch for ch in str(valor) if ch.isdigit())


def so_alfanumerico(valor: str) -> str:
    """Remove a máscara preservando letras e dígitos, em CAIXA ALTA.

    É o normalizador do CNPJ: descarta pontuação (``.``, ``/``, ``-``, espaços)
    mas mantém as letras do CNPJ alfanumérico.
    """
    return "".join(ch for ch in str(valor).upper() if ch.isalnum())


def normaliza_documento(valor: str) -> str:
    """Normaliza CPF **ou** CNPJ preservando o que cada um aceita.

    Devolve 11 posições numéricas (CPF) ou 14 alfanuméricas (CNPJ). Quando o
    valor não tem esses tamanhos, devolve a forma alfanumérica sem máscara — o
    chamador decide o que fazer.
    """
    alfa = so_alfanumerico(valor)
    if len(alfa) == 11 and alfa.isdigit():
        return alfa
    return alfa


def _dv_cpf(digitos: str, pesos: range) -> int:
    soma = sum(int(d) * p for d, p in zip(digitos, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def validar_cpf(cpf: str) -> bool:
    """Valida um CPF (com ou sem máscara). Somente numérico."""
    d = so_digitos(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    dv1 = _dv_cpf(d[:9], range(10, 1, -1))
    dv2 = _dv_cpf(d[:10], range(11, 1, -1))
    return d[9] == str(dv1) and d[10] == str(dv2)


_PESOS_CNPJ_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_CNPJ_2 = (6,) + _PESOS_CNPJ_1


def _valor_caractere(ch: str) -> int:
    """Valor do caractere no cálculo do DV: código ASCII menos 48."""
    return ord(ch) - 48


def _dv_cnpj(base: str, pesos: tuple[int, ...]) -> int:
    soma = sum(_valor_caractere(c) * p for c, p in zip(base, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def dv_cnpj(base12: str) -> str:
    """Calcula os 2 DVs de um CNPJ a partir das 12 primeiras posições."""
    base = so_alfanumerico(base12)
    dv1 = _dv_cnpj(base, _PESOS_CNPJ_1)
    dv2 = _dv_cnpj(base + str(dv1), _PESOS_CNPJ_2)
    return f"{dv1}{dv2}"


def cnpj_e_alfanumerico(cnpj: str) -> bool:
    """``True`` se o CNPJ tem letras nas 12 primeiras posições."""
    c = so_alfanumerico(cnpj)
    return len(c) == 14 and not c[:12].isdigit()


def validar_cnpj(cnpj: str) -> bool:
    """Valida um CNPJ, **numérico ou alfanumérico** (com ou sem máscara)."""
    c = so_alfanumerico(cnpj)
    if len(c) != 14 or len(set(c)) == 1:
        return False
    base, dvs = c[:12], c[12:]
    # as 12 primeiras: dígitos ou letras A-Z; os 2 DVs: sempre numéricos
    if not all(ch.isdigit() or ("A" <= ch <= "Z") for ch in base):
        return False
    if not dvs.isdigit():
        return False
    return dvs == dv_cnpj(base)


def formatar_cpf(cpf: str) -> str:
    """Formata como ``000.000.000-00``."""
    d = so_digitos(cpf).zfill(11)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def formatar_cnpj(cnpj: str) -> str:
    """Formata como ``00.000.000/0000-00``, preservando letras."""
    c = so_alfanumerico(cnpj).rjust(14, "0")
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"


def formatar_documento(valor: str) -> str:
    """Formata como CPF (11 posições) ou CNPJ (14); devolve o original se não bater."""
    doc = so_alfanumerico(valor)
    if len(doc) == 11:
        return formatar_cpf(doc)
    if len(doc) == 14:
        return formatar_cnpj(doc)
    return str(valor)
