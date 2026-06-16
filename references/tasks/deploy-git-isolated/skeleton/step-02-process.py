import sys
import os
import json
import urllib.request
import zipfile
import shutil

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')

    devroot = r"D:\pjt\cursor\cs_py"
    git_dist = os.path.join(devroot, "venv", "git")
    git_data = os.path.join(devroot, "venv", "data-git")
    tmp_dir = os.path.join(devroot, "venv", "tmp", "deploy-git-isolated")

    version = "2.54.0"
    asset_name = f"MinGit-{version}-64-bit.zip"
    download_filename = os.path.join(tmp_dir, asset_name)

    # 代理候选
    proxies = [
        "https://gh-proxy.com",
        "https://gh.llkk.cc",
        "https://ghproxy.net",
    ]

    direct_url = f"https://github.com/git-for-windows/git/releases/download/v{version}.windows.1/{asset_name}"

    os.makedirs(tmp_dir, exist_ok=True)

    # Step 1: 下载
    print("=" * 50)
    print("Step 1: 下载 MinGit")
    print("=" * 50)

    downloaded = False
    used_url = None

    # 先尝试代理
    for proxy in proxies:
        url = f"{proxy}/{direct_url}"
        print(f"尝试代理: {proxy}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status == 200:
                    data = resp.read()
                    with open(download_filename, "wb") as f:
                        f.write(data)
                    print(f"[OK] 下载成功 via {proxy} ({len(data)} bytes)")
                    downloaded = True
                    used_url = url
                    break
                else:
                    print(f"[WARN] 状态码: {resp.status}")
        except Exception as e:
            print(f"[WARN] 失败: {e}")

    # 代理失败则尝试直连
    if not downloaded:
        print("代理全部失败，尝试直连...")
        try:
            req = urllib.request.Request(direct_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status == 200:
                    data = resp.read()
                    with open(download_filename, "wb") as f:
                        f.write(data)
                    print(f"[OK] 下载成功 via 直连 ({len(data)} bytes)")
                    downloaded = True
                    used_url = direct_url
                else:
                    print(f"[FAIL] 直连状态码: {resp.status}")
        except Exception as e:
            print(f"[FAIL] 直连失败: {e}")

    if not downloaded:
        print("[FAIL] 所有下载方式均失败")
        sys.exit(1)

    # 简单校验：文件大小不应过小（MinGit 约 40MB）
    file_size = os.path.getsize(download_filename)
    if file_size < 10 * 1024 * 1024:
        print(f"[FAIL] 文件大小异常: {file_size} bytes（预期 > 10MB）")
        sys.exit(1)

    print(f"[OK] 文件大小: {file_size} bytes")

    # Step 2: 解压
    print("\n" + "=" * 50)
    print("Step 2: 解压到 venv/git/")
    print("=" * 50)

    if os.path.exists(git_dist):
        print(f"清理旧目录: {git_dist}")
        shutil.rmtree(git_dist)

    os.makedirs(git_dist, exist_ok=True)

    with zipfile.ZipFile(download_filename, 'r') as z:
        z.extractall(git_dist)

    # MinGit 解压后内容在 venv/git/ 下直接可见（cmd/, mingw64/ 等）
    # 确认 git.exe 存在
    git_exe = os.path.join(git_dist, "cmd", "git.exe")
    if os.path.exists(git_exe):
        print(f"[OK] git.exe 存在: {git_exe}")
    else:
        # 可能解压后多了一层目录
        subdirs = [d for d in os.listdir(git_dist) if os.path.isdir(os.path.join(git_dist, d))]
        if subdirs and not os.path.exists(git_exe):
            # 检查是否有嵌套
            for sd in subdirs:
                nested_git = os.path.join(git_dist, sd, "cmd", "git.exe")
                if os.path.exists(nested_git):
                    print(f"[WARN] 检测到嵌套目录: {sd}，尝试平移...")
                    nested_root = os.path.join(git_dist, sd)
                    for item in os.listdir(nested_root):
                        shutil.move(os.path.join(nested_root, item), git_dist)
                    os.rmdir(nested_root)
                    break

    if os.path.exists(git_exe):
        print("[OK] 解压完成，git.exe 就绪")
    else:
        print(f"[FAIL] 解压后未找到 git.exe，内容: {os.listdir(git_dist)}")
        sys.exit(1)

    # Step 3: 初始化 data-git
    print("\n" + "=" * 50)
    print("Step 3: 初始化 venv/data-git/")
    print("=" * 50)

    os.makedirs(git_data, exist_ok=True)
    os.makedirs(os.path.join(git_data, ".ssh"), exist_ok=True)

    gitconfig_path = os.path.join(git_data, ".gitconfig")
    config_content = """[core]
    autocrlf = false
    eol = lf
[credential]
    helper = cache
"""
    with open(gitconfig_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    print(f"[OK] 写入初始 .gitconfig: {gitconfig_path}")
    print("[OK] 部署完成")
