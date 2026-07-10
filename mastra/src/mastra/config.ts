import { Agent as UndiciAgent, fetch as undiciFetch } from "undici";

/**
 * 全局模型配置。
 *
 * 走 Mastra 的 model router 字符串形式 `provider/model`：
 *  - provider `alibaba-cn` → DashScope 兼容端点，自动读取环境变量 DASHSCOPE_API_KEY
 *  - qwen3.7-plus 本身支持多模态，识图直接用它，无需单独的 vision 模型
 */
export const QWEN_MODEL = "alibaba-cn/qwen3.7-plus" as const;

/**
 * 传输层超时(消费端配置,与 skill 本体无关)。
 *
 * qwen3.7-plus 是推理模型:单发生成整份 deck IR(如 recommend-pages 给的 23 页)
 * 首包耗时可远超 undici 默认 headersTimeout(300s),必现
 * UND_ERR_HEADERS_TIMEOUT——skillgen 与 generate 都会撞。
 *
 * 实现取直接接管 globalThis.fetch(AI SDK 默认走它),而非 setGlobalDispatcher:
 * npm undici 的 setGlobalDispatcher 只写它自己的全局符号(.2),Node 内置 fetch
 * 读的是 .1(模块 import 时已被塞入 300s 默认 Agent)——两边不互通。已实证:
 * 对"响应头延迟 5s"的端点设 2s headersTimeout,setGlobalDispatcher 路径不超时
 * (默认值仍在生效),接管 fetch 路径正确超时。注意探针必须用秒级延迟端点,
 * undici 定时器是约 1s 粒度的 FastTimer,毫秒级探针会假阴性。
 * 本文件是所有 agent 的公共 import,进程级接管一次即全局生效。
 */
const longDispatcher = new UndiciAgent({
  headersTimeout: 30 * 60_000,   // 首包(响应头)等待:30min
  bodyTimeout: 30 * 60_000,      // 响应体间隔:30min
});
globalThis.fetch = ((input: any, init?: any) =>
  undiciFetch(input, { ...init, dispatcher: longDispatcher })) as typeof fetch;
