import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * 平台通用工具 —— 模拟任意 agent 平台的基础能力(bash + 写文件),
 * **零 skill 专用逻辑**。这是 skill 可迁移性的关键:ppt-skill 对 agent 的
 * 全部要求就是"能执行 bash、能写文件"(与 Claude Code 装载 ppt-master 同构),
 * SKILL.md 里的命令原样执行,换 agent 平台不需要任何适配代码。
 *
 * 工作目录固定为 skill 根(SKILL.md 的约定:"所有命令在本 skill 根目录执行")。
 */
const SKILL_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../ppt-skill");

export const bash = createTool({
  id: "bash",
  description:
    "在 skill 根目录执行一条 bash 命令,返回 exit code 与 stdout/stderr。" +
    "长输出会截断,机器结果(一行 JSON)不受影响。",
  inputSchema: z.object({
    command: z.string().describe("要执行的 bash 命令"),
  }),
  execute: async ({ command }) => {
    console.log(`  $ ${command.length > 120 ? command.slice(0, 120) + " …" : command}`);
    const r = spawnSync("/bin/zsh", ["-lc", command], {
      cwd: SKILL_ROOT, encoding: "utf-8", timeout: 600_000,
      maxBuffer: 64 * 1024 * 1024,
    });
    if (r.error) return { code: -1, stdout: "", stderr: String(r.error) };
    const clip = (s: string, n: number) =>
      s.length > n ? `${s.slice(0, n)}\n…[截断,共 ${s.length} 字符]` : s;
    return {
      code: r.status ?? 0,
      stdout: clip((r.stdout ?? "").trim(), 20_000),
      stderr: clip((r.stderr ?? "").trim().split("\n").slice(-8).join("\n"), 2_000),
    };
  },
});

export const writeFile = createTool({
  id: "write_file",
  description: "把内容写入文件(路径相对 skill 根目录)。写 deck.json 等中间产物用。",
  inputSchema: z.object({
    path: z.string().describe("相对 skill 根目录的文件路径"),
    content: z.string().describe("文件内容"),
  }),
  execute: async ({ path, content }) => {
    console.log(`  ✎ write ${path} (${content.length} chars)`);
    const abs = resolve(SKILL_ROOT, path);
    if (!abs.startsWith(SKILL_ROOT)) return { ok: false, error: "路径越界" };
    mkdirSync(dirname(abs), { recursive: true });
    writeFileSync(abs, content, "utf-8");
    return { ok: true, path };
  },
});
