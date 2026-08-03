"""质量链测试 —— 当前产品主干(契约生成→输入容错→事实/密度评论官→页数派生)。

这些模块历史上都出过细节回归(_strip_optional 毁 list 类型、全角标点假阳性、
JS 字符数当字节数),没有测试就是盲改区。全部零模型、毫秒级。"""
import json

from ppt_engine.cli import _normalize_deck
from ppt_engine.contract import available_kinds, render_contract
from ppt_engine.critic.density import check_density, density_profile
from ppt_engine.critic.facts import check_facts
from ppt_engine.looks import LOOKS
from ppt_engine.spec import SpecLock, resolve_spec
from ppt_engine.stages import recommend_pages, recommend_pages_from_source

SOURCE = """2025 年公司营收 8.77 万元,同比增长 45.2%。
用户数达 4689 人。防晒类内容占比 81.88%。"""


def _deck(slides):
    return {"meta": {"title": "测试"}, "theme": "crimson",
            "slides": [{"data": s} for s in slides]}


# ---- 契约生成(schema 内省) ------------------------------------------------
def test_contract_menu_keeps_list_bounds_and_optional_marks():
    text = render_contract("crimson", 20)
    assert "exhibit" in text                       # look 专属 kind 进菜单
    assert "×" in text                             # list 界限没被 _strip_optional 毁掉
    assert "?" in text                             # 可省略字段有标记
    assert "20" in text                            # 页数注入


def test_available_kinds_filtered_by_look_templates():
    assert "exhibit" in available_kinds("crimson")
    assert "exhibit" not in available_kinds("riso")   # riso 无 exhibit 模板


def test_contract_carries_look_guidance():
    # 引导段(guidance.md)必须拼进契约——look 的"报告哲学"所在
    assert "结论句" in render_contract("crimson", 14)


# ---- 输入容错(_normalize_deck):格式问题代码修,不浪费模型往返 -------------
def test_normalize_wraps_missing_data_envelope():
    payload = {"slides": [{"kind": "quote", "text": "x"}]}
    out = _normalize_deck(payload)
    assert out["slides"][0] == {"data": {"kind": "quote", "text": "x"}}


def test_normalize_coerces_numeric_number_and_pages():
    payload = {"slides": [
        {"data": {"kind": "section", "number": 2, "title": "x"}},
        {"data": {"kind": "toc", "items": [{"title": "y", "pages": 3}]}},
    ]}
    out = _normalize_deck(payload)
    assert out["slides"][0]["data"]["number"] == "02"
    assert out["slides"][1]["data"]["items"][0]["pages"] == "P03"


# ---- 事实评论官 ------------------------------------------------------------
def test_facts_catches_derived_number():
    deck = _deck([{"kind": "quote", "text": "人均产值 18.7 元"}])   # 8.77万/4689 推导值
    issues = check_facts(deck, SOURCE)
    assert any(i["type"] == "number-unsourced" for i in issues)


def test_facts_passes_verbatim_numbers():
    deck = _deck([{"kind": "quote", "text": "营收 8.77 万元,占比 81.88%"}])
    assert check_facts(deck, SOURCE) == []


def test_facts_catches_derived_series_value():
    # series 数值数组是字符串遍历的盲区:模型在这里推导补数/指数化打分
    deck = _deck([{"kind": "chart", "chart_type": "column",
                   "categories": ["甲", "乙"],
                   "series": [{"name": "x", "values": [81.88, 18.12]}]}])  # 18.12=100-81.88 推导
    issues = check_facts(deck, SOURCE)
    assert any(i["type"] == "number-unsourced" for i in issues)


def test_facts_allows_donut_complement_slice():
    # 占比图唯一补足 100% 的分块 = 呈现所需,放行;千分位逗号不阻断溯源
    deck = _deck([{"kind": "chart", "chart_type": "donut",
                   "categories": ["占比", "其他"],
                   "series": [{"name": "x", "values": [81.88, 18.12]}]}])
    assert check_facts(deck, SOURCE) == []


def test_facts_catches_fabricated_contact():
    deck = _deck([{"kind": "closing", "title": "谢谢", "contact": "+86 21 6237 0000"}])
    issues = check_facts(deck, SOURCE)
    assert any(i["type"] == "fabricated-contact" for i in issues)


# ---- 密度评论官(档位声明在 look 包) ---------------------------------------
def test_density_profile_lives_in_look_package():
    assert density_profile("crimson") is LOOKS["crimson"].density
    assert density_profile("swiss") == {}          # 稀疏是 swiss 的哲学
    assert density_profile("nonexistent") == {}


def test_density_catches_thin_kpi_and_exhibit_quota():
    deck = _deck([{"kind": "kpi", "title": "x",
                   "stats": [{"value": "1", "label": "a"}]}])
    types = {i["type"] for i in check_density(deck)}
    assert "thin-page" in types
    assert "exhibit-quota" in types


def test_density_silent_for_sparse_looks():
    deck = {"meta": {"title": "t"}, "theme": "swiss",
            "slides": [{"data": {"kind": "kpi", "title": "x",
                                 "stats": [{"value": "1", "label": "a"}]}}]}
    assert check_density(deck) == []


# ---- 页数派生(覆盖率导向,单一实现) ----------------------------------------
def test_recommend_pages_from_source_scales_and_clamps():
    assert recommend_pages_from_source("字" * 300 * 20) == 20
    assert recommend_pages_from_source("短") == 12            # 下限
    assert recommend_pages_from_source("字" * 300 * 99) == 48  # 上限


def test_recommend_pages_from_facts():
    assert recommend_pages(35) == 20       # 35/2.5=14 证据页 + 6 结构页
    assert recommend_pages(0) == 12        # 下限
    assert recommend_pages(500) == 48      # 上限


# ---- SpecLock 解析(look 包是唯一身份来源) ----------------------------------
def test_resolve_spec_look_and_fallback():
    assert resolve_spec("crimson").id == "crimson"
    assert isinstance(resolve_spec("no-such-look"), SpecLock)   # 兜底默认 look
