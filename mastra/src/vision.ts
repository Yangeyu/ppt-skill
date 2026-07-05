/**
 * 识图 CLI —— 用 qwen3.7-plus 对一张幻灯片截图做美学评审。
 *
 * 用法：
 *   pnpm vision                          # 默认评审 ../out_v03/slide_01_custom.png
 *   pnpm vision <图片路径或URL> [意图说明]
 *
 * 本地图片会被读成 base64 data URL 直接喂给多模态模型；http(s) URL 则原样传入。
 */
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { visionCritic } from "./mastra/agents/vision-critic";

const MIME: Record<string, string> = {
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  webp: "image/webp",
  gif: "image/gif",
};

async function toImagePart(src: string): Promise<{ image: string; mimeType: string }> {
  if (/^https?:\/\//i.test(src)) {
    return { image: src, mimeType: "image/jpeg" };
  }
  const abs = resolve(process.cwd(), src);
  const ext = abs.split(".").pop()?.toLowerCase() ?? "png";
  const mimeType = MIME[ext] ?? "image/png";
  const buf = await readFile(abs);
  return { image: `data:${mimeType};base64,${buf.toString("base64")}`, mimeType };
}

async function main() {
  const src = process.argv[2] ?? "../out_v03/slide_01_custom.png";
  const intent = process.argv[3] ?? "这是一份 zine 文化指南的封面页";

  const part = await toImagePart(src);
  console.log(`识图中：${src}`);
  console.log(`意图：${intent}\n`);

  const res = await visionCritic.generate([
    {
      role: "user",
      content: [
        { type: "image", image: part.image, mimeType: part.mimeType },
        { type: "text", text: `这一页的意图：${intent}。请给出美学评审。` },
      ],
    },
  ]);

  console.log("── 模型返回 ──");
  console.log(res.text);

  try {
    const json = JSON.parse(res.text.replace(/```json|```/g, "").trim());
    const dims = ["hierarchy", "balance", "design", "boldness", "fit"] as const;
    const avg = dims.reduce((s, k) => s + (Number(json[k]) || 0), 0) / dims.length;
    console.log("\n── 评分卡 ──");
    for (const k of dims) console.log(`  ${k.padEnd(10)} ${json[k]}`);
    console.log(`  ${"平均".padEnd(10)} ${avg.toFixed(2)}`);
    console.log(`  建议：${json.suggestion}`);
  } catch {
    console.log("\n(未能解析为 JSON，以上为原始文本)");
  }
}

main().catch((e) => {
  console.error("识图失败：", e);
  process.exit(1);
});
