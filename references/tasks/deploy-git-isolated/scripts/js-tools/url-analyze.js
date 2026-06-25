#!/usr/bin/env node
/**
 * url-analyze.js — URL 分析 CLI 工具（v1.0.0）
 * layer: js-tools (type: dual)
 *
 * 职责：分析 URL 的绝对地址、图片扩展名、图片类型判定。
 * 底层依赖 js-plugins/url-utils，通过 js_lib.js 统一加载。
 *
 * Node.js CLI 用法：
 *   node js-tools/url-analyze.js --url "https://example.com/a/b/c?q=1#x"
 *   node js-tools/url-analyze.js --url "/foo/bar.jpg" --base "https://x.com/path/"
 *   node js-tools/url-analyze.js --batch "url1" "url2" --base "..."
 *
 * 浏览器注入：
 *   page.add_script_tag("js-tools/url-analyze.js")
 *   → window.__URL_ANALYZE(urlStr, baseUrl) → { original, isImage, imageExt, absolute }
 */

(function (global) {
  'use strict';

  /* ── 尝试通过 js_lib 加载（对标 py_lib 模式）── */
  var HAS_JS_LIB = false;
  var JS_LIB;

  try {
    var pathMod = require('path');
    var jsLibPath = pathMod.resolve(__dirname, '..', 'js_lib.js');
    JS_LIB = require(jsLibPath);
    HAS_JS_LIB = true;
  } catch (_e) {
    HAS_JS_LIB = false;
  }

  /* ── 获取 url-utils 的兼容函数（js-plugins / window / fallback）── */
  function getUrlUtils() {
    if (global.__URL_UTILS) return global.__URL_UTILS;
    if (HAS_JS_LIB) {
      var paths = JS_LIB.resolve(['url-analyze']);
      for (var i = 0; i < paths.length; i++) {
        require(paths[i]);
      }
      if (global.__URL_UTILS) return global.__URL_UTILS;
    }
    try {
      return require('../js-plugins/url-utils.js');
    } catch (_e) {}
    return null;
  }

  /* ── URL 分析核心 ── */
  function analyzeUrl(urlStr, baseUrl) {
    var utils = getUrlUtils();
    if (!utils) {
      return { error: 'url-utils not available', original: urlStr };
    }

    var result = {
      original: urlStr,
      isImage: utils.isImageUrl(urlStr),
      imageExt: utils.guessImageExt(urlStr),
    };

    if (baseUrl || (typeof location !== 'undefined' && location.href)) {
      result.absolute = utils.toAbsoluteURI(urlStr, baseUrl || location.href);
    }

    return result;
  }

  /* ── Node.js CLI 模式（对标 py-tools 的 main()）── */
  if (typeof module !== 'undefined' && module.exports) {
    var args = process.argv.slice(2);
    var hasUrl = args.indexOf('--url') !== -1;
    var hasBatch = args.indexOf('--batch') !== -1;
    var baseIdx = args.indexOf('--base');

    if (hasUrl) {
      var urlIdx = args.indexOf('--url');
      var targetUrl = args[urlIdx + 1];
      var baseUrl = baseIdx !== -1 ? args[baseIdx + 1] : undefined;
      var result = analyzeUrl(targetUrl, baseUrl);
      process.stdout.write(JSON.stringify(result, null, 2) + '\n');
      process.exit(result.error ? 1 : 0);
    } else if (hasBatch) {
      var batchIdx = args.indexOf('--batch');
      var urls = [];
      for (var j = batchIdx + 1; j < args.length; j++) {
        if (args[j].startsWith('--')) break;
        urls.push(args[j]);
      }
      var baseUrl2 = baseIdx !== -1 ? args[baseIdx + 1] : undefined;
      var results = urls.map(function (u) { return analyzeUrl(u, baseUrl2); });
      process.stdout.write(JSON.stringify(results, null, 2) + '\n');
      process.exit(0);
    } else if (args.indexOf('--help') !== -1 || args.indexOf('-h') !== -1) {
      console.log('url-analyze.js — URL 分析工具');
      console.log('  node js-tools/url-analyze.js --url <URL> [--base <BASE>]');
      console.log('  node js-tools/url-analyze.js --batch <URL1> <URL2> [--base <BASE>]');
      process.exit(0);
    } else {
      console.error('用法: node js-tools/url-analyze.js --url <URL> [--base <BASE>]');
      console.error('  或:  node js-tools/url-analyze.js --batch <URL1> <URL2> ...');
      console.error('  或:  node js-tools/url-analyze.js --help');
      process.exit(1);
    }
  }

  /* ── 浏览器注入模式 ── */
  if (typeof window !== 'undefined') {
    global.__URL_ANALYZE = analyzeUrl;
  }
})(typeof window !== 'undefined' ? window : global);
