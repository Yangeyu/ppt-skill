/**
 * The beauty-market test brief. Raw source material only — the agent decides the
 * archetypes and flow. Numbers are provided so the deck is factual, not invented.
 */
export interface Brief {
  id: string;
  out: string;
  shots: string;
  prompt: string;
}

export const beautyBrief: Brief = {
  id: 'beauty',
  out: 'out/beauty_riso_ai/deck.pptx',
  shots: 'out/beauty_riso_ai/shots',
  prompt: `请基于以下素材，设计一份 12-14 页的 riso 风格趋势洞察演示。

# 选题
《2026 中国美妆市场趋势洞察》—— 以上海为标杆城市。

# 受众与目标
受众：美妆品牌市场负责人、渠道与投资决策者。
目标：讲清"从流量驱动到信任驱动"的结构性转变，并把趋势落成可执行动作。

# 核心叙事线
主流量红利见顶，增长逻辑正从「流量驱动」切换到「信任驱动」：功效可验证、成分透明、AI 测肤适配、情绪价值、银发与男士等新客群、线下体验店成为高转化触点。

# 可用数据素材（只能用这些数字，可挑选，不要新编造）
- Z 世代贡献线上美妆 GMV 42%（同比 +7pp）
- 68% 消费者愿为"可验证功效"支付溢价（+12pp）
- 决策前人均品牌触点 3.2 个（+0.9）
- 51% 高端线购买受 ESG 因素影响（+15pp）
- 精华修护品类增速 +26%；防晒 +21%；香氛 +19%；男士护理 +17%；彩妆 +12%
- 线下体验店在触点权重中仅排第 4，但转化效率全渠道最高（1:4.7）
- 决策旅程触点权重：小红书 32 / 抖音 28 / 品牌私域 18 / 线下体验店 15 / 跨境电商 7

# 六股人群风向（适合 icon_grid）
Z 世代主力、银发新客、成分党、情绪美容、敏感肌经济、男士进阶——各配一句锐利洞察。

# 演进时间线（适合 timeline，2020→2026）
2020 直播爆发 / 2022 成分党崛起 / 2023 情绪护肤 / 2025 AI 测肤进店 / 2026 智美共生。

# 购买动因对照（适合 comparison，2024 vs 2026）
2024：KOL 推荐、包装设计、促销力度、品牌知名度。
2026：实验室级功效披露、AI 肤质适配、门店即时检测、成分溯源可视化。

# 三大美妆商圈（适合 pillars）
南京西路(首店经济)、淮海路(策展式零售)、前滩(家庭客群)。

# 线上/线下打法（适合 two_col）
线上：内容即货架、私域承接复购、AI 试妆降决策成本。
线下：门店=检测+体验场、即时反馈驱动转化、快闪制造稀缺。

# 品类风向标（适合 table）
列：品类 / 增速 / 关键词 / 热度。覆盖精华修护、防晒、香氛、彩妆、男士护理。

# 收束
金句一条点题「信任」；结尾行动号召，落款 Shanghai Beauty Lab · 2026。

# 风格
封面 hero 用 art="city"（正合上海）；中英双语，英文大写做 mono kicker；数据前置；版式多样、节奏起伏。`,
};

export const BRIEFS: Record<string, Brief> = {
  beauty: beautyBrief,
};
