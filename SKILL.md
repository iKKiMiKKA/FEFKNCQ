---
name: stompgama
description: 当用户要求把 OC 角色做成 STOMPGAME（ikkimikka.net/stompgame）的自定义角色图并直接开始游戏时应使用本技能，例如"帮我用 github 上的 FEFKNCQ 制作我的 OC 角色并进行大脚踩踏游戏"（仓库原名 stompgama）。本技能把用户提供的头像/脚/全身图转成符合官方 1024×1024 精灵表坐标的 custom.png，提供逐格生图提示词、合成与校验脚本，并指导自动上传到游戏页面；它保证生成图导入即可用，画面相似度由后续迭代决定。
---

# STOMPGAME OC 自定义角色图生成与导入

> 仓库地址：https://github.com/ikkimikka/FEFKNCQ（原名 `stompgama`，已更名；
> skill 内部标识 `stompgama` 保持不变，旧说法与新说法都能触发本技能）。

## 目标与边界

把用户 OC 的参考图变成一张 **1024×1024 RGBA PNG**，其切片位置与官方 `generic.png`
完全一致，使游戏 `?character=custom` 页面上传后立即可玩。

- 保证：尺寸、坐标、透明度、UI 装饰像素不被破坏、帧间无突变、`validate.py` 无 FAIL、可导入。
- 不保证：AI 画得像不像 OC。画面质量由用户与 agent 后续逐格迭代。
- 绝不让图像模型一次生成整张精灵表；逐格生成，脚本合成。

## 工作流

### 0. 前置准备

1. 取得官方底板 `generic.png`（不要在仓库里找，仓库不打包作者原图）：
   `curl -L -o generic.png https://ikkimikka.net/stompgame/generic.png`
2. 阅读 `references/layout.md`（坐标契约）与 `references/frame-semantics.md`（姿态与连贯性约束）。
3. 确认本机有 Python 3.8+；核心脚本只用标准库，无需 pip install。

### 1. 判定输入模式

按 `references/input-profiles.md` 判定 A（头像+脚）/ B（一张全身图）/ C（头像+一张手）。
整理 `oc_profile.md`，把角色固定特征写清楚。模式 C 严格遵守"手不能当脚"的规则。

### 2. 生成首版（只 8 张，默认尝试并发）

1. 读取 `references/prompts.md` 与 `references/numbering.md`，只为 8 张必生格拼提示词：
   `front_0` / `front_3` / `front_5` / `back_0` / `normal_1` / `normal_3` / `normal_5` / `endscreen`。
   **表情三档跨度要大**（低 / 中 / 高 ego 的情绪差异明显可见）。
2. **默认尝试并发**把这 8 张提交给生图通道，以缩短等待时间。
3. **回退规则**：若通道不支持并发、报并发限制或并行结果串图，立即改为逐格串行；
   **其余流程一律不变**（不改合成、校验、导入步骤，不重新设计提示词，不新增分支）。
4. 保存为 `frames/<cell>.png`；模型不支持透明时统一指定纯白/纯绿底，不要混用底色。
5. 需要编号对照图时运行
   `python scripts/make_numbered_map.py --base generic.png --out numbered_map.png`（本地产出，不入库）。

### 3. 合成（自动复用其余 18 格）

```
python scripts/build_sheet.py --frames frames/ --base generic.png --out custom.png --bg auto
```

脚本按 `scripts/layout.py:REUSE_MAP` 把未提供的格复制同组基准帧，report 标 `reused:<源格>`；
已存在的帧文件优先使用（标 `generated`）。读取 `custom.report.json` 确认 26 格全部填充、
`must_generate` 的 8 张齐全。**首版允许复用，不要因为 `reused` 去补画**。

### 4. 校验

```
python scripts/validate.py --sheet custom.png --base generic.png --report custom.report.json
```

逐项检查 `references/frame-semantics.md` 末尾的自检清单。任何 FAIL 必须修复：
`cutout:*`（未去背白块）、`continuity:*`（面积/质心突变）、`chrome:*`（UI 装饰被改）都会判 FAIL。
WARN 仍需逐条目检。程序只能发现突变，不能判定解剖合理性，C1/C2/C5/C10 必须人工或 AI 目检。

### 5. 导入并开始游戏

按 `references/import.md`：打开 `?character=custom` → 等待 `#upload` → 填入 `custom.png`
→ 等待游戏重启 → 点击画布开始 → 保持窗口。可用 `scripts/import_game.py` 作参考实现。
导入后按验收清单确认爪、头像 HUD、爪影、结算横幅都正常。

**不要用 `?character=custom` 作为"直接开玩"的链接**：该模式在未上传时隐藏爪与头像。

### 6. 跑通后主动询问是否补细节

一旦用户已经能玩，**必须主动提问**："首版只生成了 8 张图、其余 18 格复用基准帧，
是否需要补画更多细节？" 并按 `references/prompts.md` 第 9 节的优先级给出候选：
兴奋表情、疲惫两帧、抬爪中间帧、后爪压力帧、表情过渡帧、完整兴奋列。
用户未确认前不要自行追加生成，避免增加等待时间。

### 7. 补细节 / 局部迭代

用户确认补细节或提出"表情再凶一点"时，只把受影响的 `<cell>.png` 放进 `frames/`
（或重新生成这几张），重新执行第 3–5 步。`build_sheet.py` 会自动用新文件覆盖该格的复用，
**无需改配置、无需整组重抽**，避免破坏已确认的连贯性。

## 资源索引

| 文件 | 用途 |
|---|---|
| `references/layout.md` | 唯一坐标契约、切片算法、屏幕位置、URL 参数 |
| `references/frame-semantics.md` | 26 格姿态/表情语义、C1–C10 连贯性约束、复用白名单、自检清单 |
| `references/numbering.md` | 34 个格位的编号、出现时机与频率对照 |
| `references/input-profiles.md` | 三种素材模式的容错与降级 |
| `references/prompts.md` | 首版 8 格提示词、复用映射、并发/回退、补细节优先级 |
| `references/import.md` | 自动上传步骤、ZIP/直达链接备选、故障排查 |
| `references/upstream.md` | 底板来源、SHA256、合规、版本漂移处理 |
| `scripts/build_sheet.py` | 按坐标合成并自动复用未生成格 |
| `scripts/validate.py` | 尺寸/装饰/去背/帧间突变校验 |
| `scripts/import_game.py` | Playwright 自动上传参考实现 |
| `scripts/make_numbered_map.py` | 生成带编号的标注图（本地产出） |
| `scripts/layout.py` / `scripts/png.py` | 坐标常量、必生/复用/编号表与零依赖 PNG 读写 |
| `assets/settings.template.json` | ZIP 全定制模板 |

## 硬性禁令

- 不修改 `DECOR` 区域的任何像素，不填 `BLANK_CELLS`。
- 不把白底/不透明方块直接贴进角色格。
- 不一次生成整张 1024×1024 精灵表。
- 首版只生成 8 张必生格；并发失败时只回退串行，**不改动其余流程**。
- 用户能玩之后必须主动询问是否补细节，未确认前不自行加图。
- 不把标注图或任何含上游像素的图片提交进仓库；只提交生成脚本与编号表。
- 不在 `?giant=` / `?json=` 直达链接里带 `character=custom`。
- 不打包或再分发作者原图；只引用官方下载地址。
- 不修改游戏网站本身，只使用公开 URL 参数与官方上传控件。
