"""Valores-limite por banco, nos dois artefatos: boleto e remessa CNAB.

Testes de exemplo mostram que um caso funciona. Estes mostram o que acontece
nas bordas — e as bordas são onde os defeitos deste pacote apareceram:

- ``str.rjust``/``str.zfill`` **preenchem mas nunca cortam**. Um valor maior que
  o campo atravessa para a posição seguinte, e como o CNAB é posicional, todo o
  resto do registro desloca. O arquivo continua parecendo válido — o banco é que
  lê o vencimento no lugar do valor. Foi assim em quatro remessas.
- O campo livre do código de barras tem **25 posições fixas**. Um dígito a mais
  em qualquer campo que entre nele quebra o boleto inteiro, e o erro só aparecia
  na montagem do código de barras, sem dizer qual campo o causou.

O contrato que estes testes prendem é o mesmo nos dois casos: **ou o valor é
recusado com um erro do pacote que nomeia o campo, ou o artefato sai no tamanho
certo.** Nunca sair calado e errado.

Os casos vêm de ``regras_campos`` (``{campo: (mínimo, máximo)}`` em dígitos) de
cada banco: sem dados, 1 caractere, o máximo declarado e máximo+1.

**O que estes testes ainda não cobrem.** A recusa na remessa vem de duas fontes:
o limite do campo (``campo_numerico``, que diz *"conta_corrente: '999999999' não
cabe em 8 posições"*) e a conferência de tamanho do registro (que diz apenas
*"registro 2 com 417 posições"*). Hoje a maioria dos campos cai na segunda: o
arquivo errado nunca sai, mas a mensagem não nomeia o campo. Levar todos os
campos de todas as remessas para a primeira é uma varredura mecânica por vinte
módulos, e cada um precisa do layout do banco para saber a largura — está fora
do que estes testes prendem.
"""

from __future__ import annotations

import dataclasses
import warnings

import pytest
import test_cnab_remessa as remessas
from exemplos_boletos import EXEMPLOS
from test_validacao_externa import _confere

from pycobranca.bancos.base import BancoBase
from pycobranca.exceptions import CampoIgnorado, PyCobrancaError

# --------------------------------------------------------------------------- #
# Boleto
# --------------------------------------------------------------------------- #


def _casos_de_limite():
    """(banco, campo, rótulo, valor, deve_aceitar) para cada regra declarada."""
    casos = []
    for nome in sorted(EXEMPLOS):
        modelo = EXEMPLOS[nome]["boleto"]()
        for campo, (minimo, maximo) in sorted(modelo.regras_campos.items()):
            casos += [
                (nome, campo, "vazio", "", minimo == 0),
                (nome, campo, "1 dígito", "1", minimo <= 1 <= maximo),
                (nome, campo, f"máximo ({maximo})", "9" * maximo, True),
                (nome, campo, f"máximo+1 ({maximo + 1})", "9" * (maximo + 1), False),
            ]
    return casos


@pytest.mark.parametrize(
    ("banco", "campo", "caso", "valor", "deve_aceitar"),
    _casos_de_limite(),
    ids=lambda v: v if isinstance(v, str) else repr(v),
)
def test_boleto_no_limite_do_campo_honra_a_regra_declarada(
    banco: str, campo: str, caso: str, valor: str, deve_aceitar: bool
) -> None:
    """Aceitar e recusar são as duas metades da promessa de ``regras_campos``.

    Recusar o que passa do máximo é o óbvio. Aceitar o máximo é o que não era
    óbvio: é justamente ali que o campo livre estourava, com a validação
    passando e o código de barras quebrando depois.
    """
    boleto = EXEMPLOS[banco]["boleto"]()
    setattr(boleto, campo, valor)

    if not deve_aceitar:
        with pytest.raises(PyCobrancaError):
            boleto.validar()
            _confere(f"{banco}/{campo}/{caso}", boleto)
        return

    boleto.validar()
    # O verificador não usa nada do núcleo: reimplementa as regras FEBRABAN do
    # zero, como faria o app de um banco lendo o boleto impresso.
    _confere(f"{banco}/{campo}/{caso}", boleto)


def _campos_de_texto(modelo: BancoBase) -> list[str]:
    return [
        f.name
        for f in dataclasses.fields(modelo)
        if isinstance(getattr(modelo, f.name, None), str) and f.name != "carteira"
    ]


@pytest.mark.parametrize("banco", sorted(EXEMPLOS))
def test_nenhum_campo_do_titulo_estoura_o_campo_livre(banco: str) -> None:
    """Varre **todos** os campos de texto, não só os que têm regra declarada.

    É esta varredura que encontra a regra que ninguém declarou — foi assim que
    apareceram ``digito_conta``, ``digito_agencia``, ``variacao``, ``byte_idt`` e
    a parcela do Sicoob, todos entrando no campo livre sem limite nenhum. Sem
    ela, o teste acima só confirma o que já se sabia.
    """
    modelo = EXEMPLOS[banco]["boleto"]()
    estouros = []
    for campo in _campos_de_texto(modelo):
        for valor in ("9" * 4, "9" * 9, "9" * 15, "9" * 30):
            boleto = EXEMPLOS[banco]["boleto"]()
            setattr(boleto, campo, valor)
            try:
                boleto.validar()
                livre = boleto.campo_livre()
            except PyCobrancaError:
                continue  # recusado com erro do pacote: é o comportamento certo
            if len(livre) != 25:
                estouros.append(f"{campo}={valor!r} → campo livre com {len(livre)}")
    assert estouros == [], f"{banco}: " + "; ".join(estouros)


@pytest.mark.parametrize("banco", sorted(EXEMPLOS))
@pytest.mark.parametrize("campo", ["agencia", "conta"])
def test_boleto_com_agencia_e_conta_de_todos_os_tamanhos(banco: str, campo: str) -> None:
    """Agência e conta variam mais que qualquer outro campo na vida real.

    Cada banco declara faixas diferentes (conta de 5 a 12 dígitos, agência de 3
    a 5), e o mesmo dado migra entre bancos. Nenhum tamanho pode produzir um
    boleto inválido em silêncio.
    """
    validos = 0
    for digitos in range(0, 16):
        boleto = EXEMPLOS[banco]["boleto"]()
        setattr(boleto, campo, "9" * digitos)
        try:
            boleto.validar()
        except PyCobrancaError:
            continue
        _confere(f"{banco}/{campo}/{digitos}", boleto)
        validos += 1
    assert validos, f"{banco}: nenhum tamanho de {campo} gerou boleto válido"


# --------------------------------------------------------------------------- #
# Remessa CNAB
# --------------------------------------------------------------------------- #


def _todas_as_remessas():
    """As remessas 400 e 240 dos exemplos, com o prefixo da família no nome."""
    return {
        **{f"400/{nome}": r for nome, r in remessas._remessas_400().items()},
        **{f"240/{nome}": r for nome, r in remessas._remessas_240().items()},
    }


def _refaz(chave: str):
    familia, nome = chave.split("/", 1)
    fabrica = remessas._remessas_400 if familia == "400" else remessas._remessas_240
    return fabrica()[nome]


def _tamanhos_aceitos(remessa) -> tuple[int, ...]:
    tamanho = remessa.tamanho_registro
    return (tamanho,) if isinstance(tamanho, int) else tuple(tamanho)


def _linhas(remessa) -> list[str]:
    return remessa.gera_arquivo().replace("\r\n", "\n").rstrip("\n").split("\n")


@pytest.mark.parametrize("chave", sorted(_todas_as_remessas()))
def test_nenhum_campo_da_remessa_desloca_o_registro(chave: str) -> None:
    """O contrato posicional: ou o campo é recusado, ou o registro fica no tamanho.

    Varre todos os campos de texto da remessa em vários tamanhos. Um registro
    com 401 posições não é um detalhe de formatação — é um arquivo em que cada
    campo depois do estouro está uma casa fora do lugar.
    """
    modelo = _refaz(chave)
    aceitos = _tamanhos_aceitos(modelo)
    campos = [
        f.name for f in dataclasses.fields(modelo) if isinstance(getattr(modelo, f.name, None), str)
    ]

    estouros = []
    for campo in campos:
        for digitos in (0, 1, 2, 5, 12, 25):
            remessa = _refaz(chave)
            # A varredura mexe em todo campo, inclusive nos que o layout não
            # grava — o aviso disso é assunto de `test_cnab_remessa.py`.
            warnings.simplefilter("ignore", CampoIgnorado)
            setattr(remessa, campo, "9" * digitos)
            try:
                comprimentos = {len(linha) for linha in _linhas(remessa)}
            except PyCobrancaError:
                continue  # recusado com erro do pacote: é o comportamento certo
            fora = sorted(comprimentos - set(aceitos))
            if fora:
                estouros.append(f"{campo}={'9' * digitos!r} → registros de {fora}")
    assert estouros == [], f"{chave}: " + "; ".join(estouros)


@pytest.mark.parametrize("chave", sorted(_todas_as_remessas()))
def test_remessa_so_levanta_erro_do_pacote(chave: str) -> None:
    """Campo fora da faixa tem de virar ``PyCobrancaError``, não ``KeyError``.

    Quem integra escreve ``except PyCobrancaError``. Um ``KeyError`` vazando de
    um dicionário interno atravessa esse ``except`` e mata o processo — foi o
    que o Banco do Nordeste fazia com carteira desconhecida.
    """
    modelo = _refaz(chave)
    campos = [
        f.name for f in dataclasses.fields(modelo) if isinstance(getattr(modelo, f.name, None), str)
    ]

    vazamentos = []
    for campo in campos:
        for digitos in (0, 1, 2, 5, 12, 25):
            remessa = _refaz(chave)
            # A varredura mexe em todo campo, inclusive nos que o layout não
            # grava — o aviso disso é assunto de `test_cnab_remessa.py`.
            warnings.simplefilter("ignore", CampoIgnorado)
            setattr(remessa, campo, "9" * digitos)
            try:
                remessa.gera_arquivo()
            except PyCobrancaError:
                continue
            except Exception as erro:  # noqa: BLE001 — é exatamente o que se mede
                vazamentos.append(f"{campo}={'9' * digitos!r} → {type(erro).__name__}")
    assert vazamentos == [], f"{chave}: " + "; ".join(vazamentos)


@pytest.mark.parametrize("chave", sorted(_todas_as_remessas()))
@pytest.mark.parametrize("campo", ["agencia", "conta_corrente"])
def test_remessa_com_agencia_e_conta_de_todos_os_tamanhos(chave: str, campo: str) -> None:
    """A mesma variação de agência/conta do boleto, agora no arquivo.

    Boleto e remessa descrevem o mesmo título e nasceram de códigos separados:
    um campo pode caber num e estourar no outro, e foi o que aconteceu no Banco
    do Nordeste, na CrediSIS, no BRB e no Santander 240.
    """
    modelo = _refaz(chave)
    if not any(f.name == campo for f in dataclasses.fields(modelo)):
        pytest.skip(f"{chave} não tem {campo}")
    aceitos = _tamanhos_aceitos(modelo)

    validos = 0
    for digitos in range(0, 16):
        remessa = _refaz(chave)
        setattr(remessa, campo, "9" * digitos)
        try:
            comprimentos = {len(linha) for linha in _linhas(remessa)}
        except PyCobrancaError:
            continue
        assert not comprimentos - set(aceitos), (
            f"{chave}: {campo} com {digitos} dígitos gerou registros de "
            f"{sorted(comprimentos)}, esperado {list(aceitos)}"
        )
        validos += 1
    assert validos, f"{chave}: nenhum tamanho de {campo} gerou arquivo"


@pytest.mark.parametrize("chave", sorted(_todas_as_remessas()))
def test_nosso_numero_de_qualquer_tamanho_nao_desloca_o_registro(chave: str) -> None:
    """O campo que originou a classe inteira de defeitos.

    O nosso número tem largura diferente em cada banco — 6 no BRB e na CrediSIS,
    7 no Banco do Nordeste, 12 no Sicoob. Passar oito onde cabem seis produzia
    um registro de 402 posições, e o módulo documentava isso como se fosse o
    layout do banco.
    """
    modelo = _refaz(chave)
    aceitos = _tamanhos_aceitos(modelo)

    maior_aceito = 0
    for digitos in range(1, 21):
        remessa = _refaz(chave)
        for pagamento in remessa.pagamentos:
            pagamento.nosso_numero = "9" * digitos
        try:
            comprimentos = {len(linha) for linha in _linhas(remessa)}
        except PyCobrancaError:
            continue
        assert not comprimentos - set(aceitos), (
            f"{chave}: nosso número com {digitos} dígitos gerou registros de "
            f"{sorted(comprimentos)}, esperado {list(aceitos)}"
        )
        maior_aceito = max(maior_aceito, digitos)
    assert maior_aceito, f"{chave}: nenhum tamanho de nosso número gerou arquivo"


def test_nenhuma_remessa_desliga_a_conferencia_de_tamanho() -> None:
    """``tamanho_registro = None`` foi como as quatro remessas quebradas passaram.

    Cada uma justificava o ``None`` dizendo que *o layout do banco* usava 401,
    402 ou 241 posições. Nenhuma usava: era o ``rjust`` estourando o campo. O
    ``None`` transformou o sintoma em documentação e desligou o único aviso.
    """
    sem_conferencia = [
        cls.__name__
        for cls in remessas._classes_de_remessa()
        if getattr(cls(), "tamanho_registro", None) is None
    ]
    assert sem_conferencia == []
