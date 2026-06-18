#!/usr/bin/env python3
"""
usage-demo.py — py_lib 插件体系用法示例
标签：py-examples
职责：展示如何通过 py_lib 入口加载插件、使用 registry 访问能力。

用法：
    python usage-demo.py

内容：
    1. 加载 core profile（基础设施插件）
    2. 加载 md-validation profile（含依赖自动补齐）
    3. 使用 registry 解析路径
    4. 调用 link_checker 验证 Markdown 链接
    5. 使用 EncodingGuard 切换编码
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 将 scripts/ 根目录加入 sys.path，使 py_lib 可 import
_scripts_dir = __import__("pathlib").Path(__file__).parent.parent.resolve()
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from py_lib import load_plugins


def demo_core_profile():
    """示例 1：加载 core profile（仅基础设施插件）"""
    print("=" * 50)
    print("示例 1: 加载 core profile")
    print("=" * 50)
    registry = load_plugins(
        devroot="D:/pjt/cursor/cs_py",
        profile="core"
    )
    print(f"已加载插件: {registry.list_loaded()}")
    print(f"devroot: {registry.devroot}")


def demo_md_validation():
    """示例 2：加载 md-validation profile（含依赖自动补齐）"""
    print("\n" + "=" * 50)
    print("示例 2: 加载 md-validation profile")
    print("=" * 50)
    registry = load_plugins(
        devroot="D:/pjt/cursor/cs_py",
        profile="md-validation"
    )
    print(f"已加载插件: {registry.list_loaded()}")

    # 使用 registry 解析路径
    task_dir = registry.resolve_path(
        "${devroot}\\references\\tasks\\deploy-git-isolated"
    )
    print(f"任务目录: {task_dir}")

    # 调用 link_checker 插件
    result = registry.link_checker.validate(task_dir=str(task_dir))
    print(f"链接检查: checked={result['checked']}, broken={result['broken']}")
    if result.get("issues"):
        for issue in result["issues"]:
            print(f"  断裂: {issue}")
    else:
        print("所有链接验证通过")


def demo_encoding_guard():
    """示例 3：使用 EncodingGuard 切换 stdout 编码"""
    print("\n" + "=" * 50)
    print("示例 3: EncodingGuard 编码切换")
    print("=" * 50)
    from encoding import EncodingGuard
    with EncodingGuard():
        print("当前 stdout 编码已切换为 UTF-8")
    print("编码已恢复")


def main():
    demo_core_profile()
    demo_md_validation()
    demo_encoding_guard()
    print("\n" + "=" * 50)
    print("全部示例执行完毕")
    print("=" * 50)


if __name__ == "__main__":
    main()
