# Ativos de marca

Gera os arquivos de `docs/images/`: banner do README, card social (Open Graph),
símbolo isolado e favicon.

```bash
pip install fonttools uharfbuzz pymupdf pillow
cd tools/marca
curl -sSLO https://raw.githubusercontent.com/google/fonts/main/ofl/manrope/Manrope%5Bwght%5D.ttf
curl -sSLO https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf
mv 'Manrope[wght].ttf' Manrope.ttf && mv 'JetBrainsMono[wght].ttf' JetBrainsMono.ttf
python gerar.py
```

Duas decisões que não são estéticas e não devem ser desfeitas sem motivo:

**Texto em curvas.** `tipografia.py` molda com HarfBuzz e converte cada glifo em
`<path>`. Sem isso o SVG depende de a fonte existir na máquina que renderiza — foi
o que trocou a tipografia do card anterior por uma serifada.

**Fundo chapado.** Gradiente de SVG não sobrevive a boa parte dos rasterizadores,
e foi o que apagou o fundo do card anterior.

O QR do banner é real, gerado por `pycobranca.pix.qr`, e aponta para o repositório.

Tipografia: [Manrope](https://github.com/sharanda/manrope) e
[JetBrains Mono](https://github.com/JetBrains/JetBrainsMono), ambas sob SIL Open
Font License 1.1. Só as curvas dos glifos entram nos SVGs; as fontes não são
distribuídas com o pacote.
