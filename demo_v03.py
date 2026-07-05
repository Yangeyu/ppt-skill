"""v0.3 端到端演示 —— 主题 → 七段管线 → 高颜值原生可编辑 .pptx。

用法:
  python demo_v03.py "你的主题" [页数]
  python demo_v03.py                      # 用默认主题（独立书店 zine）

有 LLM key(DASHSCOPE_API_KEY/OPENAI_API_KEY) → 走 freedom：现场生成设计语言+创作轨。
无 key → 自动降级确定性 seed。截图写到 ./out_v03/，pptx 写到 ./<slug>.pptx。"""
import sys
from pathlib import Path
from ppt_engine import llm
from ppt_engine.compose import generate


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "独立书店与 zine 文化指南"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    shots = Path("out_v03"); shots.mkdir(exist_ok=True)
    out = topic[:16].replace(" ", "_") + ".pptx"

    print(f"主题：{topic}")
    print(f"LLM：{'✓ ' + llm._provider()['name'] + '（freedom 路径）' if llm.available() else '✗（确定性 seed 兜底）'}\n")
    print("七段管线运行中：① 艺术总监 ② 身份评论官 ③ 套件实例化 ④ 规划路由 "
          "⑤ 浏览器排版 ⑥ 页面评论官+重生成 ⑦ 导出 …\n")

    r = generate(topic, out_path=out, tone="复古印刷·手作感",
                 n_slides=n, screenshot_dir=str(shots), aesthetic=False)

    print("── 设计语言（现场生成 / seed）──")
    print(f"  {r.spec.name} | 主色 {r.spec.colors['primary']} 纸 {r.spec.colors['bg-content']} "
          f"| 字阶比 {r.spec.type_scale.ratio} | 图像 {r.spec.image.style}")
    if r.spec.motifs:
        print(f"  母题 {[m.name for m in r.spec.motifs]}")
    if r.spec.rationale:
        print(f"  立意 {r.spec.rationale[:64]}")

    print("\n── 页面路由（双轨）──")
    for i, s in enumerate(r.deck.slides, 1):
        track = f"创作轨·{s.data.role}" if s.kind == "custom" else f"结构轨·{s.kind}"
        print(f"  {i:2d}. {track}")

    print("\n── 评论官 ──")
    idn = len([i for i in r.identity_issues if not isinstance(i, str) and getattr(i, 'level', '') == 'error'])
    print(f"  身份评论官: {idn} error")
    print(f"  结构评论官: {len(r.structural_errors)} error / "
          f"{len([i for i in r.structural_issues if i.level=='warning'])} warning")
    for i in r.structural_errors[:8]:
        print("     ", i)
    print(f"  创作页重生成: {r.rounds} 轮")

    print(f"\n✓ 输出: {out}")
    print(f"✓ 预览截图: {shots}/  （真实排版以浏览器截图为准；pptx 为原生可编辑）")
    print(f"  {r.summary()}")


if __name__ == "__main__":
    main()
