"""Regenera as capturas de tela usadas no README e na documentação.

    python tools/screenshots.py

As imagens de ``docs/images/screenshots/`` mostram a saída real do
renderizador. Sem um gerador versionado elas envelhecem em silêncio: as que
estavam no repositório eram do layout moderno anterior e sobreviveram ao
redesenho inteiro sem que nada apontasse a divergência — quem chegava pelo
README via um boleto que a biblioteca não produz mais.

Requer ``pymupdf`` (só para rasterizar; não é dependência do pacote)::

    pip install pymupdf
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from pycobranca.bancos import Bancos
from pycobranca.render import logo_do_banco, render_boleto_pdf, render_carne_pdf

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "images" / "screenshots"
DPI = 150

COMUM = {
    "cedente": "Empresa Exemplo LTDA",
    "cedente_documento": "11222333000181",
    "cedente_endereco": "Av. Paulista, 1000 - São Paulo/SP",
    "sacado": "Cliente Final da Silva",
    "sacado_documento": "52998224725",
    "sacado_endereco": "Rua das Flores, 100 - Centro - Belo Horizonte/MG",
    "data_documento": date(2026, 7, 23),
    "data_vencimento": date(2026, 8, 15),
}

INSTRUCOES = [
    "Após o vencimento, multa de 2% e juros de 1% ao mês.",
    "Não receber após 30 dias do vencimento.",
]


def _itau(**extra):
    return Bancos.find("341")(
        valor="1234.56",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        numero_documento="2026-0001",
        instrucoes=INSTRUCOES,
        **COMUM,
        **extra,
    )


def _inter():
    """Inter (077) — carteira 110, o único caminho componível fora de linha."""
    return Bancos.find("077")(
        valor="1234.56",
        agencia="0001",
        conta="123456",
        carteira="110",
        convenio="1234567",
        nosso_numero="0004309540",
        numero_documento="2026-0004",
        instrucoes=INSTRUCOES,
        logo=logo_do_banco("077"),
        **COMUM,
    )


def _bradesco_pix():
    return Bancos.find("237")(
        valor="127.50",
        agencia="1234",
        conta="56789",
        carteira="09",
        nosso_numero="12345678",
        numero_documento="2026-0002",
        instrucoes=INSTRUCOES,
        pix_chave="cobranca@empresaexemplo.com.br",
        **COMUM,
    )


TEMA = {
    "habilitado": True,
    "cor": "#1B4F8A",
    "logo_texto": "EXEMPLO",
    "empresa": "Exemplo Serviços Ltda",
    "parcela_texto": "Parcela 3/12",
    "marca_dagua": "EXEMPLO",
    "rodape": "financeiro@exemplo.com.br · 0800 000 0000",
}


def _com_tema():
    contexto = _itau().contexto_render()
    contexto["tema"] = TEMA
    return render_boleto_pdf(contexto, modelo="moderno")


def _carne(total: int = 12):
    Banco = Bancos.find("341")
    parcelas = []
    for i in range(1, total + 1):
        mes = 8 + i - 1
        boleto = Banco(
            valor="199.90",
            agencia="0057",
            conta="12345",
            carteira="109",
            nosso_numero=f"{12345678 + i:08d}",
            numero_documento=f"{i:02d}/{total}",
            instrucoes=[f"Parcela {i} de {total}.", INSTRUCOES[0]],
            **{**COMUM, "data_vencimento": date(2026 + (mes - 1) // 12, (mes - 1) % 12 + 1, 15)},
        )
        parcelas.append(boleto.contexto_render())
    return render_carne_pdf({"parcelas": parcelas})


#: ``arquivo -> (descrição, PDF em bytes)``
def _capturas() -> dict[str, tuple[str, bytes]]:
    itau_logo = _itau(logo=logo_do_banco("341"))
    return {
        "boleto-moderno.png": (
            "modelo moderno, sem PIX",
            render_boleto_pdf(_itau().contexto_render(), modelo="moderno"),
        ),
        "boleto-pix.png": (
            "Bolepix — QR na ficha de compensação",
            render_boleto_pdf(_bradesco_pix().contexto_render(), modelo="moderno"),
        ),
        "boleto-logo.png": (
            "logo do banco no cabeçalho",
            render_boleto_pdf(itau_logo.contexto_render(), modelo="moderno"),
        ),
        "boleto-tema.png": ("faixa de marca, marca d'água e rodapé", _com_tema()),
        "carne.png": ("carnê — 3 parcelas por página A4", _carne()),
        "boleto-inter.png": (
            "Banco Inter (077) — carteira 110",
            render_boleto_pdf(_inter().contexto_render(), modelo="moderno"),
        ),
    }


def main() -> int:
    try:
        import pymupdf
    except ImportError:
        print("pymupdf é necessário para rasterizar: pip install pymupdf", file=sys.stderr)
        return 1

    DESTINO.mkdir(parents=True, exist_ok=True)
    for arquivo, (descricao, pdf) in _capturas().items():
        documento = pymupdf.open(stream=pdf, filetype="pdf")
        documento[0].get_pixmap(dpi=DPI).save(DESTINO / arquivo)
        print(f"  {arquivo:22} {descricao}")
    print(f"\n{len(_capturas())} capturas em {DESTINO.relative_to(DESTINO.parents[3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
