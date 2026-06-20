#!/usr/bin/env python3
"""
archive_venv.py — 快捷脚本：归档 venv 分组
用法：python archive_venv.py [--stage all] [--format 7z] [--force]
"""
import sys
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_script = Path(__file__).parent.resolve() / "archive_project.py"
args = [str(sys.executable), str(_script), "--group", "venv"] + sys.argv[1:]
subprocess.run(args)
