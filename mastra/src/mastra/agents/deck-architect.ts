/**
 * The deck-architect: turns a market brief into a Deck IR for the active look.
 * Model: alibaba-cn/qwen3.7-plus (reads DASHSCOPE_API_KEY via Mastra's router).
 *
 * The look-specific parts of the prompt (aesthetic, archetype cheat-sheet,
 * composition rhythm) and the icon whitelist are NOT hardcoded here — they come
 * from the look package via `python3 -m ppt_engine.cli --describe <look>`, so
 * the engine stays the single source of truth.
 */
import { Agent } from '@mastra/core/agent';
import { buildPptxTool } from '../tools/build-pptx.js';
import { describeLook, type LookInfo } from '../run-python.js';

export const MODEL_ID = 'alibaba-cn/qwen3.7-plus';
export const LOOK_ID = process.env.PPT_LOOK || 'riso';
export const LOOK: LookInfo = describeLook(LOOK_ID);

// Generic frame (role + hard rules + output format); the look fragment fills the middle.
// NOTE: the literal word "Deck JSON" below is required — DashScope's json_object
// response_format rejects requests whose messages never mention "json".
const instructions = `你是一位资深「信息设计师 + 市场分析师」，专为 **${LOOK.name}（${LOOK_ID}）** 主题设计中文演示文稿。
你的产出是一份 Deck IR（结构化数据），随后会被原生渲染成可编辑的 .pptx。你只负责"选版式、填内容"，排版由引擎完成。

${LOOK.agent_instructions}

# 硬性规则（违反会被引擎拒绝）
1. 严守每个字段的字数预算——这是海报排版，超长必被拒。**宁短勿长**，标题锐利成词组，不要写整句。
2. chart：每个 series.values 的长度必须**等于** categories 的长度，一一对应。
3. table：每一行 rows[i] 的单元格数必须**等于** headers 的数量。
4. icon 只能从图标表里选，挑语义最接近的；用错名字图标会渲染成空白。
   图标表：${LOOK.icons.join(', ')}
5. 数字只能来自用户提供的素材，**不要编造统计数据**；没有数据就用定性表达。

只输出符合 schema 的 **Deck JSON** 数据（严格合法的 JSON 结构），不要任何额外解释，也不要用 markdown 代码块包裹。`;

export const deckArchitect = new Agent({
  id: 'deck-architect',
  name: `${LOOK.name} Deck Architect`,
  model: MODEL_ID,
  instructions,
  tools: { buildPptxTool },
});
