"""Hierarquia de erros de domínio da PyCobrança."""

from __future__ import annotations

__all__ = [
    "PyCobrancaError",
    "BoletoInvalido",
    "BancoNaoRegistrado",
    "CampoIgnorado",
    "DadosInvalidos",
    "DependenciaAusente",
    "LayoutGenerico",
    "ModeloInvalido",
    "OFXInvalido",
    "RetornoInvalido",
]


class PyCobrancaError(Exception):
    """Erro-base da biblioteca.

    **Todo** erro levantado pela PyCobrança herda desta classe *e* do erro
    embutido correspondente (``ValueError``, ``KeyError``, ``RuntimeError``),
    nessa ordem: ``except PyCobrancaError`` cobre a biblioteca inteira, e quem
    já tratava pelo tipo embutido continua funcionando.
    """


class BoletoInvalido(PyCobrancaError, ValueError):
    """Dados do boleto não passam nas validações (comuns ou do banco).

    Carrega a lista **estruturada** de erros em :attr:`erros` (um item por
    problema encontrado), além da mensagem única (``str(exc)`` = itens unidos
    por ``"; "``). Um consumidor — por exemplo, uma camada REST — pode mapear
    cada item de :attr:`erros` para uma resposta de validação legível.
    """

    def __init__(self, erros: str | list[str]) -> None:
        self.erros: list[str] = [erros] if isinstance(erros, str) else list(erros)
        super().__init__("; ".join(self.erros))


class BancoNaoRegistrado(PyCobrancaError, KeyError):
    """Código FEBRABAN não consta no registro de bancos."""


class DadosInvalidos(PyCobrancaError, ValueError):
    """Entrada fora do que a composição do título aceita.

    É o erro das camadas baixas — dígitos verificadores, fator de vencimento,
    código de barras e linha digitável —, onde a regra é estrutural e não tem
    banco envolvido: campo livre com 24 posições, código de barras com 43
    dígitos, sequência sem dígito para o módulo 10.

    Distinta de :class:`BoletoInvalido`, que reúne as violações **de regra de
    banco** numa lista.
    """


class ModeloInvalido(PyCobrancaError, ValueError):
    """Documento ou bloco de layout que não existe no catálogo de renderização."""


class DependenciaAusente(PyCobrancaError, RuntimeError):
    """Dependência de renderização faltando na instalação (``reportlab``, ``qrcode``)."""


class OFXInvalido(PyCobrancaError, ValueError):
    """Conteúdo não é um arquivo OFX válido (marcador ausente/estrutura quebrada)."""


class RetornoInvalido(PyCobrancaError, ValueError):
    """Arquivo de retorno CNAB vazio ou sem header reconhecível."""


class LayoutGenerico(UserWarning):
    """O retorno foi lido com um layout de reserva, não com o do banco.

    Cada banco põe os campos onde quer. Sem o mapa próprio, ``parse_cnab400`` e
    ``parse_cnab240`` recorrem a um layout genérico — o arquivo é lido até o fim
    e **nenhum erro é levantado**, mas campos podem sair de posições que não são
    as daquele banco.

    É a forma de falha mais perigosa do parsing: a saída é plausível. O Inter
    grava a ocorrência em 90–91 onde o genérico lê 109–110; o Safra usa nove
    posições de nosso número onde o genérico lê oito, cortando o DV. Nos dois
    casos o resultado passava adiante sem sinal nenhum.

    Este aviso não muda o comportamento — é o sinal que faltava. Para tratá-lo
    como erro::

        warnings.simplefilter("error", LayoutGenerico)

    Não herda de :class:`PyCobrancaError`: avisos e erros são hierarquias
    separadas em Python, e ``except PyCobrancaError`` não captura ``Warning``.
    """


class CampoIgnorado(UserWarning):
    """Um campo informado não é gravado por este layout.

    ``carteira`` existe em toda remessa porque está na base, mas nem todo layout
    tem esse campo. Oito não têm: a CrediSIS e o Santander no 400, e seis dos
    sete layouts 240, onde a FEBRABAN separa o **código da carteira** (posição 58
    do segmento P, ``1`` a ``4``) da **modalidade** do banco. Nesses, informar
    ``carteira`` não fazia nada — e não fazer nada em silêncio é o pior dos
    resultados: quem monta a remessa com o mesmo dicionário do boleto acredita
    ter escolhido a carteira, e o arquivo sai com a do padrão.

    Recusar seria mais duro do que o defeito justifica — o arquivo gerado está
    correto, só não é o que o chamador pensou ter pedido. Então sai um aviso,
    nomeando o campo que aquele layout realmente grava. Para tratá-lo como
    erro::

        warnings.simplefilter("error", CampoIgnorado)

    Não herda de :class:`PyCobrancaError`: avisos e erros são hierarquias
    separadas em Python, e ``except PyCobrancaError`` não captura ``Warning``.
    """
