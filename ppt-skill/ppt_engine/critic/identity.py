"""身份评论官 —— 校验一份设计语言「体系是否成立」（QUALITY §1）。

纯 Python、零模型、可单测。当前角色是 **look 包作者的门禁**:每个 look 的
SpecLock 必须零 error 才能入库(tests/test_floor.py 对全部注册 look 断言);
未来若恢复「按主题现场生成身份」的 freedom 路线(docs/DESIGN.md 北极星),
它就是那条路线的安全阀——信任 LLM 发明美学,用机器把住 A 层体系。

实现 QUALITY.md §1：字阶(ID-TS-*) / 配色(ID-CL-*) / 字体(ID-FT-*) / 网格母题(ID-GR/MT-*)。"""
from __future__ import annotations
from dataclasses import dataclass

from ..spec import SpecLock, RATIOS, contrast_ratio
from ..fonts import FONT_FILES   # 可嵌入字族登记表（当前 = 思源黑/宋）

EMBEDDABLE = set(FONT_FILES)     # {"Noto Sans SC", "Noto Serif SC"}
PURE_BLACK = {"000000", "010101"}
PURE_WHITE = {"FFFFFF", "FEFEFE"}


@dataclass
class IdentityIssue:
    check: str            # 规则 ID，如 "ID-TS-3"
    level: str            # "error" | "warning"
    detail: str

    def __str__(self):
        return f"[{self.level.upper():7}] {self.check}: {self.detail}"


def _near(x: float, targets, tol: float) -> bool:
    return any(abs(x - t) <= tol for t in targets)


def critique_identity(spec: SpecLock) -> list[IdentityIssue]:
    out: list[IdentityIssue] = []
    ts = spec.type_scale
    c = spec.colors

    # ---- 字阶 ID-TS ------------------------------------------------------
    if not _near(ts.ratio, RATIOS.values(), 0.03):
        out.append(IdentityIssue("ID-TS-1", "error",
            f"字阶比例 {ts.ratio} 非模块化（应 ∈ {sorted(set(RATIOS.values()))} ±0.03）"))
    # 模块化核心（micro..h1）相邻比值的宽松检查（display 是 hero 跳档，豁免）
    core = [ts.micro, ts.caption, ts.body, ts.h2, ts.h1]
    for a, b in zip(core, core[1:]):
        r = b / a
        if not (ts.ratio - 0.3 <= r <= ts.ratio + 0.45):
            out.append(IdentityIssue("ID-TS-1b", "warning",
                f"相邻字阶 {a}->{b} 比值 {r:.2f} 偏离声明比例 {ts.ratio}"))
    n_steps = len(set(ts.all_px()))
    if n_steps > 6:
        out.append(IdentityIssue("ID-TS-2", "error", f"字阶档数 {n_steps} > 6（过多）"))
    if ts.display / ts.body < 3.0:
        out.append(IdentityIssue("ID-TS-3", "error",
            f"display/body = {ts.display}/{ts.body} = {ts.display/ts.body:.1f} < 3.0（大字不够大，层级弱）"))
    if not (18 <= ts.body <= 34):
        out.append(IdentityIssue("ID-TS-4", "warning", f"正文 {ts.body}px 不在 [18,34]"))

    # ---- 配色 ID-CL ------------------------------------------------------
    need = ["primary", "primary-2", "ink", "bg-content", "bg", "muted", "hairline", "surface"]
    miss = [k for k in need if not c.get(k)]
    if miss:
        out.append(IdentityIssue("ID-CL-1", "error", f"调色板结构缺键: {miss}"))
    else:
        body_contrast = contrast_ratio(c["ink"], c["bg-content"])
        if body_contrast < 4.5:
            out.append(IdentityIssue("ID-CL-3", "error",
                f"正文对比 ink/bg-content = {body_contrast:.2f} < 4.5 (WCAG AA)"))
        dark_contrast = contrast_ratio(c["on-dark"], c["bg"])
        if dark_contrast < 4.5:
            out.append(IdentityIssue("ID-CL-3", "error",
                f"深色场景对比 on-dark/bg = {dark_contrast:.2f} < 4.5"))
        if c["ink"].lstrip("#").upper() in PURE_BLACK:
            out.append(IdentityIssue("ID-CL-4", "warning", "正文用纯黑 #000，建议染色深"))
        if c["bg-content"].lstrip("#").upper() in PURE_WHITE:
            out.append(IdentityIssue("ID-CL-4", "warning", "底用纯白 #FFF，建议暖纸/微染"))

    # ---- 字体 ID-FT ------------------------------------------------------
    fams = spec.families()
    if len(fams) > 2:
        out.append(IdentityIssue("ID-FT-1", "error", f"字族 {len(fams)} > 2: {fams}"))
    for f in (spec.display_font, spec.body_font):
        if f not in EMBEDDABLE:
            out.append(IdentityIssue("ID-FT-4", "error",
                f"字体「{f}」不可嵌入（当前仅支持 {sorted(EMBEDDABLE)}）—— Riso 等观感请用颜色+母题+重衬线表达"))

    # ---- 网格 / 母题 ID-GR / ID-MT --------------------------------------
    if spec.grid.unit <= 0 or spec.grid.cols <= 0:
        out.append(IdentityIssue("ID-GR-1", "error", "网格 unit/cols 非法"))
    allowed = spec.allowed_hex()
    for m in spec.motifs:
        # 母题只能引用令牌：粗查内联 #HEX 是否都在令牌集
        for tok in _hexes_in(m.html + " " + m.css if hasattr(m, "css") else m.html):
            if tok not in allowed:
                out.append(IdentityIssue("ID-MT-1", "error",
                    f"母题「{m.name}」引入离板色 #{tok}（不在令牌集）"))
        if m.html and "data-ppt" not in m.html:
            out.append(IdentityIssue("ID-MT-2", "warning",
                f"母题「{m.name}」缺 data-ppt 标记（将无法被抽取为原语）"))

    return out


def _hexes_in(s: str) -> set[str]:
    import re
    return {h.upper() for h in re.findall(r"#([0-9a-fA-F]{6})", s or "")}


def identity_ok(spec: SpecLock) -> bool:
    return not any(i.level == "error" for i in critique_identity(spec))
