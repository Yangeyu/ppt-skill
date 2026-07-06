"""Look 包库 —— 本引擎的"模板库"就是这里（对标 ppt-master 的
templates/<kind>/<id>/ 自包含目录包；我们叫 look 因为它比版式多三段:
叙事哲学 + 设计语言 + 图像纪律）。

一个 look 包 = 一个子目录，四个分段（对应 ppt-master 的 segment 划分）：
  身份段  __init__.py 里的 SpecLock（色/字/字阶令牌，已过身份评论官的设计语言）
  结构段  templates/*.j2（该 look 的版式库；缺的原型回落 _shared/）
  图像段  image_* 钩子（t2i 风格纪律 / 后处理再上墨 / 离线程序化兜底）
  引导段  guidance.md（该 look 的叙事声音/deck 弧线/版式路由/数据表现纪律，
          由 contract.py 拼进生成契约喂给 agent——look 的"报告哲学"所在）

_shared/ 放跨 look 公共原型（创作轨 custom.html.j2 等），无 __init__.py，
不进注册表。引擎不特判任何 look，只消费本注册表；新增 look = 新建子目录 +
LOOK 常量，零引擎改动。设计规格文档随包放（spec.md，frontmatter 同
ppt-master design_spec）。"""
from __future__ import annotations
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Callable


@dataclass
class Look:
    spec: object                        # SpecLock —— 身份段（冻结的设计语言 seed）
    template_dir: str = ""              # 结构段；"" = 只用共享模板
    icons: dict | None = None           # look 专属图标集（None = 共享 ICONS）
    image_style_suffix: str = ""        # t2i 风格纪律，引擎拼在内容 prompt 之后
    image_postprocess: Callable | None = None   # (src_png, spec, out_png) 再上墨
    image_fallback: Callable | None = None      # (art, spec, out_png) 离线兜底
    pick_when: str = ""                 # 选型指引：什么内容气质该选这个 look
    density: dict = field(default_factory=dict) # 密度纪律：critic/density 消费的配额
                                        # （空 = 稀疏是该 look 的风格，不设下限）


def _discover() -> dict[str, Look]:
    out: dict[str, Look] = {}
    for p in sorted(Path(__file__).parent.iterdir()):
        if p.is_dir() and (p / "__init__.py").exists():
            mod = import_module(f".{p.name}", __package__)
            look = getattr(mod, "LOOK", None)
            if look is not None:
                out[look.spec.id] = look
    return out


LOOKS: dict[str, Look] = _discover()

# 唯一已深度优化的结构库。身份（SpecLock）可换，结构统一走它——
# 对应 ppt-master 的 brand（身份）× layout（结构）分段融合。
DEFAULT_LOOK = "riso"


def get_look(spec) -> Look:
    """按 SpecLock（或其 look 字段）解析结构库；无包身份 → 默认结构库。"""
    lid = getattr(spec, "look", "") or getattr(spec, "id", "")
    return LOOKS.get(lid) or LOOKS[DEFAULT_LOOK]


def list_looks() -> list[dict]:
    """发现索引（对应 ppt-master 的 index 文件）——给 MCP/CLI 挑选用。"""
    return [{"id": k, "name": v.spec.name, "pick_when": v.pick_when,
             "summary": getattr(v.spec, "rationale", "")}
            for k, v in LOOKS.items()]
