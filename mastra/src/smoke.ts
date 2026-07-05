/**
 * Connectivity smoke test: verify alibaba-cn/qwen3.7-plus + DASHSCOPE_API_KEY +
 * Mastra structuredOutput all work, on a tiny schema — before spending tokens on
 * the full deck.  Run:  npm run smoke
 */
import 'dotenv/config';
import { z } from 'zod';
import { deckArchitect, MODEL_ID } from './mastra/agents/deck-architect.js';

async function main() {
  console.error(`[smoke] model=${MODEL_ID}  DASHSCOPE_API_KEY set: ${!!process.env.DASHSCOPE_API_KEY}`);
  const t0 = Date.now();
  const res = await deckArchitect.generate('用一句中文金句概括「美妆消费从流量转向信任」，并给出出处署名。', {
    structuredOutput: {
      schema: z.object({
        quote: z.string().describe('the punchy line'),
        attribution: z.string().describe('who/what it is attributed to'),
      }),
    },
  });
  console.error(`[smoke] ok in ${Date.now() - t0}ms`);
  console.log(JSON.stringify(res.object, null, 2));
}

main().catch((e) => {
  console.error('[smoke] FAILED:', e?.message || e);
  process.exit(1);
});
