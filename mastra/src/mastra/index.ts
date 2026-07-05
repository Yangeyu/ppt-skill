/**
 * Mastra instance — registers the deck-architect agent (and, through it, the
 * build-riso-pptx tool). Import `deckArchitect` directly for scripts, or use
 * `mastra.getAgent('deckArchitect')` / `mastra dev`.
 */
import { Mastra } from '@mastra/core';
import { deckArchitect } from './agents/deck-architect.js';
import { buildPptxTool } from './tools/build-pptx.js';

export const mastra = new Mastra({
  agents: { deckArchitect },
});

export { deckArchitect, buildPptxTool };
export { buildPptx } from './run-python.js';
export { DeckSchema } from './schema.js';
export type { Deck } from './schema.js';
