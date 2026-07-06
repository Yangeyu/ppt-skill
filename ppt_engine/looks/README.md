# Look 包库 —— 本引擎的模板库

参考 [ppt-master 的模板组织](https://github.com/hugohe3/ppt-master/blob/main/docs/templates-architecture.md)
(`templates/<kind>/<id>/` 自包含目录包 + 分段管理 + 发现索引)落地到本引擎。
我们叫 **look** 而不叫 template,因为它比版式多三段:叙事哲学、设计语言与图像纪律
——**一个 look 是一种报告,不只是一种配色**。

## 一个 look 包 = 一个子目录,四个分段

| 分段 | 载体 | 对应 ppt-master |
|---|---|---|
| **身份段** | `__init__.py` 里的 `SpecLock`(色板/字体/字阶/图像处理令牌) | brand / Identity segment |
| **结构段** | `templates/*.j2`(该 look 的版式库;缺的原型回落 `_shared/`) | layout / Structure segment |
| **图像段** | `Look` 上的三个钩子:`image_style_suffix`(t2i 风格纪律)、`image_postprocess`(任意源图再上墨)、`image_fallback`(离线程序化兜底) | image_prompts 的工程化强版 |
| **引导段** | `guidance.md`(叙事声音/deck 弧线/版式路由/数据表现纪律),由 `contract.py` 拼进生成契约;选型与密度纪律在 `LOOK` 常量的 `pick_when`/`density` 字段 | SKILL.md 的工艺段 |

设计规格文档随包放(`spec.md`,frontmatter 同 ppt-master 的 `design_spec.md`)。

## 契约

- 引擎不特判任何 look,只消费 `LOOKS` 注册表;**新增 look = 新建子目录 + `LOOK` 常量,零引擎改动**
  (密度配额也在 `LOOK.density` 里,`critic/density.py` 只是消费者)。
- 身份段必须过身份评论官(`critic/identity.py`,零 error——`tests/test_floor.py`
  对全部注册 look 断言,这是 look 作者的门禁)。角色字体 ≤2 族
  (`display_font`/`body_font`);中西配对的附加字面走 `embed_families`,不占角色数。
- 结构段模板只引用令牌变量(`var(--*)` / `colors[...]`)。用到扩展词汇
  (blue/pink/mustard/paper-2/on-paper-muted)没关系——`SpecLock.render_colors()`
  会为任何身份补齐别名,**身份可换、结构统一**。
- 带 CSS background 的元素必须挂 `data-ppt="rect"`,否则导出丢底色;
  巨号标题用 `white-space: nowrap`(measure→render 贯通,不静默折行)。
- `_shared/` 放跨 look 公共原型(创作轨 `custom.html.j2` 等),无 `__init__.py`,
  不进注册表。

## 当前成员

- **crimson** —— 经典深红咨询风(SCR 结论句+exhibit 复合证据版面)。见 `crimson/spec.md`。
- **riso** —— Risograph zine(默认)。见 `riso/spec.md`。
- **swiss** —— 瑞士国际主义(IKB 单锚点+细字重+发丝线)。见 `swiss/spec.md`。
- **morandi** —— 莫兰迪简约(暖纸+灰蓝+五色轮换+干笔刷肌理)。见 `morandi/spec.md`。

## 未来:现场生成身份(freedom,docs/DESIGN.md 北极星)

若恢复「按主题现场生成设计语言」,正确形态是**艺术总监产出一个新的 look 包**
(SpecLock 过 `critic/identity.py` 门禁 + 复用或生成版式),而非绕过 look 包
渲染——版式已按 look 特化,杂交渲染破坏身份一致性。
