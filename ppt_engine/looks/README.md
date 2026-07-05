# Look 包库

参考 [ppt-master 的模板组织](https://github.com/hugohe3/ppt-master/blob/main/docs/templates-architecture.md)
(`templates/<kind>/<id>/` 自包含目录包 + 分段管理 + 发现索引)落地到本引擎。

## 一个 look 包 = 一个子目录,三个分段

| 分段 | 载体 | 对应 ppt-master |
|---|---|---|
| **身份段** | `__init__.py` 里的 `SpecLock`(色板/字体/字阶/图像处理令牌) | brand / Identity segment |
| **结构段** | `templates/*.j2`(该 look 的版式库;缺的原型回落共享 `templates/`) | layout / Structure segment |
| **图像段** | `Look` 上的三个钩子:`image_style_suffix`(t2i 风格纪律)、`image_postprocess`(任意源图再上墨)、`image_fallback`(离线程序化兜底) | image_prompts 的工程化强版 |

设计规格文档随包放(`spec.md`,frontmatter 同 ppt-master 的 `design_spec.md`)。

## 契约

- 引擎不特判任何 look,只消费 `LOOKS` 注册表;**新增 look = 新建子目录 + `LOOK` 常量,零引擎改动**。
- 身份段必须过身份评论官(`critique_identity` 零 error)。角色字体 ≤2 族
  (`display_font`/`body_font`);中西配对的附加字面走 `embed_families`,不占角色数。
- 结构段模板只引用令牌变量(`var(--*)` / `colors[...]`)。用到扩展词汇
  (blue/pink/mustard/paper-2/on-paper-muted)没关系——`SpecLock.render_colors()`
  会为任何身份(seed / artdirect 现场生成)补齐别名,**身份可换、结构统一**。
- 带 CSS background 的元素必须挂 `data-ppt="rect"`,否则导出丢底色;
  巨号标题用 `white-space: nowrap`(measure→render 贯通,不静默折行)。

## 与 freedom(v0.3 现场生成身份)的关系

look 是**预置的已验证设计语言**(seed);artdirect 现场生成的 `SpecLock` 是
freedom。两者都渲染进同一结构库(`get_look()`:有包身份用包的版式,无包身份
用 `DEFAULT_LOOK` 的版式)——对应 ppt-master 的 deck(身份+结构一体) vs
brand×layout(自由融合)。

## 当前成员

- **riso** —— Risograph zine(默认)。见 `riso/spec.md`。
- **swiss** —— 瑞士国际主义(IKB 单锚点+细字重+发丝线)。见 `swiss/spec.md`。
- **morandi** —— 莫兰迪简约(暖纸+灰蓝+五色轮换+干笔刷肌理)。见 `morandi/spec.md`。
