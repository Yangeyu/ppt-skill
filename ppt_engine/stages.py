"""两段式生成的阶段层:素材 → ①事实清单(factsheet) → ②叙事大纲(outline) → ③Deck IR。

为什么拆段:一步直出整份 IR 时,叙事组织和字段填写挤在同一次输出里,
全局问题(论证链断裂/密度失衡/素材利用率低)靠单页回喂修不了。拆成
事实清单(信息从哪来)→ 大纲(怎么组织)→ 落地(怎么填格),每段都有
机器审核回喂,组织质量从"靠运气"变成"可收敛"。

本模块提供:阶段 schema(pydantic)+ 阶段契约渲染 + 阶段机器审核。
消费方式与 deck 契约一致:cli --contract <look> --stage factsheet|outline,
cli --check-only --stage ... 审核(见 cli.py)。驱动(mastra/generate.ts、
demos/agent_generate.py)只做编排,不携带任何契约文本。"""
from __future__ import annotations
import re

from pydantic import BaseModel, Field

from .contract import FACT_RULES, available_kinds, look_guidance
from .looks import LOOKS

_NUM = re.compile(r"\d+(?:\.\d+)?")


# 逐字比对前的归一化:去空白/markdown 结构符,全角标点折半角,去引号类。
# 否则模型摘表格行(含 |)或把全角逗号写成半角时会被误判"非原文"。
_PUNCT = str.maketrans(
    {"，": ",", "。": ".", "、": ",", "：": ":", "；": ";", "（": "(", "）": ")",
     "！": "!", "？": "?", "％": "%", "—": "-", "－": "-",
     "「": "", "」": "", "『": "", "』": "", "“": "", "”": "", "‘": "", "’": "",
     "|": "", "#": "", "*": "", "`": "", ">": "", "·": ""})


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", s).translate(_PUNCT)


# ---- ① 事实清单 -------------------------------------------------------------
class FactItem(BaseModel):
    id: str = Field(max_length=8)                 # 如 "F01"
    subject: str = Field(max_length=20)           # 对象(品牌/市场/人群…)
    metric: str = Field(max_length=30)            # 指标/事项
    value: str = Field(max_length=30)             # 逐字数值或事实短语
    period: str = Field(default="", max_length=20)  # 时间窗/口径
    quote: str = Field(max_length=90)             # 素材原句片段(逐字)


class FactSheet(BaseModel):
    themes: list[str] = Field(default_factory=list, max_length=8)  # 主题聚类
    facts: list[FactItem] = Field(min_length=8, max_length=60)


FACTSHEET_CONTRACT = """你在做生成前的素材预处理:把素材原文抽成**结构化事实清单**,
供后续组稿逐字引用。输出一个 JSON 对象:
{"themes":["主题聚类,≤8个"],
 "facts":[{"id":"F01","subject":"对象≤20","metric":"指标/事项≤30",
           "value":"逐字数值或事实短语≤30","period":"时间窗/口径≤20",
           "quote":"素材原句片段≤90(逐字摘抄)"}, ...]}

规则:
1. value 与 quote 必须**逐字**来自素材(quote 是原文连续片段,机器会比对);
2. 优先抽带数字的硬事实,也收关键定性判断(占位/模式/建议);8~60 条,宁全勿漏;
3. 同一事实不拆重复条目;口径/时间窗写进 period,不混进 value;
4. 不推导、不合成、不换算——素材怎么写就怎么录。"""


def check_factsheet(fs: dict, source: str) -> list[dict]:
    """事实清单审核:数字溯源 + quote 必须是原文片段。"""
    issues = []
    src_nums = set(_NUM.findall(source))
    flat = _squash(source)
    for f in fs.get("facts", []):
        fid = f.get("id", "?")
        for tok in _NUM.findall(f.get("value", "") + " " + f.get("quote", "")):
            if len(tok) > 1 and tok not in src_nums:
                issues.append({"type": "number-unsourced",
                               "detail": f"{fid} 含素材中没有的数字「{tok}」——逐字摘抄,勿改写"})
        q = _squash(f.get("quote", ""))
        if q and q not in flat:
            issues.append({"type": "quote-not-verbatim",
                           "detail": f"{fid} 的 quote 不是素材原文连续片段——逐字摘抄原句"})
    return issues


# ---- ② 叙事大纲 -------------------------------------------------------------
class OutlineSlide(BaseModel):
    no: int
    kind: str = Field(max_length=16)
    thesis: str = Field(max_length=72)            # 这页的论点/作用,一句话
    fact_ids: list[str] = Field(default_factory=list, max_length=12)
    note: str = Field(default="", max_length=110)  # 模块规划(辅助字段,预算从宽)


class OutlinePlan(BaseModel):
    title: str = Field(max_length=60)
    slides: list[OutlineSlide] = Field(min_length=4, max_length=30)


def _page_tolerance(n_target: int) -> int:
    return max(2, round(n_target * 0.2))


def recommend_pages(n_facts: int) -> int:
    """按素材信息量推荐页数:证据页约 3~4 条事实/页 + 结构页(封面/目录/章节幕/收尾)。
    页数应由素材派生,而非调用方拍脑袋——目标是覆盖充分,不是把报告压进定长模板。"""
    evidence = max(4, round(n_facts / 3.5))
    return min(40, max(10, evidence + 6))


def outline_contract(look_id: str, n_slides: int) -> str:
    kinds = " ".join(available_kinds(look_id))
    g = look_guidance(look_id)
    return f"""你在为「{LOOKS[look_id].spec.name}({look_id})」规划一份 deck 的**叙事大纲**
(先组织、后填格:这一步只定每页的论点/版式/证据分配,不写具体字段)。
输出一个 JSON 对象:
{{"title":"deck标题≤60",
 "slides":[{{"no":1,"kind":"版式名","thesis":"这页论点/作用,一句话≤72",
            "fact_ids":["引用事实清单的id,每页≤12个"],"note":"模块规划≤110(选填)"}}, ...]}}

规则(机器审核,违反退回):
1. kind 只能取: {kinds}
2. 页数 ≥{n_slides - _page_tolerance(n_slides)} 页(下限硬:不许为凑短把证据挤压/丢弃),
   上限 {round(n_slides * 1.5)} 页——素材信息量撑得起就多分页,一页一论点;
3. 除 hero/cover/toc/section/quote/closing 外,每页必须引用 ≥1 个 fact_id;
   证据要摊开用——素材利用率低(大量事实一页未用)会被退回;
4. thesis 决定成稿标题的质量:内容页写成判断句,不是话题名;
5. 遵守下方该风格的叙事纪律(deck 弧线/版式路由/密度要求)。

{g}

{FACT_RULES}"""


_STRUCTURAL = {"hero", "cover", "toc", "section", "quote", "closing"}


def check_outline(outline: dict, look_id: str, n_slides: int,
                  factsheet: dict | None = None) -> list[dict]:
    """大纲审核:版式合法/页数硬控/证据分配/素材利用率/章节配额。"""
    issues = []
    kinds_ok = set(available_kinds(look_id))
    slides = outline.get("slides", [])

    # 页数校验是不对称的:下限硬(少于目标=砍证据,退回),上限宽(为覆盖充分
    # 可超到 1.5 倍,再往上视为注水)。
    tol = _page_tolerance(n_slides)
    if len(slides) < n_slides - tol:
        issues.append({"type": "page-count",
                       "detail": f"仅 {len(slides)} 页,低于目标 {n_slides}-{tol}——"
                                 "不要压缩证据,把挤在一页的论点拆开"})
    elif len(slides) > round(n_slides * 1.5):
        issues.append({"type": "page-count",
                       "detail": f"共 {len(slides)} 页,超过 {round(n_slides * 1.5)}——"
                                 "合并稀薄页,删无证据支撑的页"})

    known_ids = {f.get("id") for f in (factsheet or {}).get("facts", [])}
    used_ids: set[str] = set()
    for s in slides:
        no, kind = s.get("no", "?"), s.get("kind", "")
        if kind not in kinds_ok:
            issues.append({"type": "unknown-kind",
                           "detail": f"第 {no} 页 kind「{kind}」不在本 look 菜单"})
        fids = s.get("fact_ids", [])
        used_ids.update(fids)
        if kind not in _STRUCTURAL and not fids:
            issues.append({"type": "no-evidence",
                           "detail": f"第 {no} 页({kind})未引用任何事实——分配 fact_ids 或改为结构页"})
        if known_ids:
            for fid in fids:
                if fid not in known_ids:
                    issues.append({"type": "bad-fact-id",
                                   "detail": f"第 {no} 页引用了不存在的事实「{fid}」"})

    n_sections = sum(1 for s in slides if s.get("kind") == "section")
    if n_sections > 3:
        issues.append({"type": "too-many-sections",
                       "detail": f"section 共 {n_sections} 页,上限 3"})

    # look 密度配额(与 critic/density.py 的档位一致)
    from .critic.density import PROFILES
    quota = PROFILES.get(look_id, {}).get("exhibit_min", 0)
    n_exhibit = sum(1 for s in slides if s.get("kind") == "exhibit")
    if quota and n_exhibit < quota:
        issues.append({"type": "exhibit-quota",
                       "detail": f"exhibit 仅 {n_exhibit} 页,本风格要求 ≥{quota}(每章主论证一页)"})

    if known_ids:
        unused = len(known_ids) - len(used_ids & known_ids)
        if unused / max(len(known_ids), 1) > 0.6:
            issues.append({"type": "low-coverage",
                           "detail": f"事实清单 {len(known_ids)} 条仅用 {len(used_ids & known_ids)} 条"
                                     "——素材利用率过低,把未用的硬事实摊进证据页"})
    return issues
