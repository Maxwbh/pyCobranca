"""Remessa CNAB 400 do Banco Safra (422).

Layout do *Leiaute de Arquivos — Cobrança CNAB 400* (Banco Safra), seção 6.1.
Registros de 400 posições: header, N detalhes tipo 1 e trailer.

**O Safra não publica CNAB 240 para cobrança.** O manual descreve apenas o 400 —
por isso existe só este módulo.

Três desvios do layout comum, todos com efeito prático:

- **Trailer com totais.** As posições 369–376 levam a quantidade de títulos e as
  377–391 o valor somado. O trailer genérico da base leva brancos ali.
- **Multa gravada dentro do campo de abatimento** (206–218), num formato próprio
  — ver :meth:`_abatimento_ou_multa`. Os dois não cabem juntos no mesmo título.
- **Banco cobrador configurável** (140–142): o Safra atua como emissor do boleto
  ou como correspondente do Itaú (341) e do Bradesco (237), caso em que o boleto
  sai com o código do correspondente.

Sobre o nosso número: o manual admite três modalidades (seção 5). Na *Cobrança
Convencional* quem emite o boleto é o banco e o campo vai **zerado** — o número
só existe depois, no retorno. As outras duas são *Cobrança Direta*, com a empresa
emitindo a partir de uma faixa que o banco entrega antes ("O banco informará à
empresa a faixa de numeração (INICIAL E FINAL)", seção 7.1). É esta que a
biblioteca compõe, e a tabela de consistências da remessa exige o que ela produz:
nosso número *"Diferente de 0"* e com *"Dígito de Controle Válido"*.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ...core.dv import modulo11_flex
from ...exceptions import BoletoInvalido
from ..formatacao import format_valor
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaSafra400"]

#: Bancos que podem constar como encarregados da cobrança (posições 140–142).
BANCOS_COBRADORES: tuple[str, ...] = ("422", "341", "237")


def _data(valor, padrao: str = "000000") -> str:
    return valor.strftime("%d%m%y") if valor else padrao


def dv_nosso_numero(sequencial: str) -> int:
    """DV do nosso número do Safra (módulo 11, pesos 9→2 da esquerda).

    Mesma composição de :attr:`pycobranca.bancos.safra.Safra.dv_nosso_numero`;
    conferida contra os três exemplos resolvidos da seção 7.1 do manual, entre
    eles o de resto zero — *"Se na divisão o resto for 0, o dígito será 1"*.
    """
    return modulo11_flex(
        so_digitos(sequencial).zfill(8),
        da_direita=False,
        mapa={10: 0, 11: 1},
        bloco=lambda total: 11 - (total % 11),
    )


@dataclass
class RemessaSafra400(RemessaCnab400Base):
    """Remessa de cobrança do Safra.

    ``carteira`` aceita ``1`` (cobrança simples) e ``2`` (cobrança vinculada),
    os dois códigos da nota 6.1.2.
    """

    #: Banco encarregado da cobrança, posições 140–142. ``422`` é o próprio Safra;
    #: ``341`` e ``237`` são os correspondentes Itaú e Bradesco (seções 8 e 9).
    banco_cobrador: str = "422"

    #: Agência encarregada da cobrança, posições 143–147. Vazio grava zeros.
    agencia_cobradora: str = ""

    CARTEIRAS: tuple[str, ...] = ("1", "2")

    def cod_banco(self) -> str:
        return "422"

    def nome_banco(self) -> str:
        """Posições 80–94: ``BANCO SAFRA`` em X(11) seguido de 4 brancos."""
        return self._format_size("BANCO SAFRA", 15)

    def info_conta(self) -> str:
        """Posições 27–46: código do beneficiário — agência(5) + conta(9) — e 6 brancos.

        O manual chama as 14 posições de "Cod. Empresa" e detalha a composição:
        *"(5 primeiras posições agência + 9 posições conta)"*.
        """
        return f"{self._codigo_beneficiario()}{' ' * 6}"

    def _codigo_beneficiario(self) -> str:
        """As 14 posições que identificam a empresa: agência(5) + conta(9)."""
        agencia = so_digitos(self.agencia).zfill(5)
        conta = so_digitos(self.conta_corrente).zfill(9)
        return f"{agencia}{conta}"

    def complemento(self) -> str:
        """Posições 101–394: 291 brancos + número sequencial do arquivo(3)."""
        return " " * 291 + so_digitos(str(self.sequencial_remessa)).zfill(3)[-3:]

    def nosso_numero9(self, pagamento: Pagamento) -> str:
        """As 9 posições do campo nosso número (63–71): sequencial(8) + DV.

        Aceita 8 dígitos (a faixa como o banco entrega, sem DV) ou 9 (o número já
        impresso num boleto, com ele). **Completar 8 para 9 com zero à esquerda
        seria o erro clássico**: o dígito sai do fim, todo o valor desloca uma
        casa e o banco recusa na consistência de *"Dígito de Controle Válido"* —
        mas as 9 posições continuam numéricas, então passa em validador de layout.
        """
        digitos = so_digitos(pagamento.nosso_numero)
        if len(digitos) == 9:
            return digitos
        return f"{digitos.zfill(8)}{dv_nosso_numero(digitos)}"

    @staticmethod
    def _tem_multa(pagamento: Pagamento) -> bool:
        return bool(pagamento.percentual_multa) or bool(pagamento.valor_multa)

    def _abatimento_ou_multa(self, pagamento: Pagamento) -> str:
        """Posições 206–218, que o manual usa para duas coisas diferentes.

        Por padrão o campo leva o **valor do abatimento**, 9(11)V99. Quando o
        título tem multa, a nota 6.1.8 manda gravar ali, no lugar, um registro
        com forma própria: data a partir da qual a multa vale (206–211), o
        percentual em 99v99 (212–215) e zeros (216–218). É por isso que multa e
        abatimento não convivem no mesmo título — :meth:`validar` recusa os dois
        juntos em vez de deixar um sobrescrever o outro em silêncio.
        """
        if not self._tem_multa(pagamento):
            return format_valor(pagamento.valor_abatimento, 13)
        percentual = format_valor(pagamento.percentual_multa, 4)
        return f"{_data(pagamento.data_multa)}{percentual}000"

    def _primeira_instrucao(self, pagamento: Pagamento) -> str:
        """Posições 157–158. A multa exige o código 16 aqui (nota 6.1.5)."""
        if self._tem_multa(pagamento):
            return "16"
        return self._format_size(pagamento.cod_primeira_instrucao, 2)

    def validar(self) -> None:
        super().validar()
        erros = []
        if self.carteira not in self.CARTEIRAS:
            validas = ", ".join(self.CARTEIRAS)
            erros.append(f"carteira {self.carteira!r} não suportada (use uma de: {validas})")
        if self.banco_cobrador not in BANCOS_COBRADORES:
            validos = ", ".join(BANCOS_COBRADORES)
            erros.append(f"banco_cobrador {self.banco_cobrador!r} inválido (use um de: {validos})")
        for pagamento in self.pagamentos:
            erros.extend(self._erros_do_pagamento(pagamento))
        if erros:
            raise BoletoInvalido(erros)

    def _erros_do_pagamento(self, pagamento: Pagamento) -> list[str]:
        erros = []
        digitos = so_digitos(pagamento.nosso_numero)
        if len(digitos) not in (8, 9):
            erros.append(
                f"nosso número {pagamento.nosso_numero!r} deve ter 8 dígitos (sem DV) ou 9 (com DV)"
            )
        elif not int(digitos):
            # Consistência 01 da remessa: "Numérico, diferente de 0". Zeros são a
            # marca da cobrança convencional, em que quem numera é o banco — e aí
            # não há boleto a compor antes do retorno.
            erros.append("nosso número não pode ser zero na cobrança direta")
        elif len(digitos) == 9 and int(digitos[8]) != dv_nosso_numero(digitos[:8]):
            esperado = dv_nosso_numero(digitos[:8])
            erros.append(
                f"nosso número {pagamento.nosso_numero!r}: DV {digitos[8]} inválido "
                f"(esperado {esperado})"
            )
        if self._tem_multa(pagamento):
            erros.extend(self._erros_da_multa(pagamento))
        return erros

    def _erros_da_multa(self, pagamento: Pagamento) -> list[str]:
        """A multa do Safra só existe em percentual, com data, e sem abatimento."""
        erros = []
        if pagamento.valor_multa and not pagamento.percentual_multa:
            erros.append(
                "o Safra grava a multa em percentual (nota 6.1.8); "
                "use percentual_multa em vez de valor_multa"
            )
        if pagamento.valor_abatimento:
            erros.append(
                "multa e abatimento ocupam o mesmo campo (206–218) e não cabem no mesmo título"
            )
        if not pagamento.data_multa:
            erros.append("data_multa é obrigatória quando há multa (posições 206–211)")
        elif pagamento.data_vencimento and pagamento.data_multa <= pagamento.data_vencimento:
            erros.append("data_multa deve ser posterior ao vencimento (nota 6.1.5)")
        return erros

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        doc_cedente = so_digitos(self.documento_cedente)
        doc_sacado = so_digitos(pagamento.documento_sacado)

        registro = (
            "1"  # 001        tipo de registro
            + ("01" if len(doc_cedente) <= 11 else "02")  # 002-003  cód. inscrição
            + doc_cedente.zfill(14)  # 004-017    núm. inscrição
            + self._codigo_beneficiario()  # 018-031    cód. empresa
            + " " * 6  # 032-037
            + self._format_size(pagamento.numero, 25)  # 038-062    uso da empresa
            + self.nosso_numero9(pagamento)  # 063-071    nosso número
            + " " * 30  # 072-101
            + "0"  # 102        código IOF — 0 = isento
            + "00"  # 103-104    moeda — 00 = real
            + " "  # 105
            + self._format_size(pagamento.dias_protesto, 2)  # 106-107  3ª instrução
            + self.carteira[:1]  # 108        carteira
            + self._format_size(pagamento.identificacao_ocorrencia, 2)  # 109-110
            + self._format_size(pagamento.documento, 10)  # 111-120    seu número
            + _data(pagamento.data_vencimento)  # 121-126    vencimento
            + format_valor(pagamento.valor, 13)  # 127-139    valor do título
            + self.banco_cobrador  # 140-142    banco cobrador
            + so_digitos(self.agencia_cobradora).zfill(5)  # 143-147  agência cobradora
            + self._format_size(pagamento.especie_titulo, 2)  # 148-149  espécie
            + (self.aceite or "N")[:1]  # 150        aceite
            + _data(pagamento.data_emissao)  # 151-156    emissão
            + self._primeira_instrucao(pagamento)  # 157-158    1ª instrução
            + self._format_size(pagamento.cod_segunda_instrucao, 2)  # 159-160  2ª instrução
            + format_valor(pagamento.valor_mora, 13)  # 161-173    juros por dia
            + _data(pagamento.data_desconto)  # 174-179    desconto até
            + format_valor(pagamento.valor_desconto, 13)  # 180-192    valor do desconto
            + format_valor(pagamento.valor_iof, 13)  # 193-205    IOF
            + self._abatimento_ou_multa(pagamento)  # 206-218    abatimento ou multa
            + ("01" if len(doc_sacado) <= 11 else "02")  # 219-220  cód. inscrição pagador
            + doc_sacado.zfill(14)  # 221-234    núm. inscrição pagador
            + self._format_size(pagamento.nome_sacado, 40)  # 235-274
            + self._format_size(pagamento.endereco_sacado, 40)  # 275-314
            + self._format_size(pagamento.bairro_sacado, 10)  # 315-324
            + " " * 2  # 325-326
            + so_digitos(pagamento.cep_sacado).zfill(8)  # 327-334
            + self._format_size(pagamento.cidade_sacado, 15)  # 335-349
            + self._format_size(pagamento.uf_sacado, 2)  # 350-351
            + self._format_size(pagamento.nome_avalista, 30)  # 352-381
            + " " * 7  # 382-388
            + self.banco_cobrador  # 389-391    banco emitente do boleto
            + so_digitos(str(self.sequencial_remessa)).zfill(3)[-3:]  # 392-394
            + str(sequencial).rjust(6, "0")  # 395-400
        )
        return registro

    def monta_trailer(self, sequencial: int) -> str:
        """Trailer do Safra: quantidade em 369–376 e valor somado em 377–391.

        O trailer genérico da base leva brancos nas duas faixas; o Safra confere
        os totais contra os detalhes.
        """
        total = sum(float(pagamento.valor or 0) for pagamento in self.pagamentos)
        return (
            "9"
            + " " * 367  # 002-368
            + str(len(self.pagamentos)).rjust(8, "0")  # 369-376
            + format_valor(total, 15)  # 377-391
            + so_digitos(str(self.sequencial_remessa)).zfill(3)[-3:]  # 392-394
            + str(sequencial).rjust(6, "0")  # 395-400
        )
