#!/usr/bin/env python3
"""Chrome 扩展管理器：从 Chrome Web Store 下载 CRX 并解压。

使用前提::

    本工具下载 CRX 必须知道准确的 32 位扩展 ID。
    如果不知道 ID，请先用 --search 搜索扩展名，找到验证通过的候选 ID，
    再复制正确的 ID 用 -e 下载。

支持四种获取扩展 ID 的方式（按适用场景）::

    1. 直接提供扩展 ID（--extension-id）—— 已知 ID 时最快
    2. 提供 Chrome Web Store 详情页 URL（--store-url）—— 从 URL 提取 ID
    3. 扫描本地已安装扩展（--list-local）—— 更新已有扩展时确认 ID
    4. 按名称搜索并验证（--search）—— 全新扩展，不知道 ID 时的标准流程

标准操作流程（全新扩展）::

    # 第 1 步：搜索扩展名，工具会自动验证哪些 ID 可下载
    python chrome_extension_manager.py --search "Obsidian Web Clipper" --verify-search

    # 第 2 步：从输出中复制验证通过的 ID
    # 第 3 步：用该 ID 下载
    python chrome_extension_manager.py -e <验证通过的ID> -o D:/download/obsidian-web-clipper

代理支持：读取环境变量 HTTP_PROXY / HTTPS_PROXY（标准 urllib 行为）。
"""
import argparse
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from urllib import request, error as urllib_error

# Agent bash 调用时 stdout/stderr 必须是 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

CRX_DOWNLOAD_URL = (
    "https://clients2.google.com/service/update2/crx"
    "?response=redirect&prodversion=119.0&acceptformat=crx2,crx3"
    "&x=id%3D{ext_id}%26uc"
)

CWS_SEARCH_URL = "https://chromewebstore.google.com/search/{keyword}?hl=zh-CN"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)


def extract_id_from_store_url(url: str) -> str | None:
    """从 Chrome Web Store URL 中提取扩展 ID。

    支持的 URL 模式::
        https://chromewebstore.google.com/detail/<name>/<id>
        https://chrome.google.com/webstore/detail/<name>/<id>
        https://chromewebstore.google.com/detail/<name>/<id>?hl=xx
    """
    patterns = [
        r"chromewebstore\.google\.com/detail/[^/]+/([a-z]{32})",
        r"chrome\.google\.com/webstore/detail/[^/]+/([a-z]{32})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def discover_local_extensions() -> list[dict]:
    """扫描本地 Chrome 扩展目录，返回已安装扩展列表（含 ID、名称、版本、路径）。"""
    candidates = []

    # 1. 项目隔离 Chrome 数据目录
    devroot = Path("D:/pjt/cursor/cs_py")
    isolated = devroot / "venv/data-chrome/Default/Extensions"
    if isolated.exists():
        candidates.append(isolated)

    # 2. 系统默认 Chrome 用户数据目录
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        system = Path(local_appdata) / "Google/Chrome/User Data/Default/Extensions"
        if system.exists():
            candidates.append(system)

    results = []
    for ext_root in candidates:
        if not ext_root.exists():
            continue
        for ext_id_dir in ext_root.iterdir():
            if not ext_id_dir.is_dir():
                continue
            ext_id = ext_id_dir.name
            version_dirs = [d for d in ext_id_dir.iterdir() if d.is_dir()]
            if not version_dirs:
                continue
            version_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            latest = version_dirs[0]
            manifest = read_manifest(latest)
            if manifest:
                results.append({
                    "id": ext_id,
                    "name": manifest.get("name", "Unknown"),
                    "version": manifest.get("version", "Unknown"),
                    "path": str(latest),
                    "source": str(ext_root),
                })
    return results


def verify_extension_id(extension_id: str, timeout: int = 15) -> dict:
    """验证扩展 ID 是否可公开下载。

    使用 Range 请求下载前 2 字节，避免全量下载。返回 dict：
    {"ok": bool, "status": int|None, "reason": str}
    """
    url = CRX_DOWNLOAD_URL.format(ext_id=extension_id)
    req = request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Range": "bytes=0-1",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return {
                "ok": True,
                "status": resp.status,
                "reason": "OK",
            }
    except urllib_error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "reason": f"HTTP {exc.code} {exc.reason}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "reason": str(exc),
        }


def download_crx(extension_id: str, output_path: Path, timeout: int = 120) -> int:
    """从 Chrome Web Store 下载 CRX 文件，返回字节数。"""
    url = CRX_DOWNLOAD_URL.format(ext_id=extension_id)
    req = request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    output_path.write_bytes(data)
    return len(data)


def extract_crx(crx_path: Path, output_dir: Path) -> int:
    """解压 CRX 文件到指定目录，返回解压出的文件数。"""
    raw = crx_path.read_bytes()
    zip_magic = b"PK\x03\x04"
    pos = raw.find(zip_magic)
    if pos == -1:
        raise ValueError(f"无法在 {crx_path} 中找到 ZIP 数据，可能不是标准 CRX 格式")
    zip_data = raw[pos:]
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zf.extractall(output_dir)
        return len(zf.namelist())


def read_manifest(extension_dir: Path) -> dict:
    """读取 manifest.json，返回字典。"""
    manifest_path = extension_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def search_chrome_webstore(keyword: str, timeout: int = 30, verify: bool = False) -> list[dict]:
    """从 Chrome Web Store 搜索关键词，返回候选扩展列表。

    解析策略：
      1. 提取 HTML 中所有 /detail/<slug>/<id> 链接，从 slug 推断名称
      2. 提取所有 32 位 ID 作为后备
      3. 若 verify=True，对每个候选发送 Range 请求验证可下载性
    """
    url = CWS_SEARCH_URL.format(keyword=keyword.replace(" ", "%20"))
    req = request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"[extension-manager] 搜索请求失败 : {exc}", file=sys.stderr)
        return []

    results = []
    seen = set()

    # 策略 1：提取详情页链接（含名称 slug）
    detail_links = re.findall(r'href="(/detail/([^/]+)/([a-z]{32}))"', html)
    for link_path, slug, ext_id in detail_links:
        if ext_id in seen or ext_id == 'abcdefghijklmnopqrstuvwxyzabcdef':
            continue
        seen.add(ext_id)
        name = slug.replace('-', ' ').replace('_', ' ').title()
        results.append({
            "id": ext_id,
            "name": name,
            "url": f"https://chromewebstore.google.com{link_path}",
            "source": "detail_link",
        })

    # 策略 2：提取所有 32 位 ID（后备）
    all_ids = set(re.findall(r'[a-z]{32}', html))
    for ext_id in all_ids:
        if ext_id not in seen and ext_id != 'abcdefghijklmnopqrstuvwxyzabcdef':
            seen.add(ext_id)
            results.append({
                "id": ext_id,
                "name": "(unknown)",
                "url": f"https://chromewebstore.google.com/detail/{ext_id}",
                "source": "heuristic",
            })

    # 策略 3：验证可下载性
    if verify and results:
        print(f"[extension-manager] 正在验证 {len(results)} 个候选 ID 的可下载性（Range 请求）...")
        verified_results = []
        for i, r in enumerate(results, 1):
            v = verify_extension_id(r["id"], timeout=15)
            status_mark = "✓" if v["ok"] else "✗"
            print(f"  [{i}/{len(results)}] {status_mark} {r['id']} — {v['reason']}")
            if v["ok"]:
                r["verified"] = True
                verified_results.append(r)
            else:
                r["verified"] = False
        # 优先返回已验证的；如果没有验证通过的，返回全部供人工判断
        if verified_results:
            print(f"[extension-manager] 验证完成：{len(verified_results)}/{len(results)} 个 ID 可下载")
            return verified_results
        else:
            print("[extension-manager] 警告：没有候选 ID 通过下载验证，返回全部结果供人工确认")
            return results

    return results


def print_search_results(results: list[dict]) -> None:
    """美化输出搜索结果。"""
    print(f"\n[extension-manager] 找到 {len(results)} 个候选扩展：")
    print("-" * 80)
    for i, r in enumerate(results, 1):
        verified = " [已验证可下载]" if r.get("verified") else ""
        print(f"\n  #{i}{verified}")
        print(f"    名称: {r['name']}")
        print(f"    ID  : {r['id']}")
        print(f"    URL : {r['url']}")
        if r.get("source") == "heuristic":
            print(f"    提示: 此 ID 来自启发式提取，建议访问 URL 确认名称后再下载")
    print("-" * 80)
    print("\n[extension-manager] 下一步：")
    print("  复制上方验证通过的 ID，执行：")
    print(f"    python chrome_extension_manager.py -e <ID> -o <输出目录>")
    print("\n  如果列表中没有你要的扩展，请直接用浏览器访问：")
    print(f"    {CWS_SEARCH_URL.format(keyword='')}")
    print("  在页面中找到扩展后，复制其 32 位 ID 再下载。\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chrome 扩展下载与解压工具（支持 CRX2/CRX3 格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用前提：下载 CRX 必须知道准确的 32 位扩展 ID。

不知道 ID 时的标准操作流程（全新扩展）：
  1. 搜索并验证：python chrome_extension_manager.py --search "扩展名称" --verify-search
  2. 从输出中复制验证通过的 ID
  3. 下载：python chrome_extension_manager.py -e <ID> -o <输出目录>

示例：
  # 已知 ID，直接下载
  %(prog)s -e cjpalhdlnbpafiamejdnhcphjbkeiagm -o ./output

  # 从 Web Store URL 提取 ID（注意：URL 中的 ID 可能与实际下载 ID 不一致）
  %(prog)s --store-url https://chromewebstore.google.com/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm -o ./output

  # 搜索全新扩展（推荐配合 --verify-search）
  %(prog)s --search "Obsidian Web Clipper" --verify-search

  # 验证某个 ID 是否可下载（不实际下载）
  %(prog)s --verify-id cjpalhdlnbpafiamejdnhcphjbkeiagm

  # 列出本地已安装扩展（更新时使用）
  %(prog)s --list-local
        """.strip(),
    )
    parser.add_argument(
        "--extension-id", "-e",
        help="Chrome 扩展 ID（32 位小写字母，如 cjpalhdlnbpafiamejdnhcphjbkeiagm）",
    )
    parser.add_argument(
        "--store-url", "-u",
        help="Chrome Web Store 详情页 URL（自动提取扩展 ID，但提取出的 ID 不一定能下载）",
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="解压输出目录（如 D:/download/obsidian-web-clipper）",
    )
    parser.add_argument(
        "--crx-only",
        action="store_true",
        help="仅下载 CRX 文件，不解压",
    )
    parser.add_argument(
        "--crx-path",
        help="指定 CRX 保存路径（默认放在输出目录内，命名为 <ext-id>.crx）",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="下载超时秒数（默认 120）",
    )
    parser.add_argument(
        "--list-local",
        action="store_true",
        help="扫描本地 Chrome 扩展目录并列出已安装扩展（不下载；仅适用于更新已有扩展）",
    )
    parser.add_argument(
        "--search",
        metavar="KEYWORD",
        help="通过关键词在 Chrome Web Store 搜索候选扩展（全新扩展的标准入口）",
    )
    parser.add_argument(
        "--verify-search",
        action="store_true",
        help="搜索后自动用 Range 请求验证每个候选 ID 是否可下载（强烈推荐）",
    )
    parser.add_argument(
        "--verify-id",
        metavar="EXT_ID",
        help="验证指定 ID 是否可公开下载（Range 探测，不实际下载）",
    )
    args = parser.parse_args()

    # 模式 A：列出本地扩展
    if args.list_local:
        print("[extension-manager] 扫描本地 Chrome 扩展目录...")
        local_exts = discover_local_extensions()
        if not local_exts:
            print("[extension-manager] 未发现本地已安装扩展。")
            print("[extension-manager] 扫描路径：")
            print("  - D:/pjt/cursor/cs_py/venv/data-chrome/Default/Extensions")
            print("  - %LOCALAPPDATA%/Google/Chrome/User Data/Default/Extensions")
            print("\n[extension-manager] 提示：本地无扩展时，请用 --search 查找全新扩展")
            return 0
        print(f"[extension-manager] 发现 {len(local_exts)} 个本地扩展：")
        print(f"{'ID':<35} {'名称':<30} {'版本':<15} {'来源'}")
        print("-" * 100)
        for ext in local_exts:
            name = ext['name'][:28]
            print(f"{ext['id']:<35} {name:<30} {ext['version']:<15} {ext['source']}")
        print("\n[extension-manager] 提示：复制上方 ID 可直接用于 -e 下载")
        return 0

    # 模式 B：验证指定 ID
    if args.verify_id:
        print(f"[extension-manager] 验证扩展 ID : {args.verify_id}")
        result = verify_extension_id(args.verify_id, timeout=args.timeout)
        if result["ok"]:
            print(f"[extension-manager] ✓ 验证通过 — {result['reason']} (status={result['status']})")
            print(f"[extension-manager] 该 ID 可以公开下载，执行：")
            print(f"  python chrome_extension_manager.py -e {args.verify_id} -o <输出目录>")
            return 0
        else:
            print(f"[extension-manager] ✗ 验证失败 — {result['reason']}", file=sys.stderr)
            print(f"[extension-manager] 该 ID 无法公开下载，可能原因：", file=sys.stderr)
            print(f"  - ID 错误或已下架", file=sys.stderr)
            print(f"  - 扩展为付费/企业/内部分发", file=sys.stderr)
            print(f"[extension-manager] 建议：用 --search 搜索扩展名确认正确 ID", file=sys.stderr)
            return 1

    # 模式 C：搜索关键词
    if args.search:
        print(f"[extension-manager] 搜索关键词 : {args.search}")
        if not args.verify_search:
            print("[extension-manager] 提示：建议追加 --verify-search 自动验证候选 ID 的可下载性")
        results = search_chrome_webstore(
            args.search,
            timeout=args.timeout,
            verify=args.verify_search,
        )
        if not results:
            print("[extension-manager] 未找到候选扩展。建议直接访问浏览器搜索：")
            print(f"  {CWS_SEARCH_URL.format(keyword=args.search.replace(' ', '%20'))}")
            print("[extension-manager] 在页面中找到扩展后，复制其 32 位 ID 再下载。")
            return 1
        print_search_results(results)
        return 0

    # 模式 D：下载扩展
    extension_id = args.extension_id
    if args.store_url:
        parsed = extract_id_from_store_url(args.store_url)
        if not parsed:
            print(f"[extension-manager] 无法从 URL 解析扩展 ID : {args.store_url}", file=sys.stderr)
            print("[extension-manager] 支持的 URL 格式：", file=sys.stderr)
            print("  https://chromewebstore.google.com/detail/<name>/<32位ID>", file=sys.stderr)
            return 1
        extension_id = parsed
        print(f"[extension-manager] 从 URL 解析到扩展 ID : {extension_id}")
        print("[extension-manager] 警告：URL 中的 ID 可能与实际可下载 ID 不一致，如果下载失败请用 --search 确认")

    if not extension_id:
        print("[extension-manager] 错误：必须提供操作参数", file=sys.stderr)
        print("[extension-manager] 不知道扩展 ID？请执行：", file=sys.stderr)
        print(f"  python chrome_extension_manager.py --search \"<扩展名称>\" --verify-search", file=sys.stderr)
        parser.print_help(sys.stderr)
        return 1

    if not args.output_dir:
        print("[extension-manager] 错误：下载模式必须提供 --output-dir", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.crx_path:
        crx_path = Path(args.crx_path)
    else:
        crx_path = output_dir / f"{extension_id}.crx"

    print(f"[extension-manager] 扩展 ID : {extension_id}")
    print(f"[extension-manager] 输出目录 : {output_dir.resolve()}")
    print(f"[extension-manager] CRX 路径 : {crx_path.resolve()}")

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    if proxy:
        print(f"[extension-manager] 检测到代理 : {proxy}")

    # 下载前可选验证
    print("[extension-manager] 下载前验证 ID 有效性...")
    precheck = verify_extension_id(extension_id, timeout=min(args.timeout, 30))
    if not precheck["ok"]:
        print(f"[extension-manager] ✗ 预验证失败 : {precheck['reason']}", file=sys.stderr)
        print(f"[extension-manager] 该 ID 无法公开下载。建议：", file=sys.stderr)
        print(f"  1. 确认 ID 是否正确（注意大小写、长度是否为 32 位）", file=sys.stderr)
        print(f"  2. 用 --search 搜索扩展名，找到验证通过的 ID", file=sys.stderr)
        print(f"  3. 访问 Chrome Web Store 页面确认扩展是否可公开安装", file=sys.stderr)
        return 1
    print(f"[extension-manager] ✓ 预验证通过 ({precheck['status']})")

    print("[extension-manager] 开始全量下载...")
    try:
        size = download_crx(extension_id, crx_path, timeout=args.timeout)
    except urllib_error.HTTPError as exc:
        print(f"[extension-manager] 下载失败 : HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[extension-manager] 下载失败 : {exc}", file=sys.stderr)
        return 1
    print(f"[extension-manager] 下载完成 : {size} bytes")

    if args.crx_only:
        print("[extension-manager] 仅下载模式，跳过解压")
        return 0

    extract_dir = output_dir / extension_id
    extract_dir.mkdir(parents=True, exist_ok=True)

    print(f"[extension-manager] 开始解压到 {extract_dir.resolve()}...")
    try:
        count = extract_crx(crx_path, extract_dir)
    except Exception as exc:
        print(f"[extension-manager] 解压失败 : {exc}", file=sys.stderr)
        return 1
    print(f"[extension-manager] 解压完成 : {count} 个文件")

    manifest = read_manifest(extract_dir)
    if manifest:
        name = manifest.get("name", "Unknown")
        version = manifest.get("version", "Unknown")
        print(f"[extension-manager] 扩展信息 : {name} v{version}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
