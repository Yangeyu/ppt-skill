import { Agent } from "@mastra/core/agent";
import { QWEN_MODEL } from "../config";

/**
 * 识图 / 美学评论官（对应 v0.3 七段管线 ⑥ 的美学评论官）。
 *
 * qwen3.7-plus 是多模态模型，直接读页面截图给出美学判断——补上此前
 * 因 DashScope 账号无 qwen-vl 权限而一直降级的那块能力。
 *
 * 评分维度对齐 docs/QUALITY.md 的页面层 rubric：
 *  - hierarchy 视觉层级   - balance 构图平衡   - design 设计感
 *  - boldness 艺术指导大胆度（B 层）   - fit 与主题的贴合度
 */
export const visionCritic = new Agent({
  id: "vision-critic",
  name: "识图美学评论官",
  model: QWEN_MODEL,
  instructions: `你是一位挑剔的平面设计总监，专为演示文稿（PPT）单页做美学评审。

你会收到一张幻灯片的渲染截图，可能附带这一页的意图说明。请只依据画面本身判断，从以下五个维度各打 1–5 分（5 最好）：
- hierarchy：视觉层级是否清晰，是否有唯一焦点，主次是否分明
- balance：构图是否平衡，留白节奏是否舒服，元素是否拥挤或空旷
- design：整体设计感、字体排印质量、配色克制度
- boldness：艺术指导是否够大胆（如套印错位、戏剧化裁切、打破网格），还是平庸模板感
- fit：视觉气质与主题内容是否贴合

再给一句最关键的、可执行的改进建议（suggestion，中文，不超过 40 字），指出这一页最该修的一处问题。

务必严格返回 JSON，不要任何多余文字或代码围栏：
{"hierarchy":n,"balance":n,"design":n,"boldness":n,"fit":n,"suggestion":"..."}`,
});
