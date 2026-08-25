"""Regenera o GIF de demonstração do README (``docs/images/demo.gif``).

    python tools/demo_gif.py

O GIF é uma sessão de terminal encenada: o texto aparece linha a linha, como se
alguém estivesse digitando. **Não é uma gravação** — é desenhado aqui, o que
permite regerá-lo quando a biblioteca muda.

Por que existe: o GIF anterior não tinha gerador e envelheceu em silêncio —
anunciava ``pycobranca-1.0.0`` muito depois de a versão ter mudado. É a mesma
armadilha que ``screenshots.py`` fecha para as capturas de boleto: sem um
gerador versionado, a imagem do README passa a descrever um software que não
existe mais, e nada aponta a divergência.

**Os valores exibidos são calculados de verdade**, não digitados: a linha
digitável que aparece na tela sai do próprio pacote, no momento da geração. Se a
saída mudar, o GIF muda junto.

Requer ``pillow`` (só para desenhar; não é dependência do pacote)::

    pip install pillow
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pycobranca import __version__
from pycobranca.bancos import Bancos

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "images" / "demo.gif"
LARGURA, ALTURA = 940, 560
MS_POR_QUADRO = 260
MS_NO_FIM = 2600

FUNDO = "#0d1b26"
JANELA = "#0a1620"
BARRA = "#12232f"
BORDA = "#1d3444"

BRANCO = "#e6edf3"
CINZA = "#8aa0ae"
VERDE = "#3ddc97"
CIANO = "#5ccfe6"
LARANJA = "#ffb454"

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def _roteiro() -> list[list[tuple[str, str]]]:
    """As linhas do terminal, como ``[(texto, cor), ...]`` por linha.

    Os números vêm do pacote — só o texto ao redor é encenado.
    """
    itau = Bancos.find("341")(
        valor="127.50",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="0057",
        conta="12345",
        carteira="109",
        nosso_numero="12345678",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    inter = Bancos.find("077")(
        valor="1234.56",
        cedente="Empresa Exemplo LTDA",
        cedente_documento="11222333000181",
        agencia="0001",
        conta="123456",
        carteira="110",
        convenio="1234567",
        nosso_numero="0004309540",
        data_vencimento=date(2026, 8, 15),
        sacado="Cliente Final da Silva",
        sacado_documento="52998224725",
    )
    quantos = len(Bancos.todos())
    return [
        [("$ ", VERDE), ("pip install pycobranca", BRANCO)],
        [(f"Successfully installed pycobranca-{__version__}  ✓", VERDE)],
        [],
        [(">>> ", CIANO), ("from pycobranca.bancos import Bancos", BRANCO)],
        [(">>> ", CIANO), ('boleto = Bancos.find("341")(  ', BRANCO), ("# Itaú", CINZA)],
        [("...       ", CIANO), ('valor="127.50", nosso_numero="12345678",', BRANCO)],
        [("...       ", CIANO), ("data_vencimento=date(2026, 8, 15))", BRANCO)],
        [(">>> ", CIANO), ("boleto.linha_digitavel", BRANCO)],
        [(f"'{itau.linha_digitavel}'", VERDE)],
        [],
        [
            (">>> ", CIANO),
            ('inter = Bancos.find("077")(  ', BRANCO),
            ("# Inter, carteira 110", LARANJA),
        ],
        [("...       ", CIANO), ('convenio="1234567", nosso_numero="0004309540", …)', BRANCO)],
        [(">>> ", CIANO), ("inter.nosso_numero_formatado()", BRANCO)],
        [(f"'{inter.nosso_numero_formatado()}'", VERDE)],
        [],
        [(">>> ", CIANO), ("pdf = render_boleto_pdf(boleto.contexto_render())", BRANCO)],
        [
            (f"# {quantos} bancos · PIX (Bolepix) · remessa/retorno CNAB · OFX ", CINZA),
            ("— Python puro", CINZA),
        ],
    ]


def _desenha(linhas_visiveis: int, roteiro, fontes) -> Image.Image:
    normal, negrito = fontes
    img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    d = ImageDraw.Draw(img)

    # janela do terminal
    d.rounded_rectangle((16, 14, LARGURA - 16, ALTURA - 14), radius=12, fill=JANELA, outline=BORDA)
    d.rounded_rectangle((16, 14, LARGURA - 16, 60), radius=12, fill=BARRA)
    d.rectangle((16, 48, LARGURA - 16, 60), fill=BARRA)
    for i, cor in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        d.ellipse((38 + i * 22, 30, 50 + i * 22, 42), fill=cor)
    titulo = "PyCobrança · Python puro"
    d.text((LARGURA / 2, 37), titulo, font=negrito, fill=CIANO, anchor="mm")

    y = 86
    for linha in roteiro[:linhas_visiveis]:
        x = 40
        for texto, cor in linha:
            d.text((x, y), texto, font=normal, fill=cor)
            x += d.textlength(texto, font=normal)
        if linha is roteiro[linhas_visiveis - 1]:  # cursor na última linha escrita
            d.rectangle((x + 3, y + 2, x + 12, y + 20), fill=VERDE)
        y += 28
    return img


def main() -> int:
    try:
        normal = ImageFont.truetype(MONO, 17)
        negrito = ImageFont.truetype(MONO_BOLD, 15)
    except OSError:
        print("fonte DejaVu Sans Mono não encontrada", file=sys.stderr)
        return 1

    roteiro = _roteiro()
    quadros = [_desenha(n, roteiro, (normal, negrito)) for n in range(1, len(roteiro) + 1)]
    duracoes = [MS_POR_QUADRO] * (len(quadros) - 1) + [MS_NO_FIM]

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    quadros[0].save(
        DESTINO,
        save_all=True,
        append_images=quadros[1:],
        duration=duracoes,
        loop=0,
        optimize=True,
    )
    tamanho = DESTINO.stat().st_size / 1024
    print(f"{DESTINO.relative_to(DESTINO.parents[2])}: {len(quadros)} quadros, {tamanho:.0f} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
