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
from ..exceptions import BoletoInvalido

__all__ = ["BancoBase", "REGISTRO"]

#: código FEBRABAN -> classe do banco (preenchido pelo auto-registro)
REGISTRO: dict[str, type[BancoBase]] = {}

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
    #: Logo opt-in do banco/beneficiário para o cabeçalho do boleto: ``bytes`` de
    #: um PNG/JPEG ou caminho de arquivo. ``None`` usa o nome do banco em texto.
    #: A biblioteca **não** embute marcas registradas — o asset é do chamador.
    logo: bytes | str | None = None
    # ---- PIX / Bolepix (opcional; requer banco com suporta_pix) ----
    pix_chave: str = ""
    pix_txid: str = ""
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

        valor_br = f"{self.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
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
            "pix": self._contexto_pix(),
        }

    def _contexto_pix(self) -> dict[str, Any]:
        """Bolepix real: payload EMV + QR quando há chave PIX e o banco suporta."""
        if not self.pix_chave:
            return {"habilitado": False}
        if not self.suporta_pix:
            raise BoletoInvalido(f"banco {self.codigo} ({self.nome}) não suporta PIX")
        from ..pix import PixPayload, qr_matrix

        payload = PixPayload(
            chave=self.pix_chave,
            nome=self.cedente,
            cidade=self.cedente_cidade or "BRASIL",
            valor=self.valor,
            txid=self.pix_txid or "***",
        )
        copia_cola = payload.br_code()
        return {
            "habilitado": True,
            "copia_cola": copia_cola,
            "qrcode_matrix": qr_matrix(copia_cola),
        }
