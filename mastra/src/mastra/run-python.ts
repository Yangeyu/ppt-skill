/**
 * Bridge to the Python engine. Writes the Deck IR to a temp JSON file and drives
 * `python3 -m ppt_engine.cli`, which validates + builds the native .pptx and
 * emits a single JSON result line on stdout (logs go to stderr).
 */
import { spawn, spawnSync } from 'node:child_process';
import { writeFile, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, dirname, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Deck } from './schema.js';

const HERE = dirname(fileURLToPath(import.meta.url)); // <repo>/mastra/src/mastra
export const REPO_ROOT = process.env.PPT_REPO_ROOT
  ? resolve(process.env.PPT_REPO_ROOT)
  : resolve(HERE, '../../..'); // -> <repo>
const PYTHON = process.env.PPT_PYTHON || 'python3';

export interface LayoutIssue {
  slide: number;
  type: string;
  detail: string;
}

export interface BuildResult {
  ok: boolean;
  out?: string;
  slides?: number;
  prims?: number;
  kinds?: string[];
  issues?: LayoutIssue[];
  shots?: string | null;
  stage?: string;
  error?: string;
  errors?: unknown;
}

function abs(p: string): string {
  return isAbsolute(p) ? p : resolve(REPO_ROOT, p);
}

/** A look's generator-facing contract, straight from the engine (single source). */
export interface LookInfo {
  ok: boolean;
  id: string;
  name: string;
  icons: string[];
  constraints: Record<string, unknown>;
  agent_instructions: string;
}

/** `python3 -m ppt_engine.cli --describe <id>` — icons / constraints / prompt fragment. */
export function describeLook(id = 'riso'): LookInfo {
  const r = spawnSync(PYTHON, ['-m', 'ppt_engine.cli', '--describe', id], {
    cwd: REPO_ROOT,
    env: process.env,
    encoding: 'utf-8',
  });
  if (r.error) throw new Error(`failed to start '${PYTHON}': ${r.error.message}`);
  const info = parseResult(r.stdout ?? '') as unknown as LookInfo | null;
  if (!info || !info.ok) {
    const detail = (info as { error?: string } | null)?.error ?? (r.stderr ?? '').slice(-400);
    throw new Error(`ppt_engine.cli --describe ${id} failed: ${detail}`);
  }
  return info;
}

/** Render a Deck to a native riso .pptx (+ optional preview PNGs). */
export async function buildPptx(deck: Deck, out: string, shots?: string | null): Promise<BuildResult> {
  const tmp = await mkdtemp(join(tmpdir(), 'riso-deck-'));
  const deckPath = join(tmp, 'deck.json');
  await writeFile(deckPath, JSON.stringify(deck), 'utf-8');

  const args = ['-m', 'ppt_engine.cli', '--deck', deckPath, '--out', abs(out)];
  const shotsPath = shots ? abs(shots) : null;
  if (shotsPath) args.push('--shots', shotsPath);

  return await new Promise<BuildResult>((done) => {
    const child = spawn(PYTHON, args, { cwd: REPO_ROOT, env: process.env });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => (stdout += d.toString()));
    child.stderr.on('data', (d) => {
      const s = d.toString();
      stderr += s;
      process.stderr.write(s); // stream engine progress live
    });
    child.on('error', (err) =>
      done({ ok: false, stage: 'spawn', error: `failed to start '${PYTHON}': ${err.message}` }),
    );
    child.on('close', (code) => {
      const result = parseResult(stdout);
      if (result) return done(result);
      done({
        ok: false,
        stage: 'bridge',
        error: `ppt_engine.cli exited ${code} with no parseable result.\n${stderr.slice(-800)}`,
      });
    });
  });
}

/** cli.py prints exactly one JSON result line to stdout; find it defensively. */
function parseResult(stdout: string): BuildResult | null {
  const lines = stdout
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('{'));
  for (let i = lines.length - 1; i >= 0; i--) {
    try {
      return JSON.parse(lines[i]) as BuildResult;
    } catch {
      /* keep scanning older lines */
    }
  }
  return null;
}
