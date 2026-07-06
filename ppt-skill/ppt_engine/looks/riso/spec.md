---
look_id: riso
kind: look
summary: Risograph zine——纸感套色海报风,适合潮流文化/叙事/独立品牌主题
primary_color: "#1E4DBC"
canvas_format: ppt169
page_types: [hero, cover, toc, section, kpi, bullets, chart, two_col, comparison,
             process, icon_grid, timeline, table, pillars, quote, closing]
---

# Riso · 设计规格

对标 ppt-master `examples/ppt169_indie_bookstore_zine_guide`(spec_lock.md)。

## I. 身份(Identity)

- **色板**:暖纸 `#F5EFE0` / Federal Blue `#1E4DBC` / Fluo Pink `#FF5C8A` /
  Mustard `#E8A02E` / 近黑墨 `#1A1A1A`。蓝粉是两块"印版",芥末只做点缀。
- **字体**:显示层 Anton × 思源黑 Black(中西分字族,a:latin/a:ea 分别落字);
  注解层 Space Mono;正文思源黑。四族全部子集嵌入。
- **字阶**:1.5 比例;display 112 / h1 54 / h2 30 / body 20 / caption 15 / micro 12。
- **硬规则**:硬边无圆角;巨号标题单行不折(nowrap);强调色克制,大面积留纸色;
  双语 chrome(mono kicker / 页码芯片 / 页脚)拉密度。

## II. 结构(Structure)

16 个原型版式(见 frontmatter page_types),1280×720。hero 版式左 56% 为
scrim 文字区——**图像焦点内容必须在 x > 0.57w**,否则 scrim 边缘切出竖缝。

## III. 图像纪律(Imagery)

三层强制,颜色永不依赖模型自觉:

1. `STYLE_SUFFIX`:stencil 剪影 / flat print / 左 45% 留白 / 禁文字禁渐变;
2. `riso_ify()` 真·双版分色后处理:暗部→蓝版半调、中间调带通→粉版半调
   (偏移 −6,−6 = 套印错位)、高光留纸白;
3. 离线/失败兜底 `make_hero(art)`:程序化画作(sun/city/shanghai/vanity)。

t2i 模型 `qwen-image-2.0`,走 DashScope `multimodal-generation/generation`
端点(messages 格式);同 prompt 构图有波动属正常。
