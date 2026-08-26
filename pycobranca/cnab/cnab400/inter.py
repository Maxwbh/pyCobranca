"""Remessa CNAB 400 do Banco Inter (077).

Layout do *Manual CNAB 400 — Emissão boletos de cobrança* (Inter, **V9, 06/07/2026**),
seção 4. Registros de 400 posições: header, N detalhes tipo 1 e trailer.

**O Inter não tem CNAB 240 para cobrança.** O manual é explícito na apresentação:
"o Inter disponibiliza duas opções para a sua empresa: a troca de arquivos com layout
CNAB400, ou a integração via API" — e não menciona 240 uma única vez. O manual CNAB240
que o banco publica é de **pagamentos**, produto diferente e fora do escopo desta
biblioteca. Por isso existe só este módulo.

Diferenças em relação ao layout comum dos outros bancos:

- **Header sem agência/conta.** As posições 27 a 46 são brancos; a conta identifica-se
  no detalhe, não no header. :meth:`info_conta` devolve 20 espaços por isso.
- **Trailer com a contagem de boletos** nas posições 2 a 7 — o trailer genérico da base
  leva brancos ali, então :meth:`monta_trailer` é redefinido.
- **Nosso número zerado nas carteiras 112 e 121.** Ali quem numera é o banco (item 13 do
  tipo 1: "Se carteira 112 ou 121, envie zeros"). A biblioteca só emite boleto na 110, mas
  a remessa aceita as três: mandar o arquivo é justamente como se obtém o número nas outras
  duas. A **121** entrou no manual depois da v2.2 e é irmã da 112 — a seção 6.1 põe as duas
  do mesmo lado: *"o Inter já realiza a emissão dos boletos e registro dos nossos números"*.

Os registros **tipo 2** (mensagens 2ª a 5ª e descontos 2 e 3), **tipo 3** (e-mail do pagador
e beneficiário final) e **tipo 4** (nota fiscal, para produtos de crédito com duplicata) são
opcionais no manual e não são emitidos aqui — assim como o **tipo 2 do retorno**, que só
aparece quando o tipo 4 foi enviado.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.documentos import so_digitos
from ...core.dv import modulo10
from ...exceptions import BoletoInvalido
from ..formatacao import format_valor
from ..pagamento import Pagamento
from .base import RemessaCnab400Base

__all__ = ["RemessaInter400"]


def _data(valor, padrao: str = "000000") -> str:
    return valor.strftime("%d%m%y") if valor else padrao


@dataclass
class RemessaInter400(RemessaCnab400Base):
    """Remessa de cobrança do Inter.

    ``carteira`` aceita ``110`` (nosso número da faixa reservada, informado no arquivo),
    ``112`` e ``121`` (nosso número zerado; o banco devolve no retorno).
    """

    #: Dias após o vencimento em que o pagamento ainda é aceito (item 19, "01" a "60").
    dias_limite_pagamento: str = "60"

    CARTEIRAS: tuple[str, ...] = ("110", "112", "121")

    def cod_banco(self) -> str:
        return "077"

    def nome_banco(self) -> str:
        return self._format_size("INTER", 15)

    def info_conta(self) -> str:
        """Posições 27–46 do header: brancos. O Inter não identifica a conta aqui."""
        return " " * 20

    def complemento(self) -> str:
        """Posições 101–394: 10 brancos + sequencial da remessa(7) + 277 brancos."""
        sequencial = self._format_size(str(self.sequencial_remessa), 7)
        return " " * 10 + sequencial + " " * 277

    def validar(self) -> None:
        super().validar()
        erros = []
        if self.carteira not in self.CARTEIRAS:
            validas = ", ".join(self.CARTEIRAS)
            erros.append(f"carteira {self.carteira!r} não suportada (use uma de: {validas})")
        if not (
            self.dias_limite_pagamento.isdigit() and 1 <= int(self.dias_limite_pagamento) <= 60
        ):
            erros.append("dias_limite_pagamento deve estar entre 01 e 60")
        # Item 06 é obrigatório no manual. Assumir "0" grava um dígito que não é o
        # da conta, e o banco recusa o arquivo — melhor cobrar aqui.
        if not so_digitos(self.digito_conta):
            erros.append("digito_conta é obrigatório (item 06 do registro tipo 1)")
        if self.carteira == "110":
            for pagamento in self.pagamentos:
                if len(so_digitos(pagamento.nosso_numero)) not in (10, 11):
                    erros.append(
                        f"nosso número {pagamento.nosso_numero!r} deve ter 10 dígitos "
                        "(sem DV) ou 11 (com DV) na carteira 110"
                    )
        if erros:
            raise BoletoInvalido(erros)

    def _nosso_numero11(self, pagamento: Pagamento) -> str:
        """As 11 posições do item 13: nosso número (10) + DV.

        Aceita as duas formas porque as duas aparecem na prática: a faixa que o
        Inter entrega vem sem DV, e o número já impresso num boleto vem com ele.

        **Completar com zero à esquerda seria o erro clássico.** Um número de 10
        dígitos preenchido para 11 vira ``0`` + número: o dígito some, o valor
        inteiro desloca, e o banco recusa com *"dígito verificador inválido para
        o nosso número"*. Pior — as 11 posições continuam numéricas, então isso
        **passa** num validador de layout e só quebra no processamento.
        """
        digitos = so_digitos(pagamento.nosso_numero)
        if len(digitos) == 11:
            return digitos
        agencia = so_digitos(self.agencia).zfill(4)
        return f"{digitos}{modulo10(f'{agencia}{self.carteira.zfill(3)}{digitos}')}"

    @staticmethod
    def _codigo_mora(pagamento: Pagamento) -> str:
        """Traduz o ``tipo_mora`` da biblioteca para o item 25 do Inter.

        A biblioteca segue a FEBRABAN, onde ``"3"`` é *isento*; o Inter usa
        ``"0"`` para sem juros. Sem esta tradução, o padrão ``"3"`` cairia num
        código que o Inter não define.
        """
        return {"1": "1", "2": "2"}.get(str(pagamento.tipo_mora), "0")

    def monta_detalhe(self, pagamento: Pagamento, sequencial: int) -> str:
        # Item 13: na 112 quem numera é o banco, e o campo vai zerado.
        nosso_numero = self._nosso_numero11(pagamento) if self.carteira == "110" else "0" * 11
        doc_sacado = "".join(c for c in pagamento.documento_sacado if c.isdigit())
        tipo_inscricao = "01" if len(doc_sacado) <= 11 else "02"

        registro = (
            "1"  # 001        item 01 — identificação do registro
            + " " * 19  # 002-020    item 02
            + self.carteira.zfill(3)  # 021-023    item 03
            + "".join(c for c in self.agencia if c.isdigit()).zfill(4)  # 024-027  item 04
            + "".join(c for c in self.conta_corrente if c.isdigit()).zfill(9)  # 028-036 item 05
            + (self.digito_conta or "0")[:1]  # 037        item 06
            + self._format_size(pagamento.numero, 25)  # 038-062    item 07
            + " " * 3  # 063-065    item 08
            + str(pagamento.codigo_multa or "0")[:1]  # 066        item 09
            + format_valor(pagamento.valor_multa, 13)  # 067-079    item 10
            + format_valor(pagamento.percentual_multa, 4)  # 080-083    item 11
            + _data(pagamento.data_multa)  # 084-089    item 12
            + nosso_numero  # 090-100    item 13
            + " " * 8  # 101-108    item 14
            + self._format_size(pagamento.identificacao_ocorrencia, 2)  # 109-110  item 15
            + self._format_size(pagamento.documento, 10)  # 111-120    item 16
            + _data(pagamento.data_vencimento)  # 121-126    item 17
            + format_valor(pagamento.valor, 13)  # 127-139    item 18
            + self.dias_limite_pagamento.zfill(2)  # 140-141    item 19
            + " " * 6  # 142-147    item 20
            + "01"  # 148-149    item 21 — espécie
            + "N"  # 150        item 22
            + " " * 6  # 151-156    item 23 — o banco carimba a emissão
            + " " * 3  # 157-159    item 24
            + self._codigo_mora(pagamento)  # 160        item 25
            + format_valor(pagamento.valor_mora, 13)  # 161-173    item 26
            + format_valor(pagamento.percentual_mora, 4)  # 174-177    item 27
            + _data(pagamento.data_mora)  # 178-183    item 28
            + str(pagamento.cod_desconto or "0")[:1]  # 184        item 29
            + format_valor(pagamento.valor_desconto, 13)  # 185-197    item 30
            + format_valor(pagamento.percentual_desconto, 4)  # 198-201  item 31
            + _data(pagamento.data_desconto)  # 202-207    item 32
            + " " * 13  # 208-220    item 33
            + tipo_inscricao  # 221-222    item 34
            + doc_sacado.zfill(14)  # 223-236    item 35
            + self._format_size(pagamento.nome_sacado, 40)  # 237-276    item 36
            + self._format_size(pagamento.endereco_sacado, 38)  # 277-314  item 37
            + self._format_size(pagamento.uf_sacado, 2)  # 315-316    item 38
            + "".join(c for c in pagamento.cep_sacado if c.isdigit()).zfill(8)  # 317-324 item 39
            + self._format_size(pagamento.mensagem, 70)  # 325-394  item 40
            + str(sequencial).rjust(6, "0")  # 395-400    item 41
        )
        return registro

    def nome_arquivo(self) -> str:
        """Nome que o Internet Banking do Inter exige no upload (manual, seção 3.1).

        ``CI400_001_???????.REM``, onde as sete posições são o **mesmo** sequencial
        gravado no header (111–117). O manual condiciona o upload a essa igualdade,
        e é fácil errar: a biblioteca gera o conteúdo, quem nomeia é o chamador.
        Gerar o nome aqui elimina a chance de os dois divergirem.
        """
        return f"CI400_001_{so_digitos(str(self.sequencial_remessa)).zfill(7)}.REM"

    def monta_trailer(self, sequencial: int) -> str:
        """Trailer do Inter: a contagem de boletos ocupa as posições 2 a 7.

        O trailer genérico da base leva brancos ali; mandar o arquivo com esse campo em
        branco é rejeição na entrada.
        """
        return (
            "9"
            + str(len(self.pagamentos)).rjust(6, "0")
            + " " * 387
            + str(sequencial).rjust(6, "0")
        )
