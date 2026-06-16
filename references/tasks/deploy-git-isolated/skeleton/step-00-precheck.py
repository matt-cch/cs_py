import sys
import os
import json

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')

    devroot = r"D:\pjt\cursor\cs_py"
    git_dist = os.path.join(devroot, "venv", "git")
    git_data = os.path.join(devroot, "venv", "data-git")
    tmp_dir = os.path.join(devroot, "venv", "tmp", "deploy-git-isolated")

    issues = []
    warnings = []

    # 1. 检测 venv/git/ 是否已存在
    if os.path.exists(git_dist):
        entries = os.listdir(git_dist)
        if entries:
            issues.append(f"venv/git/ 已存在且非空: {entries}")
        else:
            warnings.append("venv/git/ 存在但为空，可继续")

    # 2. 检测 venv/data-git/ 是否已存在
    if os.path.exists(git_data):
        entries = os.listdir(git_data)
        if entries:
            issues.append(f"venv/data-git/ 已存在且非空: {entries}")
        else:
            warnings.append("venv/data-git/ 存在但为空，可继续")

    # 3. 检测临时目录残留
    if os.path.exists(tmp_dir):
        entries = os.listdir(tmp_dir)
        if entries:
            warnings.append(f"tmp/deploy-git-isolated/ 存在残留: {entries}")

    # 4. 检测目录可写性
    for d in [os.path.dirname(git_dist), os.path.dirname(git_data)]:
        if not os.access(d, os.W_OK):
            issues.append(f"目录不可写: {d}")

    # 5. 网络连通性（简单检测代理可用性）
    import urllib.request
    test_url = "https://gh-proxy.com"
    try:
        req = urllib.request.Request(test_url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 301, 302):
                print("[OK] 代理 gh-proxy.com 可达")
            else:
                warnings.append(f"代理返回状态: {resp.status}")
    except Exception as e:
        warnings.append(f"代理连通性检测异常: {e}")

    # 输出结果
    print("=" * 50)
    print("Step 0: 预检结果")
    print("=" * 50)

    if warnings:
        for w in warnings:
            print(f"[WARN] {w}")

    if issues:
        for i in issues:
            print(f"[FAIL] {i}")
        print(f"\n结论: 不通过（{len(issues)} 个阻塞项）")
        sys.exit(1)
    else:
        print("结论: 通过，可继续部署")
        sys.exit(0)
