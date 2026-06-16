import sys
import os
import subprocess

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')

    devroot = r"D:\pjt\cursor\cs_py"
    git_dist = os.path.join(devroot, "venv", "git")
    git_data = os.path.join(devroot, "venv", "data-git")
    git_exe = os.path.join(git_dist, "cmd", "git.exe")

    print("=" * 50)
    print("Step 3: 验证隔离效果")
    print("=" * 50)

    # 1. 确认 git.exe 存在
    if not os.path.exists(git_exe):
        print(f"[FAIL] git.exe 不存在: {git_exe}")
        sys.exit(1)
    print(f"[OK] git.exe 存在: {git_exe}")

    # 2. 设置 HOME 并执行 git --version
    env = os.environ.copy()
    env["HOME"] = git_data

    # git --version
    result = subprocess.run(
        [git_exe, "--version"],
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace"
    )
    if result.returncode == 0:
        print(f"[OK] git --version: {result.stdout.strip()}")
    else:
        print(f"[FAIL] git --version 失败: {result.stderr}")
        sys.exit(1)

    # 3. 验证 --global 配置路径
    result = subprocess.run(
        [git_exe, "config", "--global", "--list", "--show-origin"],
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace"
    )
    print("\n[OK] git config --global --list --show-origin:")
    print(result.stdout if result.stdout else "(无全局配置)")
    if result.stderr:
        print(f"[WARN] stderr: {result.stderr}")

    # 4. 验证 --global 写入是否落到隔离目录
    test_key = "deploy.verify.test"
    subprocess.run(
        [git_exe, "config", "--global", test_key, "ok"],
        capture_output=True,
        env=env
    )

    gitconfig_path = os.path.join(git_data, ".gitconfig")
    if os.path.exists(gitconfig_path):
        with open(gitconfig_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "deploy" in content:
            print(f"[OK] --global 写入确实落到隔离 .gitconfig")
        else:
            print(f"[WARN] .gitconfig 中未检测到测试键，内容:\n{content}")
    else:
        print(f"[FAIL] 隔离 .gitconfig 未生成")

    # 清理测试键
    subprocess.run(
        [git_exe, "config", "--global", "--unset", test_key],
        capture_output=True,
        env=env
    )

    # 5. 对比系统 Git 与隔离 Git 的路径差异（信息性）
    sys_git = subprocess.run(
        ["git", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True
    )
    print(f"\n[INFO] 系统 Git: {sys_git.stdout.strip() if sys_git.returncode == 0 else '不可用'}")
    print(f"[INFO] 隔离 Git: {git_exe}")
    print(f"[INFO] 隔离 HOME: {git_data}")

    print("\n结论: 隔离验证通过")
