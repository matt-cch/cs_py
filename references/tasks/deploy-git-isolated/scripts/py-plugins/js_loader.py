import json
from pathlib import Path

__plugin_registry__ = None

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
_RULES_FILE = _SCRIPTS_DIR / "js-sort-rules.json"
_JS_PLUGINS_DIR = _SCRIPTS_DIR / "js-plugins"
_JS_TOOLS_DIR = _SCRIPTS_DIR / "js-tools"


def _load_rules():
    if not _RULES_FILE.exists():
        raise FileNotFoundError(f"js-sort-rules.json 不存在: {_RULES_FILE}")
    with open(_RULES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve(tool_names: list[str] | None = None, tags: list[str] | None = None) -> list[str]:
    """
    读取 js-sort-rules.json，按依赖排序返回 JS 注入顺序。

    参数:
        tool_names: 指定需要加载的 js-tools 名称（如 ["extract-article"]）
                    自动补齐其 depends 中的 js-tools/ + js-plugins/
        tags:       按 tags 筛选 js-tools（当前未实现，保留扩展）

    返回:
        按注入顺序排列的绝对路径列表（先 js-plugins/，再 js-tools/）
    """
    rules = _load_rules()
    plugins_map = {p["name"]: p for p in rules.get("plugins", [])}
    tools_map = {t["name"]: t for t in rules.get("tools", [])}

    if not tool_names:
        return []

    needed_plugins = set()
    needed_tools = set()

    def resolve_deps(tool_name):
        if tool_name not in tools_map:
            return
        needed_tools.add(tool_name)
        for dep in tools_map[tool_name].get("depends", []):
            if dep in plugins_map:
                needed_plugins.add(dep)
            elif dep in tools_map:
                resolve_deps(dep)

    for name in tool_names:
        resolve_deps(name)

    ordered = []

    for pname in plugins_map:
        if pname in needed_plugins:
            fpath = _JS_PLUGINS_DIR / plugins_map[pname]["file"]
            ordered.append(str(fpath.resolve()))

    for tname in tools_map:
        if tname in needed_tools:
            fpath = _JS_TOOLS_DIR / tools_map[tname]["file"]
            ordered.append(str(fpath.resolve()))

    return ordered


def resolve_script_tags(tool_names: list[str] | None = None) -> list[str]:
    """
    快捷方法：返回可直接传入 page.add_script_tag(path=...) 的路径列表。
    每个路径对应一个 JS 文件，按依赖顺序排列。
    """
    return resolve(tool_names=tool_names)


def list_plugins():
    """列出 js-plugins/ 中登记的可复用模块"""
    rules = _load_rules()
    return rules.get("plugins", [])


def list_tools():
    """列出 js-tools/ 中登记的完整注入脚本"""
    rules = _load_rules()
    return rules.get("tools", [])


def validate():
    """检查 js-sort-rules.json 中登记的文件是否均在磁盘上"""
    rules = _load_rules()
    errors = []
    for p in rules.get("plugins", []):
        fpath = _JS_PLUGINS_DIR / p["file"]
        if not fpath.exists():
            errors.append(f"js-plugins/{p['file']} 不存在")
    for t in rules.get("tools", []):
        fpath = _JS_TOOLS_DIR / t["file"]
        if not fpath.exists():
            errors.append(f"js-tools/{t['file']} 不存在")
    return {"valid": len(errors) == 0, "errors": errors}
