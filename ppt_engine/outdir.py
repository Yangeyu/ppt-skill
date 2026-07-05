"""统一产物目录约定 —— 所有生成结果默认落 out/<slug>/(pptx + preview/ 截图)。

demos/、cli(JSON bridge)、MCP 三个入口共用;显式传路径时不干预。
slug 保留 CJK,只把路径分隔符/空白折成下划线。"""
from __future__ import annotations
import re
from pathlib import Path


def slugify(name: str, maxlen: int = 40) -> str:
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", (name or "").strip()).strip("_")
    return s[:maxlen] or "deck"


def out_dir(name: str, root: str | Path | None = None) -> Path:
    """out/<slug>/ 目录(连 preview/ 一起建好),root 缺省为 cwd(仓库根运行)。"""
    d = (Path(root) if root else Path.cwd()) / "out" / slugify(name)
    (d / "preview").mkdir(parents=True, exist_ok=True)
    return d
