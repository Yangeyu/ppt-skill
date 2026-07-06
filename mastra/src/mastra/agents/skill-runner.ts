import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Agent } from "@mastra/core/agent";
import { QWEN_MODEL } from "../config";
import { bash, writeFile } from "../tools/generic";

/**
 * Skill 装载形态的主 agent —— 验证 ppt-skill 本体的引导力与**可迁移性**。
 *
 * 关键纪律:这里没有任何 ppt-skill 专用工具或适配逻辑。agent 拿到的只有
 * 平台通用能力(bash + write_file),SKILL.md 全文在运行时读进 instructions
 * (模拟平台的 skill 装载机制)。skill 教什么命令,agent 就原样 bash 执行——
 * 与 Claude Code 装载 ppt-master 完全同构。把 ppt-skill 目录搬去任何
 * 有 bash 的 agent 平台,行为应当一致;若这里需要写适配代码,说明 skill 有耦合。
 */
const SKILL_MD = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), "../../../../ppt-skill/SKILL.md"),
  "utf-8",
);

export const skillRunner = new Agent({
  id: "skill-runner",
  name: "PPT Skill Runner",
  model: QWEN_MODEL,
  instructions: `你是一个会使用工具的通用 agent,具备 bash(在 skill 根目录执行命令)
和 write_file(写文件)两个基础能力。

你装载了一个名为 ppt-tool 的 skill,按它的指引完成用户任务。skill 全文如下:

${SKILL_MD}`,
  tools: { bash, writeFile },
});
