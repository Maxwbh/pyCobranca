# Logos de bancos — atribuição e marcas

Os arquivos `NNN.png` deste diretório são logotipos de instituições financeiras,
nomeados pelo **código FEBRABAN** do banco. Eles alimentam a capacidade opt-in de
logo do cabeçalho do boleto (`banco.logo`).

## Marcas registradas

Cada logotipo é **marca registrada de propriedade do respectivo banco**. Eles são
incluídos aqui **exclusivamente** para identificar a instituição emissora no
boleto de cobrança — uso nominativo. A inclusão neste repositório **não** transfere
nem licencia qualquer direito de marca. Use um logo apenas quando você tiver o
direito de exibir a marca (por exemplo, cobrança legítima pela instituição ou
autorização do banco).

Se você é titular de uma dessas marcas e deseja ajuste ou remoção, abra uma issue.

## Fonte dos arquivos

Os arquivos vêm de três origens (a licença listada cobre o **arquivo**; ela **não**
concede direitos sobre as **marcas**, que permanecem de seus titulares):

- **Wikimedia Commons — Domínio Público** (alta resolução, com transparência):
  `001`, `004`, `021`, `033`, `041`, `077`, `104`, `136`, `336`, `341`, `745`, `748`, `756`.
  Renderizados em PNG a 600 px de largura a partir dos SVGs em Domínio Público (logotipos
  abaixo do limiar de originalidade / `PD-textlogo`).
- **[laravel-boleto](https://github.com/eduardokum/laravel-boleto)** (diretório
  `logos/`, **licença MIT**): `085`, `399`. A licença MIT cobre o código do projeto.
- **Coleção [Bancos-em-SVG](https://github.com/Tgentil/Bancos-em-SVG)** (SVGs
  rasterizados em alta resolução com transparência): `070`, `097`, `237`, `422`. O
  repositório de origem **não declara licença**; os arquivos foram fornecidos pelo
  mantenedor deste projeto para uso nominativo. Os logotipos permanecem marcas dos
  respectivos bancos.

## Bancos incluídos

| Código | Banco | Origem do arquivo | Licença do arquivo |
|:------:|-------|-------------------|--------------------|
| 001 | Banco do Brasil | Wikimedia Commons (`Banco do Brasil Logo.svg`) | Domínio Público |
| 004 | Banco do Nordeste | Wikimedia Commons (`Logo do Banco do Nordeste.svg`) | Domínio Público |
| 021 | Banestes | Wikimedia Commons (`Logo do Banestes.svg`) | Domínio Público |
| 033 | Santander | Wikimedia Commons (`Banco Santander Logotipo.svg`) | Domínio Público |
| 041 | Banrisul | Wikimedia Commons (`Banrisul Logo (2022).svg`) | Domínio Público |
| 070 | BRB | Bancos-em-SVG (`brb-logo-nome.svg`) | sem licença declarada na origem |
| 085 | Ailos | laravel-boleto | MIT |
| 097 | CrediSIS | Bancos-em-SVG (`credisis-nome.svg`) | sem licença declarada na origem |
| 104 | Caixa Econômica Federal | Wikimedia Commons (`Caixa Econômica Federal logo 1997.svg`) | Domínio Público |
| 136 | Unicred | Wikimedia Commons (`Logotipo do Unicred.svg`) | Domínio Público |
| 237 | Bradesco | Bancos-em-SVG (`bradesco com nome.svg`) | sem licença declarada na origem |
| 336 | C6 Bank | Wikimedia Commons (`Logo C6 Bank.svg`) | Domínio Público |
| 341 | Itaú | Wikimedia Commons (`Itaú Unibanco logo 2023.svg`) | Domínio Público |
| 399 | HSBC | laravel-boleto | MIT |
| 422 | Safra | Bancos-em-SVG (`logo-safra-nome.svg`) | sem licença declarada na origem |
| 745 | Citibank | Wikimedia Commons (`Citibank.svg`) | Domínio Público |
| 748 | Sicredi | Wikimedia Commons (`Logotipo do Sicredi (2016).svg`) | Domínio Público |
| 756 | Sicoob | Wikimedia Commons (`Logotipo do Sicoob.svg`) | Domínio Público |

## Os dois que seguem em baixa resolução

`085` (Ailos) e `399` (HSBC) continuam em 150×40, sem canal alfa. Não é pendência aberta —
cada um tem motivo:

- **Ailos** não tem logotipo no Wikimedia Commons.
- **HSBC** tem, mas só a marca de **2018**, com o hexágono à esquerda. O HSBC encerrou as
  operações no Brasil em 2016 (absorvido pelo Bradesco), e o arquivo aqui é a marca anterior —
  a que o HSBC Brasil de fato usou. Substituir deixaria o arquivo **menos** correto.

Os dois pixelam quando o boleto é impresso. Não produzem caixa opaca: o cabeçalho do boleto é
branco, e a faixa de marca (`tema`) não carrega o logo do banco.
