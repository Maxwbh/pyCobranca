"""Base do parsing de retorno CNAB — porta fiel de ``Retorno::Base`` + parseline.

Cada layout de banco é descrito por um mapa declarativo de campos posicionais
``{atributo: (inicio, fim)}`` (faixas **inclusivas**, como no parseline do Ruby).
O valor extraído é ``linha[inicio:fim+1]`` com espaços das pontas removidos; o
campo ``motivo_ocorrencia`` usa transformações específicas por banco.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields

__all__ = ["RegistroRetorno", "extrai_campo", "transforma_motivo", "ATRIBUTOS"]

#: Atributos serializáveis de um registro de retorno (equivale a ``ATRIBUTOS``).
ATRIBUTOS = (
    "codigo_registro",
    "sequencial",
    "agencia_com_dv",
    "agencia_sem_dv",
    "cedente_com_dv",
    "convenio",
    "nosso_numero",
    "documento_numero",
    "carteira",
    "carteira_variacao",
    "especie_documento",
    "valor_titulo",
    "tipo_cobranca",
    "tipo_cobranca_anterior",
    "natureza_recebimento",
    "comando",
    "codigo_ocorrencia",
    "motivo_ocorrencia",
    "data_liquidacao",
    "data_vencimento",
    "data_ocorrencia",
    "data_credito",
    "desconto",
    "iof",
    "valor_tarifa",
    "outras_despesas",
    "juros_desconto",
    "iof_desconto",
    "valor_abatimento",
    "desconto_concedito",
    "valor_recebido",
    "juros_mora",
    "outros_recebimento",
    "abatimento_nao_aproveitado",
    "valor_lancamento",
    "valor_ajuste",
    "banco_recebedor",
    "agencia_recebedora_com_dv",
    "indicativo_lancamento",
    "indicador_valor",
    "tipo_chave_dict",
    "codigo_chave_dict",
    "txid",
)


@dataclass
class RegistroRetorno:
    """Um título processado no arquivo de retorno (equivale a ``Retorno::Base``)."""

    codigo_registro: str | None = None
    sequencial: str | None = None
    agencia_com_dv: str | None = None
    agencia_sem_dv: str | None = None
    cedente_com_dv: str | None = None
    convenio: str | None = None
    nosso_numero: str | None = None
    documento_numero: str | None = None
    carteira: str | None = None
    carteira_variacao: str | None = None
    especie_documento: str | None = None
    valor_titulo: str | None = None
    tipo_cobranca: str | None = None
    tipo_cobranca_anterior: str | None = None
    natureza_recebimento: str | None = None
    comando: str | None = None
    codigo_ocorrencia: str | None = None
    motivo_ocorrencia: list[str] | str | None = None
    data_liquidacao: str | None = None
    data_vencimento: str | None = None
    data_ocorrencia: str | None = None
    data_credito: str | None = None
    desconto: str | None = None
    iof: str | None = None
    valor_tarifa: str | None = None
    outras_despesas: str | None = None
    juros_desconto: str | None = None
    iof_desconto: str | None = None
    valor_abatimento: str | None = None
    desconto_concedito: str | None = None
    valor_recebido: str | None = None
    juros_mora: str | None = None
    outros_recebimento: str | None = None
    abatimento_nao_aproveitado: str | None = None
    valor_lancamento: str | None = None
    valor_ajuste: str | None = None
    banco_recebedor: str | None = None
    agencia_recebedora_com_dv: str | None = None
    indicativo_lancamento: str | None = None
    indicador_valor: str | None = None
    tipo_chave_dict: str | None = None
    codigo_chave_dict: str | None = None
    txid: str | None = None

    def to_dict(self, compact: bool = True) -> dict:
        """Serializa o registro (equivale a ``to_hash``; ``compact`` remove nulos)."""
        dados = {f.name: getattr(self, f.name) for f in fields(self)}
        if compact:
            return {k: v for k, v in dados.items() if v is not None}
        return dados


def extrai_campo(linha: str, faixa: tuple[int, int]) -> str:
    """Extrai ``linha[inicio:fim+1]`` (faixa inclusiva) e remove espaços das pontas."""
    inicio, fim = faixa
    return linha[inicio : fim + 1].strip()


def _ruby_to_i(texto: str) -> int:
    m = re.match(r"\s*([+-]?\d+)", texto)
    return int(m.group(1)) if m else 0


def transforma_motivo(bruto: str, modo: str) -> list[str] | str:
    """Aplica a transformação de ``motivo_ocorrencia`` conforme o banco.

    - ``"chunk2"``: blocos de 2, descarta vazios e ``"00"``.
    - ``"chunk4"``: blocos de 4, descarta vazios e ``"0000"``.
    - ``"bb2"``: blocos de 2, descarta os que valem zero (regra do Banco do Brasil).
    - ``"raw"``: retorna a string sem espaços das pontas (bancos sem lambda).
    """
    if modo == "raw":
        return bruto.strip()
    if modo == "bb2":
        return [c for c in re.findall(r"..", bruto) if _ruby_to_i(c) != 0]
    if modo == "chunk4":
        return [c for c in re.findall(r".{4}", bruto) if c.strip() and c != "0000"]
    # chunk2 (padrão)
    return [c for c in re.findall(r".{2}", bruto) if c.strip() and c != "00"]
