"""契约渲染器 —— 生成端引导的单一事实来源。

一份契约 = 三段拼接:
  ① kind 菜单 + 字数预算:从 ir.py 的 pydantic schema **自动生成**,并按
    look 的 templates/ 目录过滤(该 look 没有模板的 kind 不进菜单)。
    schema 改了,所有消费方的契约自动跟上。
  ② 事实纪律:所有 look 通用的硬规则(逐字引用/禁推导/闭合槽位留空),
    来自 agent e2e 实测的模型可靠性缺陷,由 critic/facts.py 机器复核。
  ③ 叙事与组织纪律:look 包第四段 looks/<id>/guidance.md,每个 look
    自己的叙事声音/deck 弧线/版式路由/数据表现规范。

消费方:cli --contract / ppt_mcp get_contract / mastra deck-generator /
skill(SKILL.md 教 agent 运行 cli 现场获取)。禁止在任何消费方手写第二份。"""
from __future__ import annotations
import types
import typing
from pathlib import Path

import annotated_types as at
from pydantic import BaseModel

from . import ir
from .icons import ICONS
from .looks import LOOKS, DEFAULT_LOOK

_LOOKS_DIR = Path(__file__).parent / "looks"

# 语义提示:schema 说不了"这页是干什么的",在此集中声明(look 的用法差异写 guidance)
KIND_HINTS = {
    "cover":     "文字封面",
    "hero":      "主视觉页(整幅配图+大标题,prompt 描述画面内容,英文,不写风格词)",
    "toc":       "目录",
    "section":   "章节幕",
    "kpi":       "大数字页",
    "bullets":   "要点页",
    "chart":     "单图表页",
    "two_col":   "双面板清单",
    "comparison": "左右对比",
    "process":   "步骤/方法",
    "icon_grid": "图标证据格",
    "timeline":  "时间线",
    "table":     "对照表",
    "pillars":   "支柱/分栏",
    "quote":     "金句页",
    "closing":   "收尾页",
    "exhibit":   "复合证据版面(结论句大标题+主图表+侧栏结构条+洞察框+意义条+来源)",
}

# 事实纪律:全 look 通用,由 critic/facts.py 机器复核,违反会被回喂重做
FACT_RULES = """事实纪律(硬规则,机器复核,违反将被退回):
1. 事实与数字**只能逐字引用素材原文**。禁止编造;禁止自行推导/合成
   (不加总、不算比值倍数、不换算单位后再加工)。素材没有的数字,宁可不写。
2. 归属必须准确:某品牌/某对象的事实不得写到另一个对象名下。
3. 素材里没有的联系方式/邮箱/电话/链接一律留空(contact 给 "")——不要发明。
4. 图表 series 的数值必须与素材一致且与 categories 一一对应;
   条形 note 若写占比/数值,必须带素材中的原数(如 "51%"),不能只写单位。
5. 不确定的信息宁可省略,不要为了填满槽位而补全。"""


# ---- schema → kind 菜单 ----------------------------------------------------
def _bounds(metadata) -> tuple[int | None, int | None]:
    lo = hi = None
    for m in metadata:
        if isinstance(m, at.MinLen):
            lo = m.min_length
        if isinstance(m, at.MaxLen):
            hi = m.max_length
    return lo, hi


def _strip_optional(tp):
    if typing.get_origin(tp) in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        return args[0] if args else tp
    return tp


def _type_str(tp) -> str:
    """内联渲染一个字段类型(不含名字/预算,预算由调用方从 metadata 取)。"""
    if typing.get_origin(tp) is typing.Annotated:
        base, *meta = typing.get_args(tp)
        _, hi = _bounds(getattr(meta[0], "metadata", meta))
        return f"≤{hi}字" if hi else _type_str(base)
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return "{" + ",".join(_field_str(n, f) for n, f in tp.model_fields.items()) + "}"
    if typing.get_origin(tp) is list:
        return f"[{_type_str(typing.get_args(tp)[0])}]"
    if tp is str:
        return "文本"
    if tp in (float, int):
        return "数字"
    if tp is bool:
        return "true|false"
    if typing.get_origin(tp) is typing.Literal:
        return "|".join(str(a) for a in typing.get_args(tp))
    return "…"


def _field_str(name: str, fi) -> str:
    ann = _strip_optional(fi.annotation)
    lo, hi = _bounds(fi.metadata)
    # 字符串:name≤N
    if ann is str:
        s = f"{name}≤{hi}" if hi else name
    elif typing.get_origin(ann) is typing.Literal:
        s = f"{name}:" + "|".join(str(a) for a in typing.get_args(ann))
    elif typing.get_origin(ann) is list:
        inner = _type_str(typing.get_args(ann)[0])
        rng = f"×{lo or 0}-{hi}" if hi else ""
        s = f"{name}:[{inner}]{rng}"
    elif isinstance(ann, type) and issubclass(ann, BaseModel):
        s = f"{name}:{_type_str(ann)}"
    elif ann is bool:
        s = f"{name}:true|false"
    elif ann in (float, int):
        s = f"{name}:数字"
    else:
        s = name
    if not fi.is_required():
        s += "?"                      # 可省略(有默认值)
    return s


def _kind_models() -> dict[str, type[BaseModel]]:
    union = typing.get_args(typing.get_args(ir.SlideData)[0])
    return {m.model_fields["kind"].default: m for m in union}


def available_kinds(look_id: str) -> list[str]:
    """按 look 的 templates/ 目录过滤可用 kind(缺模板的 kind 不能路由)。"""
    tdir = _LOOKS_DIR / look_id / "templates"
    have = {p.name.removesuffix(".html.j2") for p in tdir.glob("*.html.j2")}
    return [k for k in _kind_models() if k in have]


def kind_menu(look_id: str) -> str:
    models = _kind_models()
    lines = []
    for kind in available_kinds(look_id):
        m = models[kind]
        fields = [_field_str(n, f) for n, f in m.model_fields.items() if n != "kind"]
        hint = KIND_HINTS.get(kind, "")
        lines.append(f"- {kind}  {hint}: " + ", ".join(fields))
    return "\n".join(lines)


# ---- guidance(look 包第四段) ---------------------------------------------
def look_guidance(look_id: str) -> str:
    p = _LOOKS_DIR / look_id / "guidance.md"
    return p.read_text("utf-8").strip() if p.exists() else ""


def render_contract(look_id: str | None = None, n_slides: int = 14) -> str:
    """给生成端(任何 agent)的完整契约文本。"""
    look_id = look_id if look_id in LOOKS else DEFAULT_LOOK
    look = LOOKS[look_id]
    icons = ", ".join(sorted((look.icons or ICONS)))
    parts = [
        f"你在为「{look.spec.name}({look_id})」产出一份 Deck IR,共约 {n_slides} 页。"
        '整体输出一个 JSON 对象:\n'
        f'{{"meta":{{"title":"deck标题"}},"theme":"{look_id}",'
        '"slides":[{"data":{"kind":"...", ...}}, ...]}',
        "可用版式(kind)与字段——**字数上限是硬约束,超限会被校验拒绝**;"
        "标 ? 的字段可省略:\n" + kind_menu(look_id),
        FACT_RULES,
        f"icon 字段只能从这些名字里选: {icons}",
    ]
    g = look_guidance(look_id)
    if g:
        parts.append(g)
    return "\n\n".join(parts)
