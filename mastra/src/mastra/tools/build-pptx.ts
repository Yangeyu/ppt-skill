/**
 * Mastra tool wrapping the Python ppt_engine — this is how the ppt tool is
 * "plugged into" the agent runtime. The driver script calls buildPptx() directly
 * for a deterministic pipeline, but registering the tool also lets the agent (or
 * a future workflow / `mastra dev` session) render decks conversationally.
 */
import { createTool } from '@mastra/core/tools';
import { z } from 'zod';
import { DeckSchema } from '../schema.js';
import { buildPptx } from '../run-python.js';

export const buildPptxTool = createTool({
  id: 'build-riso-pptx',
  description:
    'Render a complete Deck IR into a native, fully-editable Risograph-look .pptx (plus per-slide preview PNGs) via the Python ppt_engine. Returns the output path and a structural self-check (layout overflow/overlap issues).',
  inputSchema: z.object({
    deck: DeckSchema,
    out: z.string().default('deck.pptx').describe('output .pptx path (absolute, or relative to repo root)'),
    shots: z.string().nullish().describe('directory for per-slide preview PNGs'),
  }),
  outputSchema: z.object({
    ok: z.boolean(),
    out: z.string().optional(),
    slides: z.number().optional(),
    prims: z.number().optional(),
    issues: z.array(z.object({ slide: z.number(), type: z.string(), detail: z.string() })).optional(),
    stage: z.string().optional(),
    error: z.string().optional(),
  }),
  execute: async (inputData) => {
    const { deck, out, shots } = inputData;
    return await buildPptx(deck, out, shots ?? null);
  },
});
