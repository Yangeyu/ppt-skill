import { Agent } from "@mastra/core/agent";
import { QWEN_MODEL } from "../config";

/**
 * Deck 生成官 —— 真 agent e2e 的主角:素材原文 + 生成契约 → 整份 Deck IR(JSON)。
 *
 * instructions 只放稳定人设;版式菜单/字数预算/叙事纪律**不写在这里**——
 * 它们随代码演进,由驱动(src/generate.ts)在运行时调 `ppt_engine.cli --contract <look>`
 * 现场获取并拼进用户消息(契约单一来源原则,见 ppt_engine/contract.py)。
 */
export const deckGenerator = new Agent({
  id: "deck-generator",
  name: "Deck 生成官",
  model: QWEN_MODEL,
  instructions: `你是顶级咨询公司的报告策划,擅长把研究素材组织成高质量演示文稿的
结构化 IR。用户消息会给你:①生成契约(版式菜单/字数硬预算/事实纪律/该风格的
叙事与组织纪律)②素材原文,或 ③上一版 IR 的机器复核问题清单(修复轮)。

严格遵守契约——尤其字数上限与事实纪律(数字只能逐字引用素材)。
只输出一个合法 JSON 对象(Deck IR),不要代码围栏、不要任何解释文字。`,
});
