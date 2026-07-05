import { Mastra } from "@mastra/core/mastra";
import { PinoLogger } from "@mastra/loggers";

import { visionCritic } from "./agents/vision-critic";
import { artDirector } from "./agents/art-director";
import { deckGenerator } from "./agents/deck-generator";

/**
 * Mastra 实例：注册本项目的 agents。
 * `pnpm dev` 会启动 playground，可在浏览器里直接调这些 agent（含上传图片识图）。
 */
export const mastra = new Mastra({
  agents: { visionCritic, artDirector, deckGenerator },
  logger: new PinoLogger({ name: "ppt-mastra", level: "info" }),
});
