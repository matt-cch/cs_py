(function () {
  window.__extractArticle = function () {
    var docClone = document.cloneNode(true);
    var reader = new Readability(docClone);
    var article = reader.parse();
    if (!article) {
      return { ok: false, error: 'Readability.parse() returned null' };
    }
    var td = new TurndownService({
      headingStyle: 'atx',
      bulletListMarker: '-',
      codeBlockStyle: 'fenced',
    });
    td.addRule('img', {
      filter: 'img',
      replacement: function (content, node) {
        var src = node.getAttribute('src') || '';
        var alt = node.getAttribute('alt') || '';
        return src ? '![' + alt + '](' + src + ')' : '';
      },
    });
    td.keep(['table', 'thead', 'tbody', 'tr', 'th', 'td']);
    var markdown = td.turndown(article.content);
    return {
      ok: true,
      title: article.title,
      markdown: markdown,
      byline: article.byline || '',
      publishedTime: article.publishedTime || '',
      siteName: article.siteName || '',
      excerpt: article.excerpt || '',
      url: location.href,
    };
  };
})();
