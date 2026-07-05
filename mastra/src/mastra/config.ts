/**
 * 全局模型配置。
 *
 * 走 Mastra 的 model router 字符串形式 `provider/model`：
 *  - provider `alibaba-cn` → DashScope 兼容端点，自动读取环境变量 DASHSCOPE_API_KEY
 *  - qwen3.7-plus 本身支持多模态，识图直接用它，无需单独的 vision 模型
 */
export const QWEN_MODEL = "alibaba-cn/qwen3.7-plus" as const;
