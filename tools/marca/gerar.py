"""Gera os ativos de marca da PyCobrança a partir de uma fonte única.

Todo texto sai em curvas — nenhum arquivo depende de fonte instalada.
"""

from __future__ import annotations

import pathlib
import sys

import tipografia as T

SAIDA = pathlib.Path("saida")
SAIDA.mkdir(exist_ok=True)

# Paleta proposta pelo designer: acento deslocado do turquesa do PIX.
FUNDO_A, FUNDO_B = "#0C1D2B", "#0A1622"
ACENTO = "#2FA8C6"
ACENTO_CLARO = "#7FD3E8"
TEXTO = "#EEF3F5"
TEXTO_2 = "#93A8B5"

URL_REPO = "https://github.com/Maxwbh/pyCobranca"
SITE = "maxwbh.github.io/pyCobranca"

# ---------------------------------------------------------------- marca


def marca(tamanho: float = 100, x: float = 0, y: float = 0, ident: str = "") -> str:
    """Símbolo "P + barras": duas barras de código de barras que sobem até
    virar a haste do P. Legível em 16 px porque são só três traços."""
    e = tamanho / 100
    return f"""<g transform="translate({x:.2f},{y:.2f}) scale({e:.5f})" \
fill="none" stroke-linecap="round" stroke-linejoin="round">\
<path d="M20 84 L20 30" stroke="{ACENTO_CLARO}" stroke-width="10"/>\
<path d="M38 84 L38 20" stroke="{ACENTO_CLARO}" stroke-width="9"/>\
<path d="M58 84 L58 14 L67 14 A19 19 0 0 1 67 52 L58 52" stroke="{ACENTO}" \
stroke-width="15"/></g>"""


def marca_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" '
        'height="100" role="img" aria-label="PyCobrança">' + marca(100) + "</svg>"
    )


# ------------------------------------------------------------- elementos


def barras(
    x: float, y: float, largura: float, altura: float, opacidade: float, semente: int = 7
) -> str:
    """Textura de código de barras — larguras variáveis, sem gradiente."""
    larguras = [3, 8, 4, 6, 3, 9, 5, 3, 7, 4, 8, 3, 6, 5, 9, 4, 3, 7, 6, 8, 4, 5, 3, 9]
    partes, cursor, i = [], x, semente
    while cursor < x + largura - 4:
        w = larguras[i % len(larguras)]
        if i % 3:
            partes.append(f'<rect x="{cursor:.1f}" y="{y:.1f}" width="{w}" height="{altura:.1f}"/>')
        cursor += w + 3
        i += 1
    return f'<g fill="{TEXTO}" fill-opacity="{opacidade}">{"".join(partes)}</g>'


def qr(payload: str, x: float, y: float, lado: float) -> tuple[str, int]:
    """QR real, gerado pelo próprio codificador da biblioteca."""
    sys.path.insert(0, "/home/user/pyCobranca")
    from pycobranca.pix.qr import qr_matrix

    matriz = qr_matrix(payload)
    n = len(matriz)
    borda = 2
    passo = lado / (n + 2 * borda)
    # Corridas horizontais viram um retângulo só — o QR cai à metade do peso.
    pecas = []
    for r, linha in enumerate(matriz):
        c = 0
        while c < n:
            if linha[c]:
                ini = c
                while c < n and linha[c]:
                    c += 1
                pecas.append(
                    f'<rect x="{(ini + borda) * passo:.1f}" '
                    f'y="{(r + borda) * passo:.1f}" '
                    f'width="{(c - ini) * passo:.1f}" height="{passo:.1f}"/>'
                )
            else:
                c += 1
    quadrados = "".join(pecas)
    return (
        f'<g transform="translate({x:.1f},{y:.1f})">'
        f'<rect width="{lado:.1f}" height="{lado:.1f}" rx="8" fill="{TEXTO}"/>'
        f'<g fill="{FUNDO_A}">{quadrados}</g></g>',
        n,
    )


def pilula(
    x: float,
    y: float,
    texto: str,
    *,
    tamanho: float = 19,
    peso: int = 600,
    fonte: str = T.MANROPE,
    cor=None,
    altura: float = 44,
    respiro: float = 24,
) -> tuple[str, float]:
    cor = cor or ACENTO_CLARO
    largura = T.medir(texto, tamanho=tamanho, peso=peso, fonte=fonte) + respiro * 2
    r = altura / 2
    base = y + altura / 2 + tamanho * 0.34
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{largura:.1f}" height="{altura}" '
        f'rx="{r}" fill="none" stroke="{ACENTO}" stroke-opacity="0.5" '
        f'stroke-width="1.5"/>'
        f'<g fill="{cor}">'
        + T.caminho(texto, x=x + respiro, y=base, tamanho=tamanho, peso=peso, fonte=fonte)
        + "</g>",
        largura,
    )


def fundo(largura: float, altura: float, raio: float = 24) -> str:
    # Chapado de propósito: gradiente de SVG não sobrevive a boa parte dos
    # rasterizadores, e foi o que apagou o fundo do card anterior.
    return (
        f'<defs><clipPath id="corte">'
        f'<rect width="{largura}" height="{altura}" rx="{raio}"/></clipPath></defs>'
        f'<rect width="{largura}" height="{altura}" rx="{raio}" fill="{FUNDO_A}"/>'
    )


def wordmark(x: float, base: float, tamanho: float) -> str:
    py = T.medir("Py", tamanho=tamanho, peso=800)
    return (
        f'<g fill="{TEXTO}">'
        + T.caminho("Py", x=x, y=base, tamanho=tamanho, peso=800)
        + f'</g><g fill="{ACENTO}">'
        + T.caminho("Cobrança", x=x + py, y=base, tamanho=tamanho, peso=800)
        + "</g>"
    )


# --------------------------------------------------------------- banner


def banner(com_qr: bool) -> str:
    L, A, M = 1200, 300, 60
    p = [fundo(L, A)]
    p.append(f'<g clip-path="url(#corte)">{barras(756, 62, 340, 176, 0.055)}</g>')

    p.append(wordmark(M, 128, 66))
    p.append(
        f'<g fill="{TEXTO_2}">'
        + T.caminho(
            "Boletos, CNAB 240/400 e PIX/Bolepix em Python puro",
            x=M + 2,
            y=170,
            tamanho=20,
            peso=500,
        )
        + "</g>"
    )

    x = M
    for texto, fonte, peso, tam in [
        ("18 bancos", T.MANROPE, 700, 19),
        ("Python puro", T.MANROPE, 700, 19),
        ("pip install pycobranca", T.MONO, 500, 18),
    ]:
        marcacao, w = pilula(x, 196, texto, tamanho=tam, peso=peso, fonte=fonte)
        p.append(marcacao)
        x += w + 16

    if com_qr:
        lado = 116
        qx = L - M - lado
        marcacao, modulos = qr(URL_REPO, qx, 46, lado)
        p.append(marcacao)
        p.append(marca(52, qx - 24 - 52, 76))
        badge, w = pilula(
            qx + lado / 2 - 62, 186, "Python 3.12+", tamanho=16, peso=600, altura=34, respiro=16
        )
        p.append(badge)
    else:
        p.append(marca(104, L - M - 104, 62))
        badge, w = pilula(0, 0, "Python 3.12+", tamanho=17, peso=600, altura=36, respiro=18)
        bx = L - M - 104 / 2 - w / 2
        badge, _ = pilula(bx, 190, "Python 3.12+", tamanho=17, peso=600, altura=36, respiro=18)
        p.append(badge)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {A}" width="{L}" '
        f'height="{A}" role="img" aria-label="PyCobrança — boletos, CNAB 240/400 e '
        f'PIX/Bolepix em Python puro">' + "".join(p) + "</svg>"
    )


# ----------------------------------------------------------- social card


def social() -> str:
    L, A, M = 1200, 630, 60
    p = [fundo(L, A, raio=0)]
    p.append(f'<g clip-path="url(#corte)">{barras(M, 592, L - 2 * M, 38, 0.05)}</g>')

    # Marca d'água: equilibra a metade direita, que ficaria oca.
    p.append(f'<g opacity="0.10">{marca(392, 782, 150)}</g>')

    # Sobrancelha
    p.append(marca(38, M, 56))
    p.append(
        f'<g fill="{TEXTO_2}">'
        + T.caminho(
            "Python · cobrança bancária", x=M + 54, y=84, tamanho=23, peso=600, espacamento=0.6
        )
        + "</g>"
    )

    p.append(wordmark(M, 258, 108))

    for i, linha in enumerate(["Boletos, CNAB 240/400", "e PIX/Bolepix em Python puro"]):
        p.append(
            f'<g fill="{TEXTO}" fill-opacity="0.88">'
            + T.caminho(linha, x=M + 3, y=332 + i * 48, tamanho=36, peso=500)
            + "</g>"
        )

    x = M
    for texto in ["18 bancos", "BSD-3-Clause", "Sem API externa"]:
        marcacao, w = pilula(x, 432, texto, tamanho=21, peso=700, altura=50, respiro=26)
        p.append(marcacao)
        x += w + 18

    # pip install
    cx, cy, ch = M, 506, 56
    cw = T.medir("pip install pycobranca", tamanho=26, peso=500, fonte=T.MONO) + 56
    p.append(
        f'<rect x="{cx}" y="{cy}" width="{cw:.1f}" height="{ch}" rx="12" '
        f'fill="{TEXTO}" fill-opacity="0.06" stroke="{ACENTO}" stroke-opacity="0.35"/>'
        f'<g fill="{ACENTO_CLARO}">'
        + T.caminho(
            "pip install pycobranca", x=cx + 28, y=cy + 37, tamanho=26, peso=500, fonte=T.MONO
        )
        + "</g>"
    )

    p.append(
        f'<g fill="{TEXTO_2}">'
        + T.caminho(SITE, x=L - M, y=548, tamanho=25, peso=600, ancora="end")
        + "</g>"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {A}" width="{L}" '
        f'height="{A}">' + "".join(p) + "</svg>"
    )


if __name__ == "__main__":
    (SAIDA / "marca.svg").write_text(marca_svg())
    (SAIDA / "banner-sem-qr.svg").write_text(banner(False))
    (SAIDA / "banner-com-qr.svg").write_text(banner(True))
    (SAIDA / "social-card.svg").write_text(social())
    for f in sorted(SAIDA.glob("*.svg")):
        print(f"{f.name:22} {f.stat().st_size / 1024:5.1f} KB")
