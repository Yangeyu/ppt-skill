import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Agent } from "@mastra/core/agent";
import { QWEN_MODEL } from "../config";
import { pptCli } from "../tools/ppt-cli";

/**
 * Skill 装载形态的主 agent —— 验证 ppt-skill 本体的引导力。
 *
 * 与 deckGenerator(pipeline 形态)的本质区别:这里**没有任何驱动代码替 agent
 * 走流程**。SKILL.md 全文在运行时读进 instructions(就像 Claude Code 装载 skill),
 * agent 自己决定调 ppt_cli 取契约、写 IR、跑复核、循环修复、触发生成——
 * 工作流对不对,考验的是 SKILL.md 写得好不好,而不是 generate.ts 写得好不好。
 */
const SKILL_MD = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), "../../../../ppt-skill/SKILL.md"),
  "utf-8",
);

export const skillRunner = new Agent({
  id: "skill-runner",
  name: "PPT Skill Runner",
  model: QWEN_MODEL,
  instructions: `你是一个会使用工具的 agent。你装载了一个名为 ppt-tool 的 skill,
它教你如何把素材变成高质量 PPT。skill 全文如下:

${SKILL_MD}

—— 环境适配(重要)——
- skill 里的 bash 命令 \`python -m ppt_engine.cli ...\` 对应你的 ppt_cli 工具:
  参数原样进 args 数组(如 --contract riso --slides 20 →
  {"args":["--contract","riso","--slides","20"]})。
- 你没有文件系统:Deck IR JSON 不写文件,直接放 ppt_cli 的 stdin 字段,
  并且**不要**传 --deck 参数(cli 会从 stdin 读)。素材原文在用户消息里,
  --source 参数直接用用户给出的素材路径(cli 在 skill 根目录能读到)。
- 严格按 skill 的工作流走:取契约前不要凭记忆写 IR;复核不过就修 IR 重新提交,
  直到 IR 校验/fact_issues/density_issues 全零,再做完整生成。
- 完成后向用户报告:产物路径、页数、三类 issues 数、你被评论官退回过几次、
  分别因为什么。`,
  tools: { pptCli },
});
