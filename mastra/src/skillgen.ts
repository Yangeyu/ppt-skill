/**
 * skill 装载形态的 e2e:通用 agent(bash + write_file)+ SKILL.md,自主走完整工作流。
 *
 *   pnpm skillgen demos/data/isdin_report_full.md riso
 *   pnpm skillgen <素材路径(相对 skill 根)> [look] [页数]   # look/页数可省,agent 按 skill 决策
 *
 * 与 pnpm generate(pipeline 形态)的分工:
 *   generate  驱动代码编排回路,测**引擎+契约+评论官**(确定性、便宜、适合回归)
 *   skillgen  agent 只有平台通用工具,SKILL.md 是唯一引导——测 **skill 的引导力与可迁移性**
 *
 * 素材不附全文:只给路径,agent 自己 cat(与真实装载场景一致)。
 */
import { skillRunner } from "./mastra/agents/skill-runner";

async function main() {
  const pos = process.argv.slice(2).filter((a) => !a.startsWith("--"));
  const srcPath = pos[0] ?? "demos/data/isdin_report_full.md";   // 相对 skill 根
  const look = pos[1] ?? "";
  const nSlides = pos[2] ? Number(pos[2]) : null;

  const ask =
    `请把素材 ${srcPath} 做成一份 PPT。` +
    (look ? `风格用 ${look}。` : `风格按素材气质自选。`) +
    (nSlides ? `页数 ${nSlides}。` : ``);

  const t0 = Date.now();
  let step = 0;
  const res = await skillRunner.generate(ask, {
    maxSteps: 40,
    onStepFinish: () => { step += 1; },   // 工具调用明细由工具自己打日志
  });

  console.log(`\n—— agent 最终报告(${((Date.now() - t0) / 1000).toFixed(0)}s / ${step} steps)——\n`);
  console.log(res.text);
}

main().catch((e) => { console.error(e); process.exit(1); });
