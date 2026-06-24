#!/usr/bin/env python3
"""
py_lib.py — Python 插件聚合入口（v1.2.0）
职责：读取 py-sort-rules.json → 拓扑排序 → 标签筛选 → 动态 import 插件

设计原则：
- 入口与配置在 scripts/ 根下，与 PS 的 github-lib.ps1 + lib-sort-rules.json 对齐
- 插件放在 py-plugins/ 子目录下，与 PS 的 lib-plugins/ 对齐
- devroot 作为核心 cwd 判断基准，提供路径解析工具

用法：
    import sys
    sys.path.insert(0, r"...\\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", tags=["md", "validation"])

    # 插件通过 registry 访问 devroot 和路径工具
    task_dir = registry.resolve_path("${devroot}\\references\\tasks\\deploy-git-isolated")
    registry.link_checker.validate(task_dir=task_dir)
"""
import importlib
import json
import os
import sys
from pathlib import Path

__version__ = "1.2.0"

# 入口文件所在目录（scripts/）
_SCRIPTS_DIR = Path(__file__).parent.resolve()
# 规则文件（与入口同级，对称于 lib-sort-rules.json）
_RULES_FILE = _SCRIPTS_DIR / "py-sort-rules.json"
# 插件目录（对称于 lib-plugins/）
_PY_PLUGINS_DIR = _SCRIPTS_DIR / "py-plugins"

# 确保 py-plugins/ 在 sys.path 中，使插件模块可被 import
if str(_PY_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PY_PLUGINS_DIR))


def _load_rules():
    """读取 py-sort-rules.json"""
    with open(_RULES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _kahn_sort(plugins, name_map):
    """Kahn 拓扑排序"""
    in_degree = {p["name"]: 0 for p in plugins}
    adj = {p["name"]: [] for p in plugins}

    for p in plugins:
        for dep in p.get("depends", []):
            if dep in name_map:
                adj[dep].append(p["name"])
                in_degree[p["name"]] += 1

    queue = [name for name, deg in in_degree.items() if deg == 0]
    result = []

    while queue:
        queue.sort()
        name = queue.pop(0)
        result.append(name)
        for neighbor in adj[name]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(plugins):
        unresolved = [name for name, deg in in_degree.items() if deg > 0]
        raise RuntimeError(f"插件依赖存在循环或未解析: {unresolved}")

    return result


def _resolve_plugins(rules, tags=None, profile="_default"):
    """根据标签或 profile 筛选插件，并补齐依赖"""
    all_plugins = rules.get("plugins", [])
    name_map = {p["name"]: p for p in all_plugins}
    profiles = rules.get("profiles", {})

    # 确定需要加载的插件集合
    needed = set()

    if tags:
        # 按标签筛选
        for p in all_plugins:
            p_tags = set(p.get("tags", []))
            if p_tags & set(tags):
                needed.add(p["name"])
    elif profile and profile in profiles:
        # 按 profile 筛选
        prof = profiles[profile]
        include_tags = set(prof.get("include_tags", []))
        exclude_tags = set(prof.get("exclude_tags", []))

        for p in all_plugins:
            p_tags = set(p.get("tags", []))
            if exclude_tags and (p_tags & exclude_tags):
                continue
            if not include_tags or (p_tags & include_tags):
                needed.add(p["name"])
    else:
        # 默认加载全部
        needed = set(name_map.keys())

    # 补齐依赖
    def add_deps(name):
        if name not in name_map:
            return
        for dep in name_map[name].get("depends", []):
            if dep not in needed:
                needed.add(dep)
                add_deps(dep)

    for name in list(needed):
        add_deps(name)

    # 筛选出需要加载的插件列表
    filtered = [name_map[name] for name in needed if name in name_map]
    return filtered, name_map


class PluginRegistry:
    """插件注册表，按拓扑排序后的顺序加载
    
    提供 devroot 上下文和路径解析工具，供插件访问外部资源。
    """

    def __init__(self, devroot=None, rules_version=None):
        """
        参数:
            devroot: 开发根路径（核心 cwd 判断基准）。强烈建议传入，用于路径解析和验证。
            rules_version: py-sort-rules.json 的版本号
        """
        self.devroot = devroot
        self._plugins = {}
        self._modules = {}
        self._rules_version = rules_version or "unknown"

    @property
    def rules_version(self) -> str:
        """返回 py-sort-rules.json 的真源版本号"""
        return self._rules_version

    def resolve_path(self, path_template: str) -> str:
        """
        解析含 ${devroot} 占位符的路径模板，返回绝对路径
        
        参数:
            path_template: 路径模板，如 "${devroot}\\references\\runtime\\verify-runtime.py"
        
        返回:
            解析后的绝对路径字符串
        
        异常:
            ValueError: devroot 未设置但路径模板包含 ${devroot}
        """
        if "${devroot}" in path_template:
            if not self.devroot:
                raise ValueError("路径模板包含 ${devroot} 但 devroot 未设置。请在 load_plugins(devroot=...) 中传入。")
            return path_template.replace("${devroot}", str(self.devroot))
        return path_template

    def validate_devroot(self) -> bool:
        """
        验证 devroot 是否指向有效目录
        
        返回:
            True 如果 devroot 存在且为目录
        
        异常:
            ValueError: devroot 未设置或无效
        """
        if not self.devroot:
            raise ValueError("devroot 未设置。请在 load_plugins(devroot=...) 中传入。")
        devroot_path = Path(self.devroot)
        if not devroot_path.exists():
            raise ValueError(f"devroot 指向的路径不存在: {self.devroot}")
        if not devroot_path.is_dir():
            raise ValueError(f"devroot 指向的路径不是目录: {self.devroot}")
        return True

    def load(self, plugins, name_map):
        """按拓扑排序顺序加载插件"""
        sorted_names = _kahn_sort(plugins, name_map)

        for name in sorted_names:
            plugin_def = name_map[name]
            module_name = plugin_def["module"]

            try:
                mod = importlib.import_module(module_name)
                # 将 registry 注入模块，使插件可访问 devroot 和路径工具
                if hasattr(mod, "__plugin_registry__"):
                    mod.__plugin_registry__ = self
                self._modules[name] = mod
                self._plugins[name] = plugin_def
            except Exception as e:
                raise RuntimeError(f"插件 '{name}' (模块: {module_name}) 加载失败: {e}")

    def __getattr__(self, name):
        """通过属性访问插件模块"""
        if name in self._modules:
            return self._modules[name]
        raise AttributeError(f"插件 '{name}' 未加载。已加载: {list(self._plugins.keys())}")

    def list_loaded(self):
        """返回已加载的插件清单"""
        return list(self._plugins.keys())


def get_rules_version() -> str:
    """返回 py-sort-rules.json 的真源版本号"""
    rules = _load_rules()
    return rules.get("meta", {}).get("version", "unknown")


def list_plugins(tags=None):
    """
    列出 py-sort-rules.json 中定义的可用插件（不加载，只返回元数据）。

    这是发现「有哪些插件可用」的正规入口，禁止直接翻查 py-plugins/ 目录。

    参数:
        tags: 标签列表，只返回包含任一指定标签的插件。None 表示返回全部。

    返回:
        list[dict]: 每个 dict 包含 name, module, tags, description
    """
    rules = _load_rules()
    all_plugins = rules.get("plugins", [])

    if tags:
        tag_set = set(tags)
        result = []
        for p in all_plugins:
            p_tags = set(p.get("tags", []))
            if p_tags & tag_set:
                result.append({
                    "name": p["name"],
                    "module": p["module"],
                    "tags": p.get("tags", []),
                    "description": p.get("description", ""),
                })
        return result

    return [
        {
            "name": p["name"],
            "module": p["module"],
            "tags": p.get("tags", []),
            "description": p.get("description", ""),
        }
        for p in all_plugins
    ]


def load_plugins(devroot=None, tags=None, profile="_default"):
    """
    加载 py-plugins/ 下的插件

    参数:
        devroot: 开发根路径（核心 cwd 判断基准）。如未传入，自动探测并记录真源。
        tags: 标签列表，按标签筛选插件（与 profile 互斥）
        profile: 预设 profile 名（默认 _default）

    返回:
        PluginRegistry 实例
    """
    # 步骤 0: 确保 devroot 已就绪（先加载 detect_devroot 插件进行探测/验证）
    if devroot:
        # 显式传入：验证并记录到环境变量
        from detect_devroot import validate_devroot, record_devroot
        validated = validate_devroot(devroot)
        record_devroot(str(validated))
    else:
        # 未传入：尝试从环境变量获取，或自动探测
        from detect_devroot import get_devroot
        validated = get_devroot()
        devroot = str(validated)

    # 步骤 1: 加载配置的插件
    rules = _load_rules()
    rules_ver = rules.get("meta", {}).get("version", "unknown")
    plugins, name_map = _resolve_plugins(rules, tags=tags, profile=profile)

    registry = PluginRegistry(devroot=devroot, rules_version=rules_ver)
    registry.load(plugins, name_map)

    return registry


if __name__ == "__main__":
    # 自检：先列出可用插件，再加载并列出已加载
    print("=== 可用插件清单（list_plugins）===")
    for p in list_plugins():
        print(f"  {p['name']}: {p['description']} (tags: {p['tags']})")

    print("\n=== 加载 lint profile ===")
    registry = load_plugins(devroot=r"D:\pjt\cursor\cs_py", profile="lint")
    print(f"devroot: {registry.devroot}")
    print(f"已加载插件: {registry.list_loaded()}")
