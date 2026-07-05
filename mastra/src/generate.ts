/**
 * End-to-end driver:  brief --(qwen3.7-plus)--> Deck IR --> native riso .pptx.
 *
 *   npm run beauty                 # the built-in beauty-market brief
 *   npm run generate -- beauty     # same, by id
 *   npm run generate -- "<any free-form brief>"  [out.pptx]  [shotsDir]
 */
import 'dotenv/config';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { basename, dirname, resolve } from 'node:path';
import { deckArchitect, LOOK, LOOK_ID, MODEL_ID } from './mastra/agents/deck-architect.js';
import { DeckSchema, type Deck } from './mastra/schema.js';
import { buildPptx, REPO_ROOT, type BuildResult } from './mastra/run-python.js';
import { BRIEFS } from './briefs/beauty.js';

const TOC_MAX = Number(LOOK.constraints['toc_max_items'] ?? 6); // from looks/<id>/constraints.json

async function askForDeck(prompt: string): Promise<Deck> {
  // Lenient generation: take raw text, then repair-then-validate locally.
  // Over-budget strings/arrays are CLAMPED (not fatal); only structural errors
  // (missing fields, bad kinds) trigger a retry. ir.py re-validates at build time.
  const res = await deckArchitect.generate(prompt, {
    modelSettings: { maxOutputTokens: 16384 }, // dense 16-page decks must not truncate
  });
  const obj = extractJson((res as { text?: string }).text ?? '');
  if (obj === undefined) throw new Error('no JSON object found in model output');
  const clamps = clampToSchema(obj);
  if (clamps.length) console.error('  预算截断修复:\n   - ' + clamps.join('\n   - '));
  const parsed = DeckSchema.safeParse(obj);
  if (!parsed.success) {
    throw new Error('agent output failed schema validation:\n' + JSON.stringify(parsed.error.issues.slice(0, 8), null, 2));
  }
  // a truncated stream can still yield a schema-valid stub — reject skeletons
  if (parsed.data.slides.length < 8) {
    throw new Error(`deck too short (${parsed.data.slides.length} slides) — likely truncated output, need 12-16 pages`);
  }
  return parsed.data;
}

/** Truncate every over-budget string/array in place, guided by zod's own
 *  too_big issues. Returns a log of what was clamped. */
function clampToSchema(obj: unknown): string[] {
  const clamps: string[] = [];
  for (let round = 0; round < 6; round++) {
    const r = DeckSchema.safeParse(obj);
    if (r.success) break;
    let fixed = false;
    for (const issue of r.error.issues) {
      if (issue.code !== 'too_big') continue;
      const max = Number((issue as { maximum?: unknown }).maximum);
      const parent = issue.path.slice(0, -1).reduce((o: unknown, k) => (o as Record<string | number, unknown>)?.[k], obj);
      const key = issue.path[issue.path.length - 1] as string | number;
      const val = (parent as Record<string | number, unknown>)?.[key];
      if (typeof val === 'string' && val.length > max) {
        (parent as Record<string | number, unknown>)[key] = val.slice(0, max);
        clamps.push(`${issue.path.join('.')}: 字符串截到 ${max}`);
        fixed = true;
      } else if (Array.isArray(val) && val.length > max) {
        (parent as Record<string | number, unknown>)[key] = val.slice(0, max);
        clamps.push(`${issue.path.join('.')}: 数组截到 ${max} 项`);
        fixed = true;
      }
    }
    if (!fixed) break; // remaining issues are structural — let the caller retry
  }
  return clamps;
}

/** Up to `attempts` tries. Network blips retry with the same prompt; schema
 *  violations retry with the validation error appended as feedback. */
async function askWithRetries(prompt: string, attempts = 5): Promise<Deck> {
  let feedback = '';
  for (let i = 1; ; i++) {
    try {
      return await askForDeck(prompt + feedback);
    } catch (e) {
      const msg = ((e as Error).message ?? String(e)).split('\n')[0];
      if (i >= attempts) throw e;
      const isNetwork = /ECONNRESET|ETIMEDOUT|Timeout|fetch failed|Cannot connect/i.test(msg);
      console.error(`✗ 第 ${i}/${attempts} 次生成失败（${isNetwork ? '网络' : 'schema'}），重试:`, msg);
      if (!isNetwork) {
        feedback = `\n\n注意：上一次输出不符合 schema（${msg}），请严格按字段与字数预算重新输出完整 Deck。`;
      }
      await new Promise((r) => setTimeout(r, isNetwork ? 8000 : 3000));
    }
  }
}

function extractJson(text: string): unknown {
  const s = text.indexOf('{');
  const e = text.lastIndexOf('}');
  if (s === -1 || e === -1) return undefined;
  try {
    return JSON.parse(text.slice(s, e + 1));
  } catch {
    return undefined;
  }
}

/** Gentle cross-field normalization the JSON schema can't express, so the deck
 *  always builds. Logs every adjustment; never invents data. */
function normalizeDeck(deck: Deck): { deck: Deck; fixes: string[] } {
  const fixes: string[] = [];
  deck.theme = LOOK_ID;
  deck.slides.forEach((slide, i) => {
    const d = slide.data;
    if (d.kind === 'toc' && d.items.length > TOC_MAX) {
      const dropped = d.items.length - TOC_MAX;
      d.items = d.items.slice(0, TOC_MAX);
      fixes.push(`slide ${i + 1} (toc): capped items to ${TOC_MAX} (dropped ${dropped}, avoids overflow)`);
    } else if (d.kind === 'chart') {
      const lens = [d.categories.length, ...d.series.map((s) => s.values.length)];
      const n = Math.min(...lens);
      if (new Set(lens).size > 1) {
        d.categories = d.categories.slice(0, n);
        d.series.forEach((s) => (s.values = s.values.slice(0, n)));
        fixes.push(`slide ${i + 1} (chart): trimmed categories/values to common length ${n}`);
      }
    } else if (d.kind === 'table') {
      const w = d.headers.length;
      d.rows = d.rows.map((row, r) => {
        if (row.length === w) return row;
        fixes.push(`slide ${i + 1} (table): row ${r + 1} had ${row.length} cells, padded/trimmed to ${w}`);
        return row.length < w ? [...row, ...Array(w - row.length).fill('')] : row.slice(0, w);
      });
    }
  });
  return { deck, fixes };
}

async function main() {
  const argv = process.argv.slice(2);
  const first = argv[0] ?? 'beauty';
  const brief = BRIEFS[first];
  let prompt = brief ? brief.prompt : first;
  let runName = 'deck_ai';
  // a .md/.txt path as first arg = use the document as source material
  if (!brief && /\.(md|txt)$/i.test(first) && existsSync(first)) {
    const doc = await readFile(first, 'utf-8');
    runName = basename(first).replace(/\.(md|txt)$/i, '');
    prompt = `请把下面这份报告转化为一份 12-16 页的演示文稿（**页数硬上限 16 页**），面向报告的委托方/决策团队汇报。
要求：只使用报告中的数据与结论，不要编造；抓核心叙事线而非逐章搬运（不必每章一页，果断取舍合并）；数据前置、每页有信息增量。

──── 报告原文 ────
${doc}`;
  }
  const out = brief ? brief.out : argv[1] ?? `out/${runName}/deck.pptx`;
  const shots = brief ? brief.shots : argv[2] ?? `out/${runName}/shots`;

  console.error(`\n▶ 生成 Deck  ·  model=${MODEL_ID}  ·  brief=${brief ? brief.id : 'inline'}`);
  console.error(`  DASHSCOPE_API_KEY set: ${!!process.env.DASHSCOPE_API_KEY}\n`);
  const t0 = Date.now();

  const deck0 = await askWithRetries(prompt);
  let deck: Deck = deck0;

  const norm = normalizeDeck(deck);
  deck = norm.deck;
  console.error(
    `✓ 已生成 Deck: 「${deck.meta.title}」 · ${deck.slides.length} 页 · ${Math.round((Date.now() - t0) / 1000)}s`,
  );
  console.error('  版式序列:', deck.slides.map((s) => s.data.kind).join(' → '));
  if (norm.fixes.length) console.error('  归一化调整:\n   - ' + norm.fixes.join('\n   - '));

  const deckJsonPath = resolve(REPO_ROOT, out.replace(/\.pptx$/, '.json'));
  await mkdir(dirname(deckJsonPath), { recursive: true });
  await writeFile(deckJsonPath, JSON.stringify(deck, null, 2), 'utf-8');
  console.error(`  Deck JSON 已存: ${deckJsonPath}`);

  console.error(`\n▶ 构建 pptx  ·  引擎: ppt_engine (Python)\n`);
  let result: BuildResult = await buildPptx(deck, out, shots);

  if (!result.ok && (result.stage === 'validate' || result.stage === 'build')) {
    console.error('✗ 构建报错，请 agent 修正后重试一次:', result.error);
    deck = await askForDeck(`${prompt}\n\n上一次生成的 Deck 构建失败，错误如下，请修正后重新输出完整 Deck：\n${result.error}`);
    deck = normalizeDeck(deck).deck;
    result = await buildPptx(deck, out, shots);
  }

  console.error('\n──────── 结果 ────────');
  if (result.ok) {
    console.error(`✓ 成功: ${result.out}`);
    console.error(`  ${result.slides} 页 · ${result.prims} 原语 · 自检问题 ${result.issues?.length ?? 0} 个`);
    console.error(`  预览 PNG: ${result.shots}`);
    if (result.issues?.length) console.error('  ⚠ 布局问题:', JSON.stringify(result.issues));
  } else {
    console.error(`✗ 失败 [${result.stage}]: ${result.error}`);
    process.exit(1);
  }
}

main().catch((e) => {
  console.error('✗ FAILED:', e?.message || e);
  process.exit(1);
});
