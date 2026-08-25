"""Base dos bancos: o boleto de cada banco herda de :class:`BancoBase`.

Cada subclasse declara os metadados do banco (``codigo``, ``nome``,
``digito_banco``, ``carteiras``, ``suporta_pix``) e implementa
:meth:`campo_livre` (as 25 posições específicas), além de poder estender
:meth:`validar`. O auto-registro via ``__init_subclass__`` alimenta o
registro consultável em :mod:`pycobranca.bancos`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from ..boleto.codigo_barras import montar_codigo_barras
from ..boleto.linha_digitavel import linha_digitavel as _linha_digitavel
from ..core.datas import fator_vencimento
from ..core.documentos import so_alfanumerico, so_digitos, validar_cnpj, validar_cpf
from ..exceptions import BoletoInvalido, DadosInvalidos

__all__ = ["BancoBase", "REGISTRO"]

#: código FEBRABAN -> classe do banco (preenchido pelo auto-registro)
REGISTRO: dict[str, type[BancoBase]] = {}

#: Os quatro que somam/subtraem do valor do documento, na ordem da faixa
#: FEBRABAN, mais o total. Deduções entram negativas no cálculo de
#: ``valor_cobrado``; acréscimos, positivas.
_TOTALIZADORES_OPCIONAIS = (
    "desconto_abatimento",
    "outras_deducoes",
    "mora_multa",
    "outros_acrescimos",
    "valor_cobrado",
)

#: rótulos amigáveis para as mensagens de erro de tamanho de campo
_ROTULOS_CAMPOS: dict[str, str] = {
    "agencia": "agência",
    "conta": "conta",
    "convenio": "convênio",
    "nosso_numero": "nosso número",
    "posto": "posto",
    "portfolio": "portfolio",
    "incremento": "incremento",
    "numero_contrato": "número do contrato",
    "digito_agencia": "dígito da agência",
    "digito_conta": "dígito da conta",
    "variacao": "variação",
    "byte_idt": "byte de identificação",
    "quantidade": "quantidade de parcelas",
}


@dataclass
class BancoBase:
    """Boleto-base: campos comuns + composição de código de barras/linha.

    Subclasses definem os metadados de classe e o :meth:`campo_livre`.
    """

    # ---- metadados por banco (sobrescritos nas subclasses) ----
    codigo: ClassVar[str] = ""
    nome: ClassVar[str] = ""
    digito_banco: ClassVar[str] = ""
    carteiras: ClassVar[tuple[str, ...]] = ()
    suporta_pix: ClassVar[bool] = False
    #: regras de tamanho por campo numérico: ``nome_do_campo -> (mínimo, máximo)``
    #: em dígitos (após remover a máscara). O máximo trava o formato do campo
    #: livre; o mínimo pega campo vazio/curto. As carteiras válidas ficam em
    #: :attr:`carteiras` (conjunto validado à parte).
    regras_campos: ClassVar[dict[str, tuple[int, int]]] = {}

    # ---- campos do título ----
    valor: Decimal | str | float = "0"
    cedente: str = ""
    cedente_documento: str = ""
    cedente_endereco: str = ""
    agencia: str = ""
    conta: str = ""
    carteira: str = ""
    convenio: str = ""  # convênio/código do cedente-beneficiário (BB, Santander, Caixa)
    nosso_numero: str = ""
    data_vencimento: date | None = None
    data_documento: date | None = None
    numero_documento: str = ""
    sacado: str = ""
    sacado_documento: str = ""
    sacado_endereco: str = ""
    especie_documento: str = "DM"
    aceite: str = "N"
    especie_moeda: str = "R$"
    quantidade: str = ""
    local_pagamento: str = "Pagável em qualquer banco até o vencimento"
    instrucoes: list[str] = field(default_factory=list)
    demonstrativo: str = ""
    sacador_avalista: str = ""
    # ---- totalizadores impressos no boleto (opcionais) ----
    #: Os cinco campos da faixa FEBRABAN. Ficam **em branco por padrão**: no
    #: boleto comum quem os preenche é o caixa, no ato do pagamento. Informe-os
    #: quando o valor já é conhecido na emissão — desconto por pontualidade,
    #: abatimento negociado, ou um boleto reemitido com mora apurada.
    desconto_abatimento: Decimal | str | float | None = None
    outras_deducoes: Decimal | str | float | None = None
    mora_multa: Decimal | str | float | None = None
    outros_acrescimos: Decimal | str | float | None = None
    #: Deixe ``None`` para a biblioteca somar os quatro anteriores ao valor do
    #: documento. Informe explicitamente para sobrepor esse cálculo.
    valor_cobrado: Decimal | str | float | None = None
    #: Logo opt-in do banco/beneficiário para o cabeçalho do boleto: ``bytes`` de
    #: um PNG/JPEG ou caminho de arquivo. ``None`` usa o nome do banco em texto.
    #: A biblioteca **não** embute marcas registradas — o asset é do chamador.
    logo: bytes | str | None = None
    # ---- PIX / Bolepix (opcional; requer banco com suporta_pix) ----
    #: Payload EMV **pronto**, devolvido pelo banco ao registrar a cobrança
    #: (arquivo retorno ou API do PSP). Quando informado, é ele que vai no QR —
    #: é o Bolepix de verdade, vinculado ao título e com baixa automática.
    #:
    #: Tem precedência sobre :attr:`pix_chave`: se o banco já produziu o payload,
    #: montar outro localmente seria imprimir um QR que ele não conhece.
    pix_copia_cola: str = ""
    #: Chave PIX do recebedor. Monta um BR Code **estático**, que credita a chave
    #: mas **não liquida o título** no banco — ver ``docs/07-pix.md``.
    pix_chave: str = ""
    #: Identificador da transação (campo 62-05). Até 25 caracteres ``A-Za-z0-9``.
    #:
    #: **Vazio, é derivado do nosso número.** No QR avulso o identificador é o que
    #: permite reconhecer o crédito no extrato: sem ele o recebimento fica órfão e
    #: o título parece não pago. Deixar isso na lembrança de quem chama garantia
    #: que uma parte dos boletos sairia sem — então o padrão passa a identificar.
    #: Para abrir mão de propósito, informe ``"***"``.
    pix_txid: str = ""
    #: Texto livre no campo 26-02 (até 40, sem acentos). Descreve a cobrança;
    #: não substitui o ``pix_txid`` como identificador.
    pix_observacao: str = ""
    cedente_cidade: str = ""
    # ---- campos auxiliares usados por bancos específicos ----
    variacao: str = ""  # Sicoob, Banestes
    posto: str = ""  # Sicredi
    byte_idt: str = ""  # Sicredi (1=agência, 2-9=beneficiário)
    digito_convenio: str = ""  # Banrisul
    digito_conta: str = ""  # Banco do Nordeste, Banestes, Safra, Unicred
    digito_agencia: str = ""  # Safra
    portfolio: str = ""  # Citibank
    incremento: str = ""  # BRB/Banco de Brasília
    numero_contrato: str = ""  # Sicoob (carteira 9)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.codigo:
            REGISTRO[cls.codigo.zfill(3)] = cls

    def __post_init__(self) -> None:
        self.valor = Decimal(str(self.valor))
        for campo in _TOTALIZADORES_OPCIONAIS:
            bruto = getattr(self, campo)
            if bruto is not None:
                setattr(self, campo, Decimal(str(bruto)))

    # ---- derivados ----
    @property
    def valor_centavos(self) -> int:
        return int((Decimal(str(self.valor)) * 100).quantize(Decimal("1")))

    @property
    def fator_vencimento(self) -> int:
        if self.data_vencimento is None:
            raise BoletoInvalido("data_vencimento é obrigatória")
        return fator_vencimento(self.data_vencimento)

    def campo_livre(self) -> str:
        """25 posições específicas do banco (implementar na subclasse)."""
        raise NotImplementedError

    @property
    def codigo_barras(self) -> str:
        self.validar()
        return montar_codigo_barras(
            self.codigo, self.fator_vencimento, self.valor_centavos, self.campo_livre()
        )

    @property
    def linha_digitavel(self) -> str:
        return _linha_digitavel(self.codigo_barras)

    def nosso_numero_formatado(self) -> str:
        return self.nosso_numero

    def agencia_conta_formatado(self) -> str:
        return f"{self.agencia} / {self.conta}"

    # ---- validação ----
    def validar(self) -> None:
        """Validações comuns; subclasses estendem com regras próprias."""
        erros: list[str] = []
        if self.valor_centavos <= 0:
            erros.append("valor deve ser positivo")
        if self.data_vencimento is None:
            erros.append("data_vencimento é obrigatória")
        if not self.cedente:
            erros.append("cedente é obrigatório")
        if self.carteiras and self.carteira not in self.carteiras:
            validas = ", ".join(self.carteiras)
            erros.append(f"carteira {self.carteira!r} não suportada (use uma de: {validas})")
        for campo, (minimo, maximo) in self.regras_campos.items():
            rotulo = _ROTULOS_CAMPOS.get(campo, campo)
            digitos = so_digitos(getattr(self, campo) or "")
            if len(digitos) < minimo:
                erros.append(f"{rotulo} deve ter no mínimo {minimo} dígito(s)")
            elif len(digitos) > maximo:
                erros.append(f"{rotulo} deve ter no máximo {maximo} dígitos")
        # CPF é numérico; CNPJ pode ser alfanumérico (IN RFB 2.229/2024)
        doc = so_alfanumerico(self.cedente_documento)
        if doc and not (validar_cpf(doc) or validar_cnpj(doc)):
            erros.append("cedente_documento inválido (CPF/CNPJ)")
        doc = so_alfanumerico(self.sacado_documento)
        if doc and not (validar_cpf(doc) or validar_cnpj(doc)):
            erros.append("sacado_documento inválido (CPF/CNPJ)")
        if erros:
            raise BoletoInvalido(erros)

    # ---- serialização / integração com render ----
    def to_dict(self) -> dict[str, Any]:
        """Representação JSON-friendly (nomes prontos para API REST)."""
        return {
            "banco": self.codigo,
            "valor": str(self.valor),
            "cedente": self.cedente,
            "documento_cedente": self.cedente_documento,
            "agencia": self.agencia,
            "conta_corrente": self.conta,
            "carteira": self.carteira,
            "nosso_numero": self.nosso_numero,
            "data_vencimento": self.data_vencimento.isoformat() if self.data_vencimento else None,
            "sacado": self.sacado,
            "sacado_documento": self.sacado_documento,
            "codigo_barras": self.codigo_barras,
            "linha_digitavel": self.linha_digitavel,
        }

    def contexto_render(self) -> dict[str, Any]:
        """Contexto pronto para os backends de renderização (ver doc 11)."""

        def data_br(d: date | None) -> str:
            return d.strftime("%d/%m/%Y") if d else ""

        def moeda(v: Decimal | str | float | None) -> str:
            """Máscara brasileira; campo não informado imprime vazio, não ``0,00``.

            Reconverte para ``Decimal`` como ``valor_centavos`` já fazia: o
            ``__post_init__`` normaliza o que chega pelo construtor, mas os
            campos são públicos e mutáveis, e um ``"12.00"`` atribuído depois
            estourava aqui com ``ValueError: Unknown format code 'f'``.
            """
            if v is None:
                return ""
            try:
                v = Decimal(str(v))
            except ArithmeticError as erro:
                raise DadosInvalidos(f"valor monetário inválido: {v!r}") from erro
            return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        valor_br = moeda(self.valor)
        banco: dict[str, Any] = {
            "codigo_dv": f"{self.codigo}-{self.digito_banco}",
            "nome": self.nome,
            "sigla": self.nome[:2].upper(),
        }
        if self.logo is not None:
            banco["logo"] = self.logo
        return {
            "banco": banco,
            "linha_digitavel": self.linha_digitavel,
            "codigo_barras": self.codigo_barras,
            "local_pagamento": self.local_pagamento,
            "vencimento": data_br(self.data_vencimento),
            "valor_documento": valor_br,
            "beneficiario": {
                "nome": self.cedente,
                "documento": self.cedente_documento,
                "endereco": self.cedente_endereco,
                "agencia_codigo": self.agencia_conta_formatado(),
            },
            "documento": {
                "data": data_br(self.data_documento),
                "numero": self.numero_documento,
                "especie": self.especie_documento,
                "aceite": self.aceite,
                "data_processamento": data_br(self.data_documento),
            },
            "nosso_numero": self.nosso_numero_formatado(),
            "carteira": self.carteira,
            "especie_moeda": self.especie_moeda,
            "quantidade": self.quantidade,
            "instrucoes": list(self.instrucoes),
            "pagador": {
                "nome": self.sacado,
                "documento": self.sacado_documento,
                "endereco": self.sacado_endereco,
            },
            "sacador_avalista": self.sacador_avalista,
            "demonstrativo": self.demonstrativo,
            # Sempre em branco: a faixa de desconto/mora/acréscimo e o total são
            # preenchidos **pelo caixa** no momento do pagamento, não pelo
            # beneficiário. A regra de encargo do título vai em ``instrucoes``
            # ("após o vencimento, multa de 2% e juros de 1% ao mês"), que é o que
            # o caixa lê para calcular. Imprimir valor aqui antecipa uma conta que
            # não é do emissor e induz o pagador a erro.
            "totalizadores": dict.fromkeys(_TOTALIZADORES_OPCIONAIS, ""),
            "pix": self._contexto_pix(),
        }

    def txid_do_titulo(self) -> str:
        """Identificador derivado do nosso número, para o campo 62-05.

        Mantém só ``A-Za-z0-9`` e corta em 25, que é o que o padrão aceita — o
        nosso número formatado costuma trazer ``/`` e ``-``. Devolve ``"***"``
        (ausente, no padrão EMV) quando não sobra nada, em vez de montar um
        payload inválido.

        É o que amarra o crédito PIX ao título na conciliação por OFX.
        """
        if not so_digitos(self.nosso_numero):
            # Sem nosso número, ``nosso_numero_formatado()`` preenche com zeros e
            # ainda calcula o dígito em cima deles: sairia um txid plausível e sem
            # significado, que não casa com título nenhum na conciliação — ou casa
            # com o errado. Melhor declarar ausente.
            return "***"
        alfanumericos = "".join(c for c in self.nosso_numero_formatado() if c.isalnum())
        return alfanumericos[:25] or "***"

    def _contexto_pix(self) -> dict[str, Any]:
        """QR do PIX, em uma de duas naturezas — e o contexto diz qual.

        Com :attr:`pix_copia_cola`, o payload é o que o **banco** devolveu ao
        registrar a cobrança: QR dinâmico, vinculado ao título, com baixa
        automática. É o Bolepix.

        Com :attr:`pix_chave`, o payload é montado aqui e é **estático**: paga a
        chave, mas o banco não sabe que aquele pagamento quita este título. O
        título segue em aberto até conciliação manual — daí ``vinculado`` sair no
        contexto, para quem renderiza ou expõe não confundir os dois.
        """
        from ..pix import qr_matrix

        if self.pix_copia_cola:
            copia_cola = self.pix_copia_cola.strip()
            return {
                "habilitado": True,
                "vinculado": True,
                "copia_cola": copia_cola,
                "qrcode_matrix": qr_matrix(copia_cola),
            }
        if not self.pix_chave:
            return {"habilitado": False}
        if not self.suporta_pix:
            raise BoletoInvalido(f"banco {self.codigo} ({self.nome}) não suporta PIX")
        from ..pix import PixPayload

        payload = PixPayload(
            chave=self.pix_chave,
            nome=self.cedente,
            cidade=self.cedente_cidade or "BRASIL",
            valor=self.valor,
            txid=self.pix_txid or self.txid_do_titulo(),
            info_adicional=self.pix_observacao,
        )
        copia_cola = payload.br_code()
        return {
            "habilitado": True,
            "vinculado": False,
            "copia_cola": copia_cola,
            "qrcode_matrix": qr_matrix(copia_cola),
        }
