/* Nome acessível para o diálogo de busca.
 *
 * O mkdocs-material emite `<div class="md-search" role="dialog">` sem
 * `aria-label`. Um elemento com `role="dialog"` e sem nome é anunciado pelo
 * leitor de tela apenas como "diálogo" — quem navega por áudio não sabe o que
 * abriu. É a única reprovação de acessibilidade do tema na página.
 *
 * Conferido na 9.7.7 (instalada) e na 9.8.0 (a mais recente no PyPI): as duas
 * emitem o mesmo markup, então atualizar o tema não resolve.
 *
 * Feito em JavaScript, e não copiando `partials/search.html` para
 * `docs/overrides/`, de propósito: a cópia fixaria ~40 linhas de markup
 * interno do tema, que passariam a envelhecer em silêncio a cada atualização
 * — o próprio arquivo do tema avisa "automatically generated - do not edit".
 * O leitor de tela lê o DOM vivo, então definir o atributo depois da carga
 * tem o mesmo efeito para quem precisa dele.
 *
 * `document$` é o observable que o material expõe para rodar código a cada
 * troca de página; com `navigation.instant` ligado não há recarga, e um
 * `DOMContentLoaded` só valeria para a primeira página visitada.
 */
document$.subscribe(function () {
  var busca = document.querySelector('.md-search[role="dialog"]');
  if (busca && !busca.getAttribute("aria-label")) {
    busca.setAttribute("aria-label", "Buscar na documentação");
  }
});
