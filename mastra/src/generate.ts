/**
 * 真 agent e2e 驱动(三段流)—— 素材 → ①事实清单 → ②叙事大纲 → ③Deck IR → 视觉闭环。
 *
 *   素材.md → deckGenerator ①factsheet ─check→ ②outline ─check→ ③deck IR ─check→ 引擎 build
 *                   ↑____________机器审核问题回喂(每段独立修复回路)___________|
 *                                                                              ↓
 *              visionCritic 逐页读截图评分 → 低分页建议回喂 → 一轮修订重建(可选)
 *
 * 所有契约由 `ppt_engine.cli --contract --stage ...` 现场渲染(单一来源);
 * 所有审核由 `cli --check-only --stage ...` 机器执行(数字溯源/证据覆盖/密度/页数硬控)。
 * 阶段产物(factsheet/outline/agent_deck.json)全部落盘供审计。
 *
 * 用法: pnpm generate ../demos/data/isdin_report_full.md [look=crimson] [页数=15] [--no-vision]
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { deckGenerator } from "./mastra/agents/deck-generator";
import { visionCritic } from "./mastra/agents/vision-critic";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const PY = resolve(ROOT, ".venv/bin/python");

function cli(args: string[], input?: string): { code: number; stdout: string } {
  const r = spawnSync(PY, ["-m", "ppt_engine.cli", ...args], {
    cwd: ROOT, input, encoding: "utf-8", maxBuffer: 64 * 1024 * 1024,
  });
  if (r.error) throw r.error;
  if (r.stderr) process.stderr.write(r.stderr);
  return { code: r.status ?? 0, stdout: r.stdout };
}

function contractOf(stage: "factsheet" | "outline" | "deck", look: string, n: number): string {
  const r = cli(["--contract", look, "--stage", stage, "--slides", String(n)]);
  if (r.code !== 0) throw new Error(`取 ${stage} 契约失败: ${r.stdout}`);
  return r.stdout;
}

function parseJson(text: string): any {
  let t = text.trim().replace(/^```[a-z]*\n?/i, "").replace(/\n?```$/, "").trim();
  const s = t.indexOf("{"), e = t.lastIndexOf("}");
  if (s < 0 || e <= s) throw new Error(`模型输出中找不到 JSON: ${t.slice(0, 120)}…`);
  return JSON.parse(t.slice(s, e + 1));
}

/** 从 cli 复核返回里汇总问题清单(校验错误 + 各评论官 issues)。 */
function problemsOf(rep: any): string[] {
  const out: string[] = [];
  for (const er of rep.errors ?? []) out.push(`- [IR校验] ${er.loc.join(".")}: ${er.msg}`);
  for (const key of ["issues", "fact_issues", "density_issues"]) {
    for (const it of rep[key] ?? []) {
      out.push(`- [${it.type ?? key}] ${it.detail ?? JSON.stringify(it)}`);
    }
  }
  return out;
}

/** LLM 调用带网络重试:DashScope 偶发 headers timeout,不该打死整个流程。 */
async function genWithRetry(ask: string, tries = 3): Promise<string> {
  for (let attempt = 1; ; attempt++) {
    try {
      return (await deckGenerator.generate([{ role: "user", content: ask }])).text;
    } catch (e) {
      if (attempt >= tries) throw e;
      console.error(`  (API 波动,${attempt * 10}s 后重试)`);
      await new Promise((r) => setTimeout(r, attempt * 10_000));
    }
  }
}

/** 一个阶段的生成+机器审核回路:审核问题原文回喂,直到干净或超轮数。 */
async function stageLoop(label: string, ask: string, maxRepair: number,
                         check: (payload: any) => string[]): Promise<any> {
  let payload: any = null;
  for (let round = 0; round <= maxRepair; round++) {
    console.error(`→ ${label}(第 ${round + 1} 次)…`);
    payload = parseJson(await genWithRetry(ask));
    const problems = check(payload);
    if (problems.length === 0) return payload;
    console.error(`  ✗ ${problems.length} 处问题,回喂修复`);
    for (const p of problems.slice(0, 3)) console.error(`    ${p.slice(0, 110)}`);
    if (round === maxRepair)
      throw new Error(`${label} ${maxRepair + 1} 轮未过审:\n${problems.join("\n")}`);
    ask = `你上一版${label}未通过机器审核:\n${problems.slice(0, 14).join("\n")}\n\n` +
          `请修正后重新输出**完整** JSON,其余内容保持不变。上一版:\n${JSON.stringify(payload)}`;
  }
  return payload;
}

async function main() {
  const srcPath = resolve(process.cwd(), process.argv[2] ?? "../demos/data/isdin_report_full.md");
  const look = process.argv[3] ?? "crimson";
  const nSlides = Number(process.argv[4] ?? 15);
  const withVision = !process.argv.includes("--no-vision");
  const source = readFileSync(srcPath, "utf-8");

  const stem = basename(srcPath).replace(/\.[^.]+$/, "");
  const dest = resolve(ROOT, "out", `${stem}_${look}_mastra`);
  mkdirSync(dest, { recursive: true });
  const save = (name: string, obj: unknown) =>
    writeFileSync(resolve(dest, name), JSON.stringify(obj, null, 1), "utf-8");

  // ① 事实清单:素材 → 结构化 facts(逐字溯源)
  const factsheet = await stageLoop(
    "事实清单", `${contractOf("factsheet", look, nSlides)}\n\n素材:\n\n${source}`, 2,
    (p) => problemsOf(JSON.parse(
      cli(["--check-only", "--stage", "factsheet", "--source", srcPath], JSON.stringify(p)).stdout)));
  save("factsheet.json", factsheet);
  console.error(`  ✓ ${factsheet.facts.length} 条事实`);

  // ② 叙事大纲:先组织后填格(版式路由/证据分配/页数硬控在此收敛)
  const fsPath = resolve(dest, "factsheet.json");
  const outline = await stageLoop(
    "叙事大纲",
    `${contractOf("outline", look, nSlides)}\n\n事实清单:\n${JSON.stringify(factsheet)}\n\n素材原文(供理解上下文):\n\n${source}`,
    3,
    (p) => problemsOf(JSON.parse(
      cli(["--check-only", "--stage", "outline", "--look", look, "--slides", String(nSlides),
           "--factsheet", fsPath], JSON.stringify(p)).stdout)));
  save("outline.json", outline);
  console.error(`  ✓ ${outline.slides.length} 页大纲 · 路由 ${outline.slides.map((s: any) => s.kind).join(",")}`);

  // ③ 逐页落地成 Deck IR(校验+事实+密度三重复核)
  const deckCheck = (p: any) => {
    p.theme = look;
    return problemsOf(JSON.parse(
      cli(["--check-only", "--source", srcPath], JSON.stringify(p)).stdout));
  };
  let deck = await stageLoop(
    "Deck IR",
    `${contractOf("deck", look, nSlides)}\n\n已批准的叙事大纲(逐页落地,不得改动版式路由与论点;` +
    `thesis 是该页标题的底稿,fact_ids 指向要用的证据):\n${JSON.stringify(outline)}\n\n` +
    `事实清单:\n${JSON.stringify(factsheet)}\n\n素材原文(数字逐字以此为准):\n\n${source}`,
    3, deckCheck);
  deck.theme = look;
  save("agent_deck.json", deck);

  // build(附 LibreOffice 真渲染,供视觉评审——浏览器截图不含原生图表/hero 图)
  const outPptx = resolve(dest, `${stem}_${look}_mastra.pptx`);
  const build = () => JSON.parse(cli(
    ["--source", srcPath, "--out", outPptx, "--shots", resolve(dest, "preview"), "--render"],
    JSON.stringify(deck)).stdout);
  let result = build();
  if (!result.ok) throw new Error(`生成失败: ${result.error}`);

  // ④a 布局闭环:结构评论官在真实几何上抓到的问题(溢出/重叠)回喂修 IR
  for (let round = 0; result.issues.length > 0 && round < 2; round++) {
    console.error(`→ 布局问题回喂修订(${result.issues.length} 处)…`);
    const probs = result.issues.map((i: any) =>
      `- 第 ${i.slide} 页 ${i.type}:「${i.detail}」——精炼该处文案(标题溢出=缩短到单行能容纳)`);
    deck = await stageLoop("Deck IR(布局修订)",
      `你产出的 Deck IR 经真实排版发现布局问题:\n${probs.join("\n")}\n\n` +
      `只修改涉及页的相应字段,其他页保持不变。当前版:\n${JSON.stringify(deck)}`,
      1, deckCheck);
    deck.theme = look;
    save("agent_deck.json", deck);
    result = build();
  }

  // ④b 视觉闭环(visionCritic 低分页回喂,至多一轮修订)
  if (withVision) {
    console.error("→ visionCritic 逐页评审…");
    const shotsDir = result.rendered ?? result.shots;   // 优先真渲染
    const shots = readdirSync(shotsDir).filter((f) => f.endsWith(".png")).sort();
    const weak: string[] = [];
    const reviews: any[] = [];
    const reviewOne = async (i: number, f: string) => {
      const img = `data:image/png;base64,${readFileSync(resolve(shotsDir, f)).toString("base64")}`;
      const intent = outline.slides[i]?.thesis ?? "";
      try {
        const res = await visionCritic.generate([{ role: "user", content: [
          { type: "image", image: img, mimeType: "image/png" },
          { type: "text", text: `这一页的意图:${intent}。请评审。` +
            `(注:预览渲染会替换嵌入字体,请忽略字体风格本身,关注布局/层级/密度/留白)` },
        ]}]);
        const r = parseJson(res.text);
        reviews[i] = { page: i + 1, file: f, ...r };
        if (Math.min(r.hierarchy, r.balance, r.design) <= 2)
          weak.push(`- 第 ${i + 1} 页(${deck.slides[i]?.data?.kind}): ${r.suggestion} ` +
                    `(hierarchy=${r.hierarchy} balance=${r.balance} design=${r.design})`);
      } catch (e) { console.error(`  (第 ${i + 1} 页评审失败,跳过: ${e})`); }
    };
    for (let b = 0; b < shots.length; b += 5)          // 5 页一批并行,避免限流
      await Promise.all(shots.slice(b, b + 5).map((f, j) => reviewOne(b + j, f)));
    save("vision_reviews.json", reviews.filter(Boolean));
    const avg = reviews.length
      ? (reviews.reduce((a, r) => a + (r.hierarchy + r.balance + r.design + r.boldness + r.fit) / 5, 0) / reviews.length).toFixed(2)
      : "n/a";
    console.error(`  ✓ 均分 ${avg} · 低分页 ${weak.length}`);

    if (weak.length > 0) {
      console.error("→ 低分页回喂修订(1 轮)…");
      deck = await stageLoop(
        "Deck IR(视觉修订)",
        `你之前产出的 Deck IR 经视觉评审发现以下页面观感问题,请只调整涉及页的内容组织` +
        `(如拆分/补充/精简该页素材),不要改动其他页:\n${weak.join("\n")}\n\n当前版:\n${JSON.stringify(deck)}`,
        1, deckCheck);
      deck.theme = look;
      save("agent_deck.json", deck);
      result = build();
    }
  }

  console.error(`✓ ${result.out}\n  ${result.slides} 页 · 路由 ${result.kinds.join(",")}\n` +
    `  布局 ${result.issues.length} · 事实 ${(result.fact_issues ?? []).length} · 密度 ${(result.density_issues ?? []).length}`);
  console.log(JSON.stringify(result));
}

main().catch((e) => { console.error(e); process.exit(1); });
