/**
 * Zod mirror of ppt_engine/ir.py — the contract between the LLM and the engine.
 *
 * Same discriminated union on `kind`, same word budgets. The model fills this
 * schema (via Mastra structuredOutput); the Python side re-validates against the
 * pydantic original as the final gate. Keep the two in sync.
 *
 * Note: string `.max()` counts UTF-16 units, which equals Python `len()` for the
 * BMP CJK we use here — so budgets line up with ir.py.
 */
import { z } from 'zod';

// ---- leaf pieces ---------------------------------------------------------
export const StatSchema = z.object({
  value: z.string().max(8).describe('the big number, e.g. "42%", "3.2", "+15pp"'),
  label: z.string().max(16).describe('what the number measures'),
  delta: z.string().max(12).nullish().describe('change vs baseline, e.g. "+7pp"'),
  delta_dir: z.enum(['up', 'down', 'flat']).default('flat'),
});

export const BulletSchema = z.object({
  text: z.string().max(80),
  emphasis: z.boolean().default(false),
});

export const SeriesSchema = z.object({
  name: z.string().max(20),
  values: z.array(z.number()).describe('one value per category, same length as categories'),
});

export const ColumnSchema = z.object({
  heading: z.string().max(24),
  points: z.array(z.string().max(60)).min(1).max(5),
});

export const TocItemSchema = z.object({ title: z.string().max(24) });

export const StepSchema = z.object({
  title: z.string().max(16),
  desc: z.string().max(48).default(''),
  icon: z.string().default('check-circle'),
});

export const IconCardSchema = z.object({
  icon: z.string().describe('one valid icon name from the look whitelist (cli --describe)'),
  title: z.string().max(12),
  subtitle: z.string().max(32).default('').describe('latin/mono caption'),
  lines: z.array(z.string().max(20)).max(3).default([]).describe('1-3 short lines, each <= ~14 chars'),
  punch: z.string().max(20).default('').describe('the colored take-away line'),
});

export const MilestoneSchema = z.object({
  year: z.string().max(10),
  title: z.string().max(16),
  desc: z.string().max(44).default(''),
});

export const PillarSchema = z.object({
  heading: z.string().max(16),
  tag: z.string().max(22).default('').describe('latin/mono sub-label'),
  points: z.array(z.string().max(60)).min(1).max(5),
});

// ---- per-archetype data --------------------------------------------------
const CoverData = z.object({
  kind: z.literal('cover'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(28),
  subtitle: z.string().max(48).default(''),
  footer: z.string().max(48).default(''),
});

const HeroData = z.object({
  kind: z.literal('hero'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(28),
  subtitle: z.string().max(48).default(''),
  footer: z.string().max(48).default(''),
  art: z.string().max(16).default('sun').describe('motif seed for generated poster art: sun | city | wave | ...'),
  src: z.string().max(240).default('').describe('optional source image path to riso-ify; leave "" to auto-generate art'),
});

const SectionData = z.object({
  kind: z.literal('section'),
  number: z.string().max(4).default('').describe('e.g. "01"'),
  title: z.string().max(20),
  subtitle: z.string().max(40).default(''),
});

const KpiData = z.object({
  kind: z.literal('kpi'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  stats: z.array(StatSchema).min(2).max(4),
});

const BulletsData = z.object({
  kind: z.literal('bullets'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  bullets: z.array(BulletSchema).min(1).max(6),
});

const ChartData = z.object({
  kind: z.literal('chart'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  chart_type: z.enum(['column', 'bar', 'line']).default('column'),
  categories: z.array(z.string()).min(2).max(8),
  series: z.array(SeriesSchema).min(1).max(4),
  takeaway: z.string().max(60).default(''),
});

const TocData = z.object({
  kind: z.literal('toc'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24).default('目录'),
  items: z.array(TocItemSchema).min(2).max(6), // <=6 fits the riso toc layout (8 overflows)
});

const TwoColData = z.object({
  kind: z.literal('two_col'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  left: ColumnSchema,
  right: ColumnSchema,
});

const CompareData = z.object({
  kind: z.literal('comparison'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  left: ColumnSchema,
  right: ColumnSchema,
});

const ProcessData = z.object({
  kind: z.literal('process'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  steps: z.array(StepSchema).min(2).max(5),
});

const IconGridData = z.object({
  kind: z.literal('icon_grid'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  subtitle: z.string().max(56).default('').describe('mono strapline under the title'),
  cards: z.array(IconCardSchema).min(2).max(6),
});

const TimelineData = z.object({
  kind: z.literal('timeline'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  subtitle: z.string().max(56).default(''),
  milestones: z.array(MilestoneSchema).min(2).max(5),
});

const TableData = z.object({
  kind: z.literal('table'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  subtitle: z.string().max(56).default(''),
  headers: z.array(z.string()).min(2).max(5),
  rows: z.array(z.array(z.string())).min(1).max(8).describe('each row has exactly headers.length cells'),
});

const PillarsData = z.object({
  kind: z.literal('pillars'),
  eyebrow: z.string().max(24).default(''),
  title: z.string().max(24),
  subtitle: z.string().max(56).default(''),
  columns: z.array(PillarSchema).min(2).max(4),
});

const QuoteData = z.object({
  kind: z.literal('quote'),
  quote: z.string().max(80),
  attribution: z.string().max(40).default(''),
});

const ClosingData = z.object({
  kind: z.literal('closing'),
  title: z.string().max(20).default('谢谢'),
  subtitle: z.string().max(48).default(''),
  contact: z.string().max(48).default(''),
});

export const SlideDataSchema = z.discriminatedUnion('kind', [
  CoverData,
  HeroData,
  SectionData,
  KpiData,
  BulletsData,
  ChartData,
  TocData,
  TwoColData,
  CompareData,
  ProcessData,
  IconGridData,
  TimelineData,
  TableData,
  PillarsData,
  QuoteData,
  ClosingData,
]);

export const SlideSchema = z.object({
  data: SlideDataSchema,
  notes: z.string().nullish(),
});

export const DeckMetaSchema = z.object({
  title: z.string(),
  lang: z.enum(['zh', 'en']).default('zh'),
});

export const DeckSchema = z.object({
  meta: DeckMetaSchema,
  theme: z.string().default('riso'),
  slides: z.array(SlideSchema).min(1).max(20),
});

export type Deck = z.infer<typeof DeckSchema>;
export type Slide = z.infer<typeof SlideSchema>;
export type SlideData = z.infer<typeof SlideDataSchema>;
