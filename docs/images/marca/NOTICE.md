# Marca da M&S do Brasil — aviso de uso

Os arquivos `ms-*.svg` deste diretório são a **assinatura da M&S do Brasil LTDA**, mantenedora da
PyCobrança. Estão aqui para uma finalidade só: assinar o endosso no rodapé do README e da
documentação, na forma *"um projeto M&S do Brasil"*.

## A licença do código não vale para a marca

A PyCobrança é distribuída sob a [BSD-3-Clause](../../../LICENSE). **Essa licença cobre o código e
não autoriza o uso do nome ou da marca da empresa.** São coisas distintas: quem recebe o direito de
usar, modificar e redistribuir a biblioteca não recebe com isso direito sobre a identidade visual
de quem a mantém.

Na prática, para quem usa a PyCobrança em outro projeto:

- **Pode**, sem pedir: citar a M&S do Brasil pelo nome, em texto.
- **Pode**, sem pedir: usar a assinatura, sem alteração, para dizer que um projeto é mantido ou
  apoiado pela M&S — nas formas *"um projeto M&S do Brasil"* ou *"com apoio da M&S do Brasil"* —
  **quando isso for verdade**.
- **Precisa de autorização**: aplicar a marca em material de terceiros, parceiros ou clientes, e
  usá-la em produtos, eventos ou publicidade.
- **Não pode**: alterar desenho, cores ou proporções fora das variantes do kit; usar a marca de
  modo que sugira parceria ou endosso que não existe.

Pedidos e dúvidas: <contato@msbrasil.inf.br>.

## Os arquivos

Cópia byte a byte do kit de marca oficial — **nenhum foi editado aqui**. Alterar a arte é vedado
pelos termos de uso; mudanças só no kit de origem, que é gerado por script a partir de uma
geometria única.

| Arquivo | Variante | Onde se aplica |
|---|---|---|
| `ms-assinatura-horizontal-fundo-claro.svg` | Marinho `#0D1B4B` + ciano escuro `#0891B2` | Fundo branco ou claro |
| `ms-assinatura-horizontal-fundo-escuro.svg` | Branco + ciano `#06B6D4` | Fundo marinho ou escuro |

As duas estão no README dentro de um `<picture>`, trocadas por `prefers-color-scheme`. O manual
veda aplicar a versão clara sobre fundo escuro, e o GitHub tem os dois temas — uma variante só
quebraria a regra em metade dos leitores.

**Tamanho mínimo em tela:** 28 px de altura (101 px de largura) para a assinatura horizontal.
Abaixo disso o manual manda trocar pelo símbolo. No README ela entra com 150 px de largura,
cerca de 42 px de altura.

**Área de proteção:** um terço da altura visível em todos os lados — 14 px a 42 px de altura.
Nenhuma outra marca entra nessa faixa.

## Procedência

Kit de marca **v0.7**, de novembro de 2026 — a versão em produção. O desenho está fechado. O que
resta são itens de processo, como a busca de anterioridade no INPI e a prova gráfica, que não
alteram a arte em tela. Os arquivos daqui são os oficiais enquanto não houver versão nova do kit;
quando houver, eles são **substituídos por cópia**, nunca editados.

## Por que a marca da PyCobrança não muda

O manual classifica a PyCobrança como **marca endossada** — modelo *"marca própria + linha de
endosso"*, cuja avaliação no próprio manual é *"mantém o que já existe e liga à empresa"*. A
identidade visual da biblioteca é dela: nome, desenho e cores seguem como estão. A ligação com a
empresa se faz pela assinatura no rodapé, não repintando o projeto.

É também o que explica o arranjo deste repositório, pela regra de convivência do manual: *"no site
e em material comercial, a M&S vem primeiro e os produtos abaixo; em repositório e documentação
técnica, o produto vem primeiro, e o endosso fica no rodapé do README."* Por isso a marca da
PyCobrança continua no topo e a da empresa aparece só no fim — e por isso a assinatura da empresa
não encosta na arte do projeto.

Este arquivo é informativo e não altera os termos de licença de nada.
