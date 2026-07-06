/**
 * skill 装载形态的 e2e:主 agent(装载 SKILL.md)+ ppt_cli 工具,自主走完整工作流。
 *
 *   pnpm skillgen ../ppt-skill/demos/data/isdin_report_full.md riso
 *   pnpm skillgen <素材.md> [look] [页数]      # look/页数可省,agent 自己按 skill 决策
 *
 * 与 pnpm generate(pipeline 形态)的分工:
 *   generate  驱动代码编排回路,测**引擎+契约+评论官**(确定性、便宜、适合回归)
 *   skillgen  agent 自主编排,测 **SKILL.md 引导力本身**(真实 skill 消费形态)
 */
import { readFileSync } from "node:fs";
import { relative, resolve } from "node:path";
import { skillRunner } from "./mastra/agents/skill-runner";

async function main() {
  const pos = process.argv.slice(2).filter((a) => !a.startsWith("--"));
  const srcPath = resolve(process.cwd(), pos[0] ?? "../ppt-skill/demos/data/isdin_report_full.md");
  const look = pos[1] ?? "";
  const nSlides = pos[2] ? Number(pos[2]) : null;
  const source = readFileSync(srcPath, "utf-8");
  // cli 在 skill 根目录运行,--source 要给相对 skill 根的路径
  const skillRelPath = relative(resolve(process.cwd(), "../ppt-skill"), srcPath);

  const ask =
    `请把下面的素材做成一份 PPT。` +
    (look ? `风格用 ${look}。` : `风格按素材气质自选。`) +
    (nSlides ? `页数 ${nSlides}。` : ``) +
    `\n素材文件路径(给 --source 用):${skillRelPath}\n\n素材全文:\n\n${source}`;

  const t0 = Date.now();
  let step = 0;
  const res = await skillRunner.generate(ask, {
    maxSteps: 40,
    onStepFinish: () => { step += 1; },   // 工具调用明细由 ppt_cli 自己打日志
  });

  console.log(`\n—— agent 最终报告(${((Date.now() - t0) / 1000).toFixed(0)}s / ${step} steps)——\n`);
  console.log(res.text);
}

main().catch((e) => { console.error(e); process.exit(1); });
