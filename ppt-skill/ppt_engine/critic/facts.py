"""事实评论官 —— 生成 IR 对素材原文的忠实度复核(纯文本比对,零模型)。

覆盖 agent e2e 实测出的四类模型缺陷,prompt 说服不了、必须机器把关:
  编数字/推导数字(把 8.77万÷4689 算成"差18.7倍")、编目标数、
  编联系方式(闭合槽位刻板幻觉,如 "+86 21 6237 XXXX")、结构数量超限。

原则:只报高置信度问题(数字 token 素材里查无 = 高置信),归属类错误
(张冠李戴)文本比对查不出,留给视觉评论官/人工抽查。"""
from __future__ import annotations
import re

_NUM = re.compile(r"\d+(?:\.\d+)?")
# 这些字段里的数字是排版性质的(章节号/页码芯片),不做溯源
_SKIP_FIELDS = {"number", "pages", "theme"}


def _walk(obj, path="deck"):
    """递归产出 (路径, 字符串值)。"""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in _SKIP_FIELDS:
                continue
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _canon_num(v) -> str:
    """数值 → 与素材 token 可比的字符串形态(整数去掉 .0)。"""
    f = float(v)
    return str(int(f)) if f.is_integer() else repr(f)


def check_facts(deck: dict, source: str, *, max_sections: int = 3) -> list[dict]:
    """deck 为 Deck IR 的 dict 形态;source 为素材原文。返回 issues(空 = 干净)。"""
    issues: list[dict] = []
    # 千分位逗号是排版差异不是数字差异:"47,397" 应能对上 series 值 47397
    src_nums = set(_NUM.findall(source)) | set(_NUM.findall(source.replace(",", "")))
    # series 数值走数值域比对(素材 "27.30" 应能对上 JSON 解析出的 27.3)
    src_vals = {float(t) for t in src_nums}
    slides = deck.get("slides", [])

    for idx, slide in enumerate(slides, 1):
        d = slide.get("data", {})
        # 图表 series 数值溯源(字符串遍历覆盖不到数值数组——模型会在这里推导补数)
        ctype = d.get("chart_type", "column")
        for s_ in (d.get("series") or []):
            vals = [v for v in (s_.get("values") or []) if isinstance(v, (int, float))]
            missing = [v for v in vals if float(v) not in src_vals]
            # 占比图例外:唯一一个补足 100% 的分块是画图所需的呈现推导,放行
            if (ctype in ("pie", "donut") and len(missing) == 1
                    and 99.0 <= sum(vals) <= 101.0):
                missing = []
            for v in missing:
                issues.append({
                    "slide": idx, "type": "number-unsourced",
                    "detail": f"series「{s_.get('name', '')}」含素材中没有的数值"
                              f"「{_canon_num(v)}」——图表数值必须逐字来自素材,不得推导/"
                              "指数化;占比图仅允许一个补足 100% 的'其他'分块",
                })
        for path, text in _walk(d, d.get("kind", "?")):
            for tok in _NUM.findall(text):
                if len(tok) > 1 and tok not in src_nums:
                    issues.append({
                        "slide": idx, "type": "number-unsourced",
                        "detail": f"{path} 出现素材中没有的数字「{tok}」:“{text[:40]}”"
                                  "——只能逐字引用素材原数,不得推导/编造;查无请删除或改写",
                    })
        # 闭合槽位:素材没给的联系方式一律视为编造
        contact = d.get("contact", "")
        if contact and contact not in source:
            issues.append({
                "slide": idx, "type": "fabricated-contact",
                "detail": f"contact「{contact}」在素材中不存在——留空(\"\")",
            })

    # 章节数上限随 deck 体量缩放:短 deck 最多 3 幕,长报告约每 6 页允许一幕
    # (页数是覆盖率承诺,章节结构应服务于素材本身的论证骨架,不硬压)
    cap = max(max_sections, len(slides) // 6)
    n_sections = sum(1 for s in slides if s.get("data", {}).get("kind") == "section")
    if n_sections > cap:
        issues.append({
            "slide": 0, "type": "too-many-sections",
            "detail": f"section 章节幕共 {n_sections} 页,超过上限 {cap}(约每 6 页一幕)——"
                      "合并相邻主题,删多余章节幕",
        })
    return issues
