"""Validação e formatação de CPF e CNPJ."""

from __future__ import annotations

__all__ = ["so_digitos", "validar_cpf", "validar_cnpj", "formatar_cpf", "formatar_cnpj"]


def so_digitos(valor: str) -> str:
    """Remove tudo que não for dígito."""
    return "".join(ch for ch in str(valor) if ch.isdigit())


def _dv_cpf(digitos: str, pesos: range) -> int:
    soma = sum(int(d) * p for d, p in zip(digitos, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def validar_cpf(cpf: str) -> bool:
    """Valida um CPF (com ou sem máscara)."""
    d = so_digitos(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    dv1 = _dv_cpf(d[:9], range(10, 1, -1))
    dv2 = _dv_cpf(d[:10], range(11, 1, -1))
    return d[9] == str(dv1) and d[10] == str(dv2)


_PESOS_CNPJ_1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_CNPJ_2 = (6,) + _PESOS_CNPJ_1


def _dv_cnpj(digitos: str, pesos: tuple[int, ...]) -> int:
    soma = sum(int(d) * p for d, p in zip(digitos, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def validar_cnpj(cnpj: str) -> bool:
    """Valida um CNPJ (com ou sem máscara)."""
    d = so_digitos(cnpj)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    dv1 = _dv_cnpj(d[:12], _PESOS_CNPJ_1)
    dv2 = _dv_cnpj(d[:13], _PESOS_CNPJ_2)
    return d[12] == str(dv1) and d[13] == str(dv2)


def formatar_cpf(cpf: str) -> str:
    """Formata como ``000.000.000-00``."""
    d = so_digitos(cpf).zfill(11)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def formatar_cnpj(cnpj: str) -> str:
    """Formata como ``00.000.000/0000-00``."""
    d = so_digitos(cnpj).zfill(14)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
