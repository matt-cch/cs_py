(function () {
  var presets = {};

  presets.createArticlePreset = function (td) {
    td.addRule('img', {
      filter: 'img',
      replacement: function (content, node) {
        var src = node.getAttribute('src') || '';
        var alt = node.getAttribute('alt') || '';
        return src ? '![' + alt + '](' + src + ')' : '';
      },
    });
    td.keep(['table', 'thead', 'tbody', 'tr', 'th', 'td']);
    return td;
  };

  presets.createGitHubPreset = function (td) {
    td.addRule('img', {
      filter: 'img',
      replacement: function (content, node) {
        var src = node.getAttribute('src') || '';
        var alt = node.getAttribute('alt') || '';
        if (!src) return '';
        var w = node.getAttribute('width');
        var h = node.getAttribute('height');
        var dims = (w && h) ? ' =' + w + 'x' + h : '';
        return '![' + alt + '](' + src + dims + ')';
      },
    });
    td.keep(['table', 'thead', 'tbody', 'tr', 'th', 'td']);
    return td;
  };

  presets.createCleanPreset = function (td) {
    td.remove(['script', 'style', 'iframe', 'noscript']);
    td.keep(['pre', 'code']);
    return td;
  };

  if (typeof window !== 'undefined') window.__MARKDOWN_RULES = presets;
  if (typeof module !== 'undefined' && module.exports) module.exports = presets;
})();
