"""CrediSIS (097)."""

from __future__ import annotations

from typing import ClassVar

from ..core.documentos import so_alfanumerico, so_digitos
from ..core.dv import modulo11_flex
from ..exceptions import BoletoInvalido
from .base import BancoBase

__all__ = ["CrediSIS"]


class CrediSIS(BancoBase):
    codigo: ClassVar[str] = "097"
    nome: ClassVar[str] = "CrediSIS"
    digito_banco: ClassVar[str] = "3"
    carteiras: ClassVar[tuple[str, ...]] = ("18",)
    suporta_pix: ClassVar[bool] = False
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {
        "agencia": (1, 4),
        "convenio": (1, 6),
        "nosso_numero": (1, 6),
    }

    @property
    def dv_documento_cedente(self):
        doc = so_alfanumerico(self.cedente_documento)
        if not doc:
            raise BoletoInvalido("cedente_documento é obrigatório para o CrediSIS")
        if not doc.isdigit():
            # O manual oficial ("Padronização Boletos de Pagamento", Cooperativa
            # Central de Crédito Noroeste Brasileiro, v1.0, maio/2017) define o
            # nosso número como 097XAAAACCCCCCSSSSSS, com X = "Módulo 11 do
            # CPF/CNPJ (Incluindo dígitos verificadores) do Beneficiário". O
            # documento é anterior à IN RFB 2.229/2024 e não define o cálculo
            # quando há letras. Falhar é mais seguro do que emitir um código de
            # barras que o banco rejeitaria.
            raise BoletoInvalido(
                "CrediSIS ainda não suporta CNPJ alfanumérico no cedente "
                "(o DV do campo livre não está definido no manual do banco)"
            )
        return modulo11_flex(doc, mapa={0: 1, 10: 1, 11: 1})

    def nosso_numero_formatado(self) -> str:
        return (
            f"097{self.dv_documento_cedente}"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.convenio).zfill(6)}"
            f"{so_digitos(self.nosso_numero).zfill(6)}"
        )

    def campo_livre(self) -> str:
        return (
            f"00000097{self.dv_documento_cedente}"
            f"{so_digitos(self.agencia).zfill(4)}"
            f"{so_digitos(self.convenio).zfill(6)}"
            f"{so_digitos(self.nosso_numero).zfill(6)}"
        )
