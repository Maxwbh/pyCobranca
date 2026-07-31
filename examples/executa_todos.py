"""Executa todos os exemplos em sequência — é o que a CI roda.

    python examples/executa_todos.py

Falha (código de saída 1) no primeiro exemplo que levantar exceção, garantindo
que a documentação executável nunca fique desatualizada em relação à API.
"""

from __future__ import annotations

import runpy
import sys
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


def exemplos() -> list[Path]:
    """Os exemplos numerados, em ordem (ignora ``_comum`` e este runner)."""
    return sorted(p for p in RAIZ.glob("[0-9][0-9]_*.py"))


def main() -> int:
    sys.path.insert(0, str(RAIZ))  # para o `import _comum` dos exemplos
    falhas: list[str] = []

    for exemplo in exemplos():
        print(f"\n{'─' * 70}\n▶ {exemplo.name}\n{'─' * 70}")
        try:
            runpy.run_path(str(exemplo), run_name="__main__")
        except Exception:  # noqa: BLE001 — o runner reporta e segue
            traceback.print_exc()
            falhas.append(exemplo.name)

    print(f"\n{'═' * 70}")
    if falhas:
        print(f"✗ {len(falhas)} exemplo(s) falharam: {', '.join(falhas)}")
        return 1
    print(f"✓ {len(exemplos())} exemplos executados com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
