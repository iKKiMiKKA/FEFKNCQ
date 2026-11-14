# FEFKNCQ

给 AI agent 用的 skill：把你的 OC 角色做成 [STOMPGAME](https://ikkimikka.net/stompgame/)
（`?character=custom`）能直接导入的自定义角色图 `custom.png`，同时产出可设置角色名、
描述与结算评级的 `custom.zip`，并自动开始游戏。

仓库：<https://github.com/ikkimikka/FEFKNCQ>

> 仓库原名 `stompgama`，2026-11-10 更名为 `FEFKNCQ`；旧地址会自动重定向。
> skill 内部标识仍为 `stompgama`（小写，符合 skill 命名规范），不影响触发。

## 一句话用法

把下面这句发给支持 skill / 能调用生图的 AI agent（豆包电脑版、百度搭子、workbuddy 等），
附上你的 OC 参考图即可：

```
帮我用 github 上的 FEFKNCQ 制作我的 OC 角色并进行大脚踩踏游戏
```

agent 会：判定素材模式 → **首版生成 10 张必生图**（`front_0` / `front_2` / `front_3` / `front_5` /
`back_0` / `normal_0` / `normal_1` / `excite_0` / `excite_1` /
`endscreen`）→ 其余 16 格由脚本自动复用同组基准帧 → 合成 1024×1024 `custom.png` 与
`custom.zip`（调试产物在临时目录，最终交付加 `--deliver` 才复制到桌面）→ 校验 → 有浏览器能力就**默认上传 `custom.zip`** 并点击开始。
ZIP 根目录的 `settings.json` 带角色名、描述、评级与贴纸；上传纯 PNG 会关闭评级、角色名只取文件名。
**表情每列两档**：平静 `normal_0`（平静1）/`normal_1`（平静2），兴奋 `excite_0`/`excite_1`，
后期复用第二档；`normal_1`/`excite_1` 先借用 F11/F12 的高档设计，后续再细化。
生成时**默认尝试并发**；通道不支持并发或结果串图时只回退为逐格串行，其余流程不变。

**想用手掌拍而不是脚踩？** 明确说"用手 / 用手掌 / 用手拍 / 不要脚"即可，
11 个爪格会全部生成真正的手；只发来一张手部参考图不算，仍按脚生成。

**主体是无后腿的单一椭圆下踩体（屁股、蛞蝓/史莱姆等）？** 后爪位置整组留空，只画前爪
作唯一的下踩主体：首版跳过 `back_0`（必生变 9 张），合成加 `--empty back`，后爪 5 格输出
透明且免报缺失。

**如果你没有指定图片放在哪里**，脚本默认把产物生成到系统临时目录（`tempfile.gettempdir()/stomp_output/`），
文件名自动带上角色名（`--name`）与生成时间戳（如 `<名字>_custom_20261111_120000.png` / `.zip`），桌面保持干净；
**只在最终交付时**加 `--deliver`，脚本才额外复制一份到桌面（带角色名 + 时间戳、不覆盖旧产物）。
若你明确要求放到别处且不要桌面副本，agent 会改用 `--out <路径>`（不加 `--deliver` 即无桌面副本）。

**跑通能玩后 agent 会主动询问是否补画更多细节**（后期表情升级、击杀兴奋反馈、
疲惫两帧、抬爪中间帧等），
用户确认前不会自行加图。补细节只需往 `frames/` 多放几张 `<帧名>.png` 重新合成，
单格文件会自动覆盖该格的复用，无需改配置。之后也可以直接说
"第 3 个表情再凶一点"之类的调整，agent 只重画对应格子。

### 你可以提供的素材（任意一种都行）

| 素材 | 说明 |
|---|---|
| 头像 + 脚 | 最佳，角色最还原 |
| 一张全身图 | 自动裁出头/脚作参考 |
| 头像 + 一张手的图（未说用手） | 手部图只借用线条/配色/饰物风格，脚的结构按官方示例推导 |
| 只给动漫/游戏角色名（无参考图） | 角色名模式：采用该 IP 最经典标志性形象，还原发型/脸/身材/服饰，详见 `references/input-profiles.md` 模式 E |
| 明确说"用手 / 手掌 / 手拍 / 不要脚" | 手模式：11 个爪格全部画真正的手，坐标与交付流程不变 |

> 参考图若穿鞋、穿袜或戴手套，一律**按鞋和手套画**，不会擅自改成光脚/裸手：
> 11 个爪格保持同款、不脱不换款，`front_0` 的"露脚底"改为露鞋底/手套掌面。

## 这个 skill 保证什么

- **保证**：坐标、尺寸、透明度、UI 装饰像素、帧间无突变、导入即可用。
- **能自动拦截**：脚底悬空、未去背白块、空心描边腿、必生爪帧姿态雷同、前后爪不同源、
  平静脸两档重复、兴奋帧等于平静帧、UI 装饰被改（`validate.py`）。
- **不保证**：AI 画得像不像 OC、脚底解剖是否正确、肉垫有没有在贴地帧露出来、是否真是同一只脚；
  这些仍需目检。
  首版生成 10 张、其余 16 格复用：表情每列两档（平静 1/2、兴奋 1/2），后期复用第二档；
  代价是中间档未细分、`normal_1`/`excite_1` 暂用高档设计占位，属已知取舍，用户提出再加图。

核心做法：不让图像模型一次画出整张精灵表，而是**逐格生成 + 脚本按坐标合成**，
并把官方 `generic.png` 的 UI 装饰像素原样保留。

## 快速开始（手动跑一遍）

```bash
# 1. 取官方底板（仓库不打包作者原图）
curl -L -o generic.png https://ikkimikka.net/stompgame/generic.png

# 2. 首版放 10 张图到 frames/（命名见 references/prompts.md）
#    front_0.png / front_2.png / front_3.png / front_5.png / back_0.png
#    normal_0.png / normal_1.png / excite_0.png / excite_1.png
#    endscreen.png
#    其余 16 格由 build_sheet.py 按 REUSE_MAP 自动复制，不必生成
#    （单主体/无后腿形态如屁股、蛞蝓：跳过 back_0，合成加 --empty back，后爪 5 格留空）

# 2b. 需要编号对照图时（含上游像素，仅本地查看，不要提交）
python scripts/make_numbered_map.py --base generic.png --out numbered_map.png

# 3. 合成 + 校验（默认产物在系统临时目录，最终交付加 --deliver 才复制到桌面，文件名带角色名/时间戳）
python scripts/build_sheet.py --frames frames/ --base generic.png --bg auto --name "MY OC"
python scripts/validate.py --sheet custom.png --base generic.png --report custom.report.json
#    调试产物默认在系统临时目录；加 --deliver 时路径见 custom.report.json 的 desktop_copy / desktop_zip

# 3b. 已指定保存位置、不想要桌面副本时（不要 --deliver）
python scripts/build_sheet.py --frames frames/ --base generic.png --bg auto --out D:/pic/my.png
# 3c. 只要 PNG、不要 ZIP：加 --no-zip
# 3d. 改角色名/评级/贴纸：复制 assets/settings.template.json 改好后传 --settings my.json
# 3e. 想保留官方默认贴纸：加 --keep-default-stickers（默认模板会清空它们）

# 4. 自动导入并开始（可选依赖，默认上传 custom.zip）
#    仅适合本机真实终端：脚本默认等待回车以保持窗口；agent 请用自带浏览器工具
pip install -r requirements-browser.txt
playwright install chromium
python scripts/import_game.py
```

也可以不装 Playwright：打开 <https://ikkimikka.net/stompgame/?character=custom>，
把桌面上的 `custom.zip`（或 `custom.png`）拖进上传框，再点击画布开始。
推荐 ZIP：会额外带上角色名、描述与结算评级。

## 目录

```
SKILL.md                        agent 主指令
references/layout.md            唯一坐标契约（1024×1024 全部切片）
references/frame-semantics.md   26 格姿态/表情语义 + 防动作突变约束
references/input-profiles.md    四种素材模式（含手模式）的容错与降级
references/numbering.md         34 个格位编号、出现时机与频率
references/prompts.md           首版 10 格提示词 + 复用映射 + 补细节优先级
references/import.md            自动导入、验收清单、故障排查
references/upstream.md          底板来源、SHA256、合规、版本漂移
scripts/layout.py               坐标常量 + MUST_GENERATE / REUSE_MAP / NUMBERED_CELLS
scripts/png.py                  零依赖 PNG 读写/去背/缩放/统计
scripts/build_sheet.py          合成、复用未生成格、生成 PNG+ZIP；默认产物在临时目录，加 --deliver 才复制桌面
scripts/validate.py             校验（装饰/去背/贴底/实体腿/姿态/前后爪/击杀表情/帧间突变）
scripts/import_game.py          Playwright 自动上传参考实现（默认上传 ZIP）
scripts/make_numbered_map.py    生成带编号的标注图（本地产出）
assets/settings.template.json   ZIP 全定制模板
```

## 依赖

- 核心脚本：Python 3.8+，**仅标准库**（无 Pillow / numpy）。
- **生图帧必须是 8-bit 非隔行 PNG**（RGBA/RGB/调色板均可）；16-bit、隔行、WebP/JPEG
  需先转换，否则 `build_sheet.py` 记 error、`validate.py` 判 FAIL。
- 浏览器自动上传：可选 `playwright>=1.44,<2`（见 `requirements-browser.txt`）。
  agent 若自带浏览器工具，可完全跳过。
- 在中文 Windows 上运行 skill-creator 的 `quick_validate.py` / `package_skill.py` 时，
  先设 `$env:PYTHONUTF8='1'`，否则脚本按 GBK 读取中文 `SKILL.md` 会报编码错误。

## 关键事实（踩过的坑）

- `?character=custom` 页面在**未上传**时会隐藏爪与头像，`intro_screen()` 直接返回；只有上传
  文件触发 `custom_loaded=true` 后才恢复。所以"打开链接直接玩"要用 `?giant=` / `?json=` 参数，
  不能带 `character=custom`。
- 切片算法：精灵数组第 7 项 `sp=3` 表示每列 3 帧、向下排满再向右换列。
  左侧 11 个爪格 = 前爪 6 帧 + 后爪 5 帧；右侧 14 个表情格 = 常态 6 + 兴奋 6 + 疲惫 2。
- 头像框、棋盘底、名字条、爪影点阵是 UI 装饰，必须原样保留；`validate.py` 逐像素比对。
- 编号是**图位顺序**，不是动画顺序：前爪为 `P01→P05→P09→P02→P06→P10`。
  `F09–F12`（高 ego）、`F13/F14`（疲惫）、`P08/P10`（高压）出现频率低，`X01–X03`
  默认永不采样——这是首版敢复用 16 格的依据，详见 `references/numbering.md`。
- 桌面副本仅在 `--deliver` 时由 `build_sheet.py` 用标准库探测：Windows 先问 shell API
  （兼容 OneDrive 重定向），其余平台依次尝试 `~/Desktop`、`~/桌面`、`~/OneDrive*/Desktop`；
  可用 `STOMP_DESKTOP_DIR` 或 `--desktop-dir` 覆盖。文件名含角色名 + 时间戳、不覆盖旧产物；
  路径分别记在 report 的 `desktop_copy` / `desktop_zip`；调试阶段（无 `--deliver`）产物在临时目录。
- **脚掌（手模式为手掌）必须贴格子底边**：游戏按爪格底边对齐 `paw_y`（碰撞只看 `paw_y`
  与 `floor_y=228`，不读图片内容），官方底板触地帧脚底留白为 0px。若脚底离格底约 50px，
  显示放大 2 倍后就是约 100px 的"悬空"，小人却已被判定踩死。`build_sheet.py` 会对爪格
  自动裁剪透明边并底对齐，`validate.py` 的 `ground:*` 会拦截超过 6px 的留白。
- **腿必须实体填充**：只画两条轮廓线的"空心腿"在游戏里会看成透明腿；提示词要求柱状实体
  并延伸到格顶，`validate.py` 的 `leg:*` 判 FAIL、`top:*` 检查腿是否到顶边。
- **表情走两条线**：ego 等级 = `floor(ego_climb/1000)`，`normal` 列是"无击杀时"按等级显示，
  `excite` 列只在**击杀得分后约 0.5 秒**闪现。首版每列做两档：平静 `normal_0`/`normal_1`、
  兴奋 `excite_0`/`excite_1`；`normal_1`/`excite_1` 先借用 `normal_5`/`excite_5` 的高档设计
  （占位），后续移回 F11/F12 并重生成中度表情。`validate.py` 的 `expression:normal-reuse`
  （`normal_0`/`normal_1` 相同）是 WARN，`expression:kill-ego`（兴奋帧等于平静脸）判 FAIL。
  后期 `normal_2..5` 复用 `normal_1`、`excite_2..5` 复用 `excite_1`，`tired_0/1` 也复用，
  属已知损失（`expression:fast-pass` WARN）；跑通后等用户提出，再按 `references/prompts.md`
  第 9 节补。
- **ZIP 才能带元数据**：包内 `settings.json` 必须在根目录，`images.giant` 指向包内图片名；
  上传 ZIP 会应用 `giant.name` / `description` / `grades` / `stickers`，上传 PNG 则
  `giant.grades=false`、名字取文件名（贴纸仍保留游戏默认）。
  `settings.json` 的 11 个顶层字段分两类：`sound_urls` / `stickers` / `demographics` /
  `ego_tiers` **写了就全量覆盖**，其余不写即用游戏默认；坐标类 `*_spr`、`ego.levels`、
  `paw.width` / `stomp_masks` 不要改，`build_sheet.py` 会对它们和 `grades` 结构打印 WARN。
  详见 `references/import.md`。
- **未去背的白底方块**会被 `validate.py` 的 `plate:*`（包围盒填充率）判 FAIL；
  合成保持 `--bg auto` 自动估色，必要时显式 `--bg white`。

## 合规

- 本项目为非官方第三方 skill，与游戏作者 ikkimikka 无关联。
- 仓库**不打包**作者的 `generic.png`，运行时从官方地址下载；出处与 SHA256 见
  `references/upstream.md`。
- **分发请用 GitHub 仓库 / zipball**：不要用 skill-creator 的 `package_skill.py` 直接打包
  当前工作目录，它会把 `.git/`、`__pycache__/` 以及含上游像素的本地标注图
  `numbered_map.png` 一起打进 zip。含像素产物（`custom.png`、`custom.zip`、标注图）一律
  不提交、输出到仓库外（`.gitignore` 已覆盖常见文件名）。
- OC 素材需由用户自行确认使用权；生成内容请遵守所用生图服务与上游站点条款。
- 游戏为"巨人踩踏小人"的卡通玩法，公开分享时请自行标注受众。
