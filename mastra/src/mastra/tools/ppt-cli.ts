import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

// skill 需要的唯一工具:ppt-skill 的 cli。通用一个工具而不是每命令一个——
// SKILL.md 里教的 bash 命令与工具调用 1:1 对应,skill 引导什么 agent 就执行什么。
const SKILL_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../ppt-skill");
const PY = resolve(SKILL_ROOT, ".venv/bin/python");

export const pptCli = createTool({
  id: "ppt_cli",
  description:
    "运行 ppt-skill 的引擎 cli(python -m ppt_engine.cli,已在 skill 根目录)。" +
    "args 为命令行参数数组,如 [\"--contract\",\"riso\",\"--slides\",\"20\"];" +
    "Deck IR JSON 通过 stdin 传入(不要用 --deck 文件参数,你没有文件系统)。" +
    "stdout 为一行 JSON(--contract 除外,输出纯文本契约)。",
  inputSchema: z.object({
    args: z.array(z.string()).describe("cli 参数数组"),
    stdin: z.string().optional().describe("经 stdin 传给 cli 的内容(Deck IR JSON)"),
  }),
  execute: async ({ args, stdin }) => {
    // 观测日志在这里打(而不是驱动的 onStepFinish):不依赖 Mastra step 结构
    console.log(`  → ppt_cli ${args.join(" ")}${stdin ? `  (stdin ${stdin.length} chars)` : ""}`);
    const r = spawnSync(PY, ["-m", "ppt_engine.cli", ...args], {
      cwd: SKILL_ROOT, input: stdin, encoding: "utf-8",
      maxBuffer: 64 * 1024 * 1024,
    });
    if (r.error) return { code: -1, stdout: "", stderr: String(r.error) };
    // stderr 是人类日志,截尾部防淹没上下文;stdout 是机器结果,原样返回
    return {
      code: r.status ?? 0,
      stdout: (r.stdout ?? "").trim(),
      stderr: (r.stderr ?? "").trim().split("\n").slice(-6).join("\n"),
    };
  },
});
