"""确定性地板测试 —— 不依赖浏览器/LLM，验证 A 层评论官与令牌纪律。

覆盖：seed 过身份评论官 / pos-neg 可读性归一 / SpecLock 与 Theme 接口兼容 /
身份评论官能拒坏设计语言 / 结构评论官能抓越界·重叠·离板色·低对比。"""
import re
from ppt_engine.spec import SpecLock, TypeScale, contrast_ratio, legibilize
from ppt_engine.theme import THEMES
from ppt_engine.artdirect import critique_identity
from ppt_engine.artdirect.identity_critic import identity_ok
from ppt_engine.critic import critique_structure

SEEDS = list(THEMES)


def _errs(issues):
    return [i for i in issues if i.level == "error"]


# ---- 身份层 --------------------------------------------------------------
def test_all_seeds_pass_identity():
    for s in SEEDS:
        assert identity_ok(SpecLock.from_seed(s)), f"seed {s} 未过身份评论官"


def test_seeds_semantic_colors_legible():
    for s in SEEDS:
        sp = SpecLock.from_seed(s)
        paper = sp.colors["bg-content"]
        assert contrast_ratio(sp.colors["pos"], paper) >= 3.1, f"{s} pos 不可读"
        assert contrast_ratio(sp.colors["neg"], paper) >= 3.1, f"{s} neg 不可读"


def test_legibilize_darkens_light_semantic():
    colors = {"bg-content": "#FFFFFF", "pos": "#10B981", "neg": "#F43F5E"}
    before = contrast_ratio(colors["pos"], "#FFFFFF")
    legibilize(colors)
    after = contrast_ratio(colors["pos"], "#FFFFFF")
    assert before < 3.0 <= after, "legibilize 未把浅绿压到可读"


def test_identity_rejects_bad_language():
    bad = SpecLock.from_seed("editorial")
    bad.type_scale = TypeScale(ratio=1.07, display=24, h1=22, h2=21, body=20, caption=19, micro=18)  # 非模块化+对比弱
    bad.display_font = "Impact"          # 不可嵌入
    errs = _errs(critique_identity(bad))
    checks = {e.check for e in errs}
    assert "ID-TS-1" in checks      # 比例非模块化
    assert "ID-TS-3" in checks      # display/body < 3
    assert "ID-FT-4" in checks      # 字体不可嵌入


# ---- 结构层（合成已测原语，无需浏览器） ----------------------------------
SPEC = SpecLock.from_seed("editorial")
INK = "rgb(33, 28, 24)"        # #211C18 ink
PAPER = "rgb(245, 240, 230)"   # #F5F0E6 bg-content
BG_RECT = {"kind": "rect", "x": 0, "y": 0, "w": 1280, "h": 720, "z": -20, "fill": PAPER}


def _text(t, x, y, w=300, h=40, color=INK, size=20, deco=False):
    return {"kind": "text", "x": x, "y": y, "w": w, "h": h, "text": t,
            "color": color, "fontSizePx": size, "fontWeight": 400,
            "family": "Noto Sans SC", "deco": deco, "z": 10}


def test_structural_clean_page_no_errors():
    page = [BG_RECT, _text("合规正文", 100, 100), _text("第二段落", 100, 300)]
    assert _errs(critique_structure([page], SPEC)) == []


def test_structural_detects_overflow():
    page = [BG_RECT, _text("越界文本", -120, 100)]
    assert any(e.check == "PG-GM-1" for e in _errs(critique_structure([page], SPEC)))


def test_structural_detects_overlap():
    page = [BG_RECT, _text("甲甲甲甲", 100, 100), _text("乙乙乙乙", 110, 105)]
    assert any(e.check == "PG-GM-2" for e in _errs(critique_structure([page], SPEC)))


def test_structural_detects_off_token_color():
    page = [BG_RECT, _text("离板色文字", 100, 100, color="rgb(255, 0, 0)")]  # #FF0000 不在令牌
    assert any(e.check == "PG-CL-1" for e in _errs(critique_structure([page], SPEC)))


def test_structural_detects_low_contrast():
    # 纸色文字压纸底 → 不可读
    page = [BG_RECT, _text("看不见的正文内容", 100, 100, color=PAPER)]
    assert any(e.check == "PG-CL-2" for e in _errs(critique_structure([page], SPEC)))


def test_punctuation_only_contrast_is_warning_not_error():
    page = [BG_RECT, _text("·", 100, 100, color=PAPER)]   # 纯标点装饰
    assert not any(e.check == "PG-CL-2" for e in _errs(critique_structure([page], SPEC)))


# ---- SpecLock 与 Theme 接口兼容（render/oox/fonts 不改即用） --------------
def test_speclock_theme_compatible_surface():
    sp = SpecLock.from_seed("aurora")
    assert isinstance(sp.css_vars(), str) and "--type-display" in sp.css_vars()
    assert set(sp.scheme()) >= {"dk1", "lt1", "accent1", "accent2"}
    assert sp.color_slot()                      # 反查表非空
    assert sp.families() and sp.body_font in sp.families()
