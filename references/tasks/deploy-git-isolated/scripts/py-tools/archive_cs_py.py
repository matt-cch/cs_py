#!/usr/bin/env python3
"""
archive_cs_py.py — 快捷脚本：归档 cs_py 分组
用法：python archive_cs_py.py [--stage all] [--format 7z] [--force]

注：本脚本为 py-tools 快捷入口，透传参数到 archive_project.py（主编排层）。
"""
import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_script = Path(__file__).parent.resolve() / "archive_project.py"
args = [str(sys.executable), str(_script), "--group", "cs_py"] + sys.argv[1:]
subprocess.run(args)
