---
name: stompgama
description: 当用户要求把 OC 角色做成 STOMPGAME（ikkimikka.net/stompgame）的自定义角色图并直接开始游戏时应使用本技能，例如"帮我用 github 上的 FEFKNCQ 制作我的 OC 角色并进行大脚踩踏游戏"、"用手拍"或"用手掌做踩踏图"（仓库原名 stompgama）。本技能把用户提供的头像/脚/全身图/手转成符合官方 1024×1024 精灵表坐标的 custom.png 与 custom.zip，提供逐格生图提示词、合成与校验脚本，并指导自动上传到游戏页面；它保证生成图导入即可用，画面相似度由后续迭代决定。
---

# STOMPGAME OC 自定义角色图生成与导入

> 仓库地址：https://github.com/ikkimikka/FEFKNCQ（原名 `stompgama`，已更名；
> skill 内部标识 `stompgama` 保持不变，旧说法与新说法都能触发本技能）。

## 目标与边界

把用户 OC 的参考图变成一张 **1024×1024 RGBA PNG**，其切片位置与官方 `generic.png`
完全一致；同时产出可直接上传的 **ZIP**（图片 + `settings.json`），使游戏
`?character=custom` 页面上传后立即可玩。

- 保证：尺寸、坐标、透明度、UI 装饰像素不被破坏、帧间无突变、`validate.py` 无 FAIL、可导入。
- 不保证：AI 画得像不像 OC。画面质量由用户与 agent 后续逐格迭代。
- 绝不让图像模型一次生成整张精灵表；逐格生成，脚本合成。
- 游戏只按坐标切片、不识别语义：用户明确说"用手"时按手生成，不再限定为脚。

## 工作流

### 0. 前置准备

1. 取得官方底板 `generic.png`（不要在仓库里找，仓库不打包作者原图）：
   `curl -L -o generic.png https://ikkimikka.net/stompgame/generic.png`
2. 阅读 `references/layout.md`（坐标契约）与 `references/frame-semantics.md`（姿态与连贯性约束）。
3. 确认本机有 Python 3.8+；核心脚本只用标准库，无需 pip install。

### 1. 判定输入模式

按 `references/input-profiles.md` 判定 A（头像+脚）/ B（一张全身图）/ C（头像+一张手，
仍按脚生成）/ **D 手模式**（用户明确说"用手 / 手掌 / 手拍 / 不要脚"）。
整理 `oc_profile.md`，把角色固定特征写清楚，并记下 OC 名字（用于 ZIP 的 `giant.name`）。
**参考图若穿鞋/穿袜/戴手套，必须把鞋型或手套款式记为固定项，按鞋和手套画，不得改成光脚/裸手**
（见 `references/input-profiles.md`「鞋袜与手套」）。
**只有手部参考图不等于手模式**；模式 D 下 11 个爪格全部画真正的手（或同款手套），坐标与流程不变。

### 2. 生成首版（10 张，默认尝试并发）

1. 读取 `references/prompts.md` 与 `references/numbering.md`，只为 10 张必生格拼提示词：
   `front_0` / `front_2` / `front_3` / `front_5` / `back_0` / `normal_0` / `normal_1` /
   `excite_0` / `excite_1` / `endscreen`。
   **表情每列两档**：平静 `normal_0`（平静1）/`normal_1`（平静2），兴奋 `excite_0`
   （兴奋1）/`excite_1`（兴奋2）。`normal_1`/`excite_1` 先采用 `normal_5`/`excite_5`
   的高档设计占位，让 ego 0→1 立刻看到表情差；**兴奋脸不得照抄平静脸**，否则踩死小人时
   头像无反应。后期 `normal_2..5` 复用 `normal_1`、`excite_2..5` 复用 `excite_1`。
   **四张爪格必查**：`front_0` 要露完整脚底/肉垫（穿鞋/戴手套时露鞋底/手套掌面）、
   腿是实体填充并延伸到顶边；`front_3/5` **脚底朝下贴地、不露肉垫**，`front_5` 比 `front_3`
   更宽更扁；`back_0` 以 `front_0` 为参考图、同视角只缩小 10–15%、踩地不露肉垫，
   不得换成正面/俯视。
   **模式 D** 改用 `prompts.md` 的「手模式（D）专属描述替换」表，其余四条不变。
2. **默认尝试并发**把这 10 张提交给生图通道，以缩短等待时间。
3. **回退规则**：若通道不支持并发、报并发限制或并行结果串图，立即改为逐格串行；
   **其余流程一律不变**（不改合成、校验、导入步骤，不重新设计提示词，不新增分支）。
   **串行与补图时必须把同组已生成的基准帧作为参考图上传**（`front_3`←`front_0`、
   `front_5`←`front_3`、`back_0`←`front_0`、`normal_1`←`normal_0`、`excite_0`←`normal_0`、
   `excite_1`←`normal_0`），
   完整对照见 `references/prompts.md` 第 2 节；并发提交没有可用基准帧，各帧共用 OC 参考图。
4. 保存为 `frames/<cell>.png`；模型不支持透明时统一指定纯白/纯绿底，不要混用底色。
5. 需要编号对照图时运行
   `python scripts/make_numbered_map.py --base generic.png --out numbered_map.png`（本地产出，不入库）。

### 3. 合成（自动复用其余 16 格，产出 PNG + ZIP；调试产物在临时目录，最终交付加 --deliver 才复制到桌面）

```
python scripts/build_sheet.py --frames frames/ --base generic.png --bg auto --name "<OC 名字>"   # 调试：产物在临时目录
# 最终交付时加 --deliver，复制一份到桌面
```

脚本按 `scripts/layout.py:REUSE_MAP` 把未提供的格复制同组基准帧，report 标 `reused:<源格>`；
已存在的帧文件优先使用（标 `generated`）。读取 `custom.report.json` 确认 26 格全部填充、
`must_generate` 的 10 张齐全。**首版允许复用，不要因为 `reused` 去补画**。

**爪格贴底对齐（必做）**：`build_sheet.py` 对 `front_*` / `back_*` 先裁掉透明边再**底对齐**
贴入，保证脚掌（手模式为手掌）最底部紧贴格子底边。游戏把爪格底边当作落脚点、
碰撞判定不看图片内容，格底留白会导致"脚还悬在空中、小黑人却已被踩死"。
表情格与结算横幅仍居中。若用户只拿来一张已生成的旧 `custom.png`，按
`scripts/layout.py:CELLS` 切出各格再重新合成即可修正，**不需要重新生图**。

**调试阶段默认把产物生成到系统临时目录**（`tempfile.gettempdir()/stomp_output/`），不在桌面堆积；
文件名自动带角色名（`--name`）与生成时间戳（如 `<名字>_custom_20261111_120000.png` 与同名 `.zip`），
路径在 report 的 `out` 字段。（ZIP 根目录含图片与 `settings.json`，`images.giant` 自动指向
ZIP 内图片名，`--name` 写入 `giant.name`，模板带评级与贴纸）。**只在最终交付时**加 `--deliver`，
脚本才额外复制一份到桌面（report 的 `desktop_copy` / `desktop_zip`，带角色名 + 时间戳、不覆盖旧产物）；
能联网的 agent 直接上传最终 ZIP 即可。

- 调试 / 中间产物 → 不加 `--deliver`，产物在临时目录，桌面保持干净。
- 最终交付给用户留底 → 加 `--deliver`（或 `--out <桌面路径>`），复制一份到桌面。
- 用户**明确要求放在别处** → 传 `--out <路径>`（不加 `--deliver` 就不会有桌面副本）。
- 只要 PNG、不要 ZIP → 传 `--no-zip`。
- 要改评级/贴纸/描述 → 复制 `assets/settings.template.json` 改好后传 `--settings my.json`；
  可设字段、合并/替换语义与禁止改的坐标见 `references/import.md`。
- 想保留官方默认贴纸 → 传 `--keep-default-stickers`（默认模板的 `stickers: []` 会清空它们）。
- 交付时**把本次 ZIP 实际改了哪些设定列给用户**，让他选 PNG / ZIP 时知道差异；
  `custom.report.json` 里 settings 校验产生的 WARN 也要一并说明。
- 桌面找不到（沙箱 / 特殊重定向）→ 仅在 `--deliver` 时打印 WARN，用 `--desktop-dir <路径>` 或
  环境变量 `STOMP_DESKTOP_DIR` 指定桌面目录。

### 4. 校验

```
python scripts/validate.py --sheet custom.png --base generic.png --report custom.report.json
```

逐项检查 `references/frame-semantics.md` 末尾的自检清单。任何 FAIL 必须修复：
`cutout:*` / `plate:*`（未去背白块）、`continuity:*`（面积/质心突变）、`chrome:*`（UI 装饰被改）、
`ground:*`（爪格底部留白）、`leg:*`（只有描边的空心腿）、
`expression:kill-ego`（兴奋帧等于平静脸）都会判 FAIL。
`top:*`（腿没到顶边）、`pose:*`（三张必生爪帧几乎同姿态）、`pressure:*`（压扁反而变小）、
`back:*`（前后爪不同源）、`expression:normal-reuse`（`normal_0`/`normal_1` 相同）、
`expression:fast-pass`（后期复用损失）是 WARN：前四条要修到消失或向用户说明；
**`expression:fast-pass` 是首版预期 WARN，交付说明里主动告知「表情只做两档、中期占位、
后期复用第二档」**。
程序只能发现几何与统计异常，不能判定解剖合理性，C1/C2/C5/C10 必须人工或 AI 目检。

### 5. 导入并开始游戏

按 `references/import.md`：**有浏览器能力的 agent 默认直接上传 `custom.zip` 并开始游戏**，
用户无需手动找文件；因为 ZIP 的 `settings.json` 能设置角色名、描述、评级与贴纸。
打开 `?character=custom` → 等待 `#upload` → 填入 `custom.zip` → 等待游戏重启
→ 点击画布开始 → 保持窗口。参考实现 `python scripts/import_game.py`（`--image` 默认即 ZIP）。
**不要默认上传 PNG**：PNG 会关闭评级、角色名只能取文件名，仅作为用户手动选择的备选。
导入后按验收清单确认爪、头像 HUD、爪影、结算横幅、角色名与评级都正常。

**不要用 `?character=custom` 作为"直接开玩"的链接**：该模式在未上传时隐藏爪与头像。

### 6. 跑通后主动询问是否补细节

一旦用户已经能玩，**必须主动提问**："首版生成了 10 张图、其余 16 格复用基准帧，
是否需要补画更多细节？" 并按 `references/prompts.md` 第 9 节的优先级给出候选：
优先把 `normal_1`/`excite_1` 的中度表情补上、并将当前占位版移回 `normal_5`/`excite_5`；
其次是中间档 `normal_2..4`/`excite_2..4`、抬爪中间帧、后爪压力帧、疲惫两帧。
用户提出再加即可。
用户未确认前不要自行追加生成，避免增加等待时间。

### 7. 补细节 / 局部迭代

用户确认补细节或提出"表情再凶一点"时，只把受影响的 `<cell>.png` 放进 `frames/`
（或重新生成这几张），重新执行第 3–5 步。`build_sheet.py` 会自动用新文件覆盖该格的复用，
并重新生成 PNG 与 ZIP，**无需改配置、无需整组重抽**。

## 资源索引

| 文件 | 用途 |
|---|---|
| `references/layout.md` | 唯一坐标契约、切片算法、屏幕位置、URL 参数 |
| `references/frame-semantics.md` | 26 格姿态/表情语义、C1–C11 约束、手模式、复用白名单、自检清单 |
| `references/numbering.md` | 34 个格位的编号、出现时机与频率对照 |
| `references/input-profiles.md` | A/B/C/D 四种素材模式、鞋袜/手套规则与降级 |
| `references/prompts.md` | 首版 9 格提示词、手模式词替换、复用映射、并发/回退、补细节优先级 |
| `references/import.md` | ZIP 默认自动上传、桌面双产物、settings.json 全字段与禁令、验收清单、故障排查 |
| `references/upstream.md` | 底板来源、SHA256、合规、版本漂移处理 |
| `scripts/build_sheet.py` | 合成、复用未生成格、生成 PNG+ZIP；默认产物在临时目录，加 --deliver 才复制桌面 |
| `scripts/validate.py` | 尺寸/装饰/去背/白板/贴底/实体腿/姿态/平静与击杀表情/帧间突变校验 |
| `scripts/import_game.py` | Playwright 自动上传参考实现（默认上传 ZIP） |
| `scripts/make_numbered_map.py` | 生成带编号的标注图（本地产出） |
| `scripts/layout.py` / `scripts/png.py` | 坐标常量、必生/复用/编号表与零依赖 PNG 读写 |
| `assets/settings.template.json` | ZIP 内 settings.json 模板（角色名/描述/评级/贴纸） |

## 硬性禁令

- 不修改 `DECOR` 区域的任何像素，不填 `BLANK_CELLS`。
- 不在 `settings.json` 里改任何 `*_spr` 坐标、`ego.levels`、`paw.width`、
  `paw.stomp_masks` 或 `ego_tiers` 长度：它们与 26 格切片契约绑定，改了整张图会错位。
- 不写半份 `sound_urls`（整体替换字段，省略该键才用默认音效）；`grades` 保持 ≤5 条，
  名字/描述/台词用短英文（`VT323` 等宽字体，中文会溢出）。
- 不把白底/不透明方块直接贴进角色格。
- 不一次生成整张 1024×1024 精灵表。
- 不让爪格底部留透明空隙（C11）：提示词要求贴底边，脚本裁剪+底对齐，`ground:*` 拦截。
- 不画空心/只有描边的腿（C9）：腿与手臂必须实体填充并延伸到格顶，`leg:*` 判 FAIL。
- 不把穿鞋/穿袜/戴手套的参考图改成光脚/裸手（C1）：11 格必须同款、不得脱掉或换款；
  "露脚底"改为露鞋底/手套掌面，趾数/掌纹只在裸露时才是固定项。
- 不让肉垫/掌垫在贴地帧出现（C12）：`front_3/4/5` 与 `back_*` 脚底朝下贴地，
  只能画脚背/脚侧/脚跟；肉垫只在抬起帧 `front_0/1/2` 可见。
- 不把后爪画成另一个视角或另一只形状的脚（C5）：以 `front_0` 为参考图、同趾序、
  只缩小 10–15%，`back:*` 会拦截。
- **用户明确说用手时不得强制画脚**；仅提供手部参考图（模式 C）时仍不得把手掌当脚的解剖依据。
- 首版生成 10 张必生格（含击杀 2 张：`excite_0`/`excite_1`）；并发失败时只回退串行，**不改动其余流程**。
- 调试产物默认落在系统临时目录（不在桌面堆积）；最终交付加 `--deliver` 才复制一份到桌面（文件名带角色名 + 时间戳，不覆盖旧产物）。
- 有浏览器能力的 agent **默认上传 ZIP**，不默认上传 PNG。
- 用户能玩之后必须主动询问是否补细节，未确认前不自行加图。
- 不把标注图、PNG 成品、ZIP 或任何含上游像素的文件提交进仓库。
- 不在 `?giant=` / `?json=` 直达链接里带 `character=custom`。
- 不打包或再分发作者原图；只引用官方下载地址。
- 不修改游戏网站本身，只使用公开 URL 参数与官方上传控件。
