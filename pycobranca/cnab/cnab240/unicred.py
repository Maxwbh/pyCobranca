"""Remessa CNAB 240 — Unicred (136).

Reutiliza integralmente o layout do Sicredi (mesma cooperativa de tecnologia).
"""

from __future__ import annotations

from dataclasses import dataclass

from .sicredi import RemessaSicredi240

__all__ = ["RemessaUnicred240"]


@dataclass
class RemessaUnicred240(RemessaSicredi240):
    pass
