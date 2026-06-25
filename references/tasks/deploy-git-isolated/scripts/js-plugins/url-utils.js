(function () {
  var utils = {};

  utils.toAbsoluteURI = function (uri, baseUrl) {
    if (!uri) return '';
    if (/^[a-zA-Z][a-zA-Z0-9+\-.]*:/.test(uri)) return uri;
    if (uri.indexOf('//') === 0) {
      var proto = (baseUrl || (typeof location !== 'undefined' ? location.href : 'http://localhost')).split(':')[0];
      return proto + ':' + uri;
    }
    var base = baseUrl || (typeof location !== 'undefined' ? location.href : 'http://localhost');
    if (uri.indexOf('/') === 0) {
      var parts = base.split('/');
      return parts[0] + '//' + parts[2] + uri;
    }
    var dir = base.substring(0, base.lastIndexOf('/') + 1);
    return dir + uri;
  };

  utils.guessImageExt = function (url) {
    var p = (url || '').split('?')[0].split('#')[0].toLowerCase();
    if (/\.(jpe?g|png|gif|webp|svg|bmp)$/.test(p)) {
      return p.match(/\.(\w+)$/)[1];
    }
    return 'jpg';
  };

  utils.isImageUrl = function (url) {
    return /\.(jpe?g|png|gif|webp|svg|bmp)(\?|#|$)/i.test(url);
  };

  if (typeof window !== 'undefined') window.__URL_UTILS = utils;
  if (typeof module !== 'undefined' && module.exports) module.exports = utils;
})();
