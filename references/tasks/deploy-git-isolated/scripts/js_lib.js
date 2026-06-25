/**
 * js_lib.js — JS 入口（对标 py_lib.py）
 *
 * 职责：读取 js-sort-rules.json → 拓扑排序 → 返回注入/加载顺序
 *
 * 浏览器注入（通过 Playwright add_script_tag）：
 *   python 侧调用 py-plugins/js_loader.py → 读取同一份 JSON 做拓扑排序
 *
 * Node.js CLI（通过 node.exe 执行 js-tools/ 脚本）：
 *   node js_lib.js --resolve extract-article   → 打印排序后的路径列表
 *   node js_lib.js --list                      → 打印可用 js-tools/ 清单
 *
 * 被 require 时暴露 resolve() 供 js-tools/ 使用：
 *   const { resolve } = require('./js_lib.js');
 *   const paths = resolve(['extract-article']);
 */

const fs = require('fs');
const path = require('path');

const SCRIPTS_DIR = __dirname;
const RULES_FILE = path.join(SCRIPTS_DIR, 'js-sort-rules.json');
const JS_PLUGINS_DIR = path.join(SCRIPTS_DIR, 'js-plugins');
const JS_TOOLS_DIR = path.join(SCRIPTS_DIR, 'js-tools');

function loadRules() {
  const raw = fs.readFileSync(RULES_FILE, 'utf-8');
  return JSON.parse(raw);
}

/**
 * 按依赖排序返回 JS 文件路径列表
 * @param {string[]} toolNames - 需要加载的 js-tools 名称
 * @returns {string[]} 按注入/执行顺序排列的绝对路径
 */
function resolve(toolNames) {
  const rules = loadRules();
  const pluginsMap = {};
  const toolsMap = {};

  for (const p of (rules.plugins || [])) pluginsMap[p.name] = p;
  for (const t of (rules.tools || [])) toolsMap[t.name] = t;

  const neededPlugins = new Set();
  const neededTools = new Set();

  function resolveDeps(name) {
    if (toolsMap[name]) {
      if (neededTools.has(name)) return;
      neededTools.add(name);
      for (const dep of (toolsMap[name].depends || [])) {
        if (pluginsMap[dep]) resolveDepsPlugin(dep);
        else if (toolsMap[dep]) resolveDeps(dep);
      }
    }
  }

  function resolveDepsPlugin(name) {
    if (neededPlugins.has(name)) return;
    neededPlugins.add(name);
    const p = pluginsMap[name];
    for (const dep of (p.depends || [])) {
      if (pluginsMap[dep]) resolveDepsPlugin(dep);
    }
  }

  for (const name of toolNames) {
    resolveDeps(name);
  }

  const ordered = [];

  for (const pname of Object.keys(pluginsMap)) {
    if (neededPlugins.has(pname)) {
      ordered.push(path.resolve(JS_PLUGINS_DIR, pluginsMap[pname].file));
    }
  }

  for (const tname of Object.keys(toolsMap)) {
    if (neededTools.has(tname)) {
      ordered.push(path.resolve(JS_TOOLS_DIR, toolsMap[tname].file));
    }
  }

  return ordered;
}

function listTools() {
  const rules = loadRules();
  return rules.tools || [];
}

function listPlugins() {
  const rules = loadRules();
  return rules.plugins || [];
}

// CLI mode
if (require.main === module) {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (cmd === '--resolve') {
    const names = args.slice(1);
    if (names.length === 0) {
      console.error('用法: node js_lib.js --resolve <tool-name> [...更多]');
      process.exit(1);
    }
    const paths = resolve(names);
    paths.forEach(p => console.log(p));
  } else if (cmd === '--list') {
    console.log('--- js-plugins ---');
    for (const p of listPlugins()) {
      console.log(`  ${p.name} (${p.type || 'browser'}) — ${p.description}`);
    }
    console.log('--- js-tools ---');
    for (const t of listTools()) {
      console.log(`  ${t.name} (${t.type || 'browser'}) — ${t.description}`);
    }
  } else if (cmd === '--help' || cmd === '-h') {
    console.log('js_lib.js — JS 入口（对标 py_lib.py）');
    console.log('  node js_lib.js --resolve <name> [...]  按依赖排序返回路径');
    console.log('  node js_lib.js --list                   列出可用资产');
  } else {
    console.error('未知命令: ' + cmd);
    console.error('用法: node js_lib.js --resolve <name>  或  node js_lib.js --list');
    process.exit(1);
  }
}

module.exports = { resolve, listTools, listPlugins };
