# 导入游戏：ZIP 默认自动上传，桌面同时给 PNG 与 ZIP

## 交付物（build_sheet.py 默认产出）

| 文件 | 位置 | 用途 |
|---|---|---|
| `custom.png` | 与 `--out` 同目录 + **桌面副本** | 纯图片上传，用户手动选择时用 |
| `custom.zip` | 与 `--out` 同目录 + **桌面副本** | **默认上传对象**：内含图片与根目录 `settings.json` |

ZIP 内的 `settings.json` 来自 `assets/settings.template.json`（可用 `--settings` 换成自定义文件），
`images.giant` 自动指向 ZIP 内图片的文件名，`--name "<OC 名字>"` 会写入 `giant.name`。
模板还含 `giant.description`、`congrats`、`grades`（评级）、`stickers`；要改评级/贴纸时
复制一份 settings.json 用 `--settings` 传入。**不要把文件夹本身压进 ZIP，两个文件都在根。**

模板的 `"stickers": []` 会**清空**游戏默认贴纸（官方贴纸坐标按默认爪图设计，套到 OC 上
容易错位，默认清空更安全）；想保留官方默认贴纸就加 `--keep-default-stickers`，
脚本会省略该键。打包时脚本会校验 settings.json，危险改动写入 report 的 `warnings`。

桌面副本路径记在 `custom.report.json` 的 `desktop_copy`（PNG）与 `desktop_zip`（ZIP），
agent 应把两个路径都告诉用户；同名文件不会被覆盖（改用带时间戳的名字）。

## 主路线（默认）：有浏览器能力的 agent 上传 ZIP

1. 用浏览器打开 `https://ikkimikka.net/stompgame/?character=custom`（有头模式，保持窗口）。
2. 等待运行时注入的 `#upload` 出现（该 input 由 CUSTOM UPLOAD 面板动态写入，不在初始 HTML 里）。
3. 把本地 `custom.zip` 设置到 `#upload`：
   - Playwright：`page.set_input_files("#upload", "/abs/path/custom.zip")`
   - 参考实现：`python scripts/import_game.py`（`--image` 默认就是 `custom.zip`）
   - 其他浏览器工具：等价于给 `input[type=file]` 选择文件；拖放亦可。
4. 等待约 2–3 秒。上传会解析 ZIP 根目录的 `settings.json`，触发
   `textures.set("giant", ...)`、`custom_loaded = true`、`cancelAnimationFrame` 与
   `done_loading()` 重启游戏；此时爪与右上头像 HUD 才恢复显示。
5. 点击画布 `#outcanvas` 任意位置，进入 `CLICK TO BEGIN` → 开始游戏。
6. 保持浏览器窗口打开，把游戏交给用户。

`scripts/import_game.py` 只是参考实现（需 `requirements-browser.txt`）：默认在真实终端里
`input()` 等待回车以保持窗口；agent/CI 的非交互环境 stdin 为 EOF，窗口会随进程退出而关闭
（脚本会打印 NOTE 提示）。**agent 自带浏览器工具时优先用自带工具**，要立即关闭可传 `--no-wait`。

## 备选：用户自己上传（桌面二选一）

桌面同时有 `custom.png` 与 `custom.zip`，用户打开上传页后拖任意一份进上传框即可：
选 PNG 最省事，选 ZIP 会额外应用角色名/描述/评级/贴纸。**两份是同一张图，不要重新生成。**
agent 没有浏览器能力、或用户只想自己上传时走这条路。
用户明确指定了保存位置时脚本加 `--no-desktop`，两个文件都按指定位置输出、不产生桌面副本。

## 上传后的游戏行为（必须知道）

- **上传 ZIP（默认）**：`settings.json` 生效，`giant.name` 为设定名字，`giant.description`、
  `congrats`、`grades`（评级）、`stickers` 按模板/自定义值加载；结算页会显示评级。
- **上传 PNG**：游戏用文件名去 `.png` 当名字（自动命名后会带时间戳/角色名，故**角色名以 ZIP 内 `settings.json` 为准**，优先上传 ZIP），
  `giant.description = ""`，`giant.grades = false`（评级关闭，结算横幅只画单层、无评级抖动残影）；
  **贴纸保持游戏默认**（只有贴纸编辑器模式 `?stickers=true` 才清空）。反之默认 ZIP 模板的
  `"stickers": []` 是整体替换，会清空默认贴纸——这是两种上传方式的观感差异之一。
- 两种情况都只替换 `giant` 纹理；小人、背景、音效仍是默认 `city.png` 与站点资源；
  **所有坐标仍按 `references/layout.md`**。

### 验收清单（导入后逐项确认）

- [ ] 屏幕上有前爪与远景后爪，移动鼠标时前爪跟随
- [ ] 右上角 128×128 头像框内是 OC 的脸，不是白块/错位
- [ ] 抬爪、落下、加压时爪的姿态连续，无突然换脚/换视角
- [ ] 地面有爪影，不是白色方块
- [ ] 结算画面顶部横幅是自定义图
- [ ] **上传 ZIP 时**开场名字条显示设定角色名，结算页出现评级
- [ ] 无白底方块覆盖游戏画面（去背失败的最典型症状）

## 进阶：自定义 settings.json

复制 `assets/settings.template.json` 改好后用 `--settings my.json` 传给 `build_sheet.py`，
脚本会重新打包并校验。**ZIP 内 `settings.json` 必须在根**；任何带 `url` 的属性都能写
ZIP 内相对路径（加载时先在包内找，再回退站点 URL），所以自定义背景图/音效可直接放进包里。

游戏 `apply_settings()` 只认 11 个顶层字段，分两种语义：

| 语义 | 字段 | 常用可设内容 |
|---|---|---|
| **浅合并**（不写即用游戏默认） | `giant` | `name`、`description`（开场多行介绍）、`congrats`、`grades` |
| | `images` | `giant`（脚本自动写包内图片名）、`env`（背景图） |
| | `set` | `tiny_name*`、`bg_color`、`day_night_cycle`、`phrase_changes`、`closed_walls`、`starter_bugs`、`show_*` HUD 开关、`ambience_url` |
| | `bug` | 小人动画/物理、`fits` 替代小人；血腥效果的贴图都在这里（`sticker_*_spr` / `stain_spr` / `drop_*_spr` / `strand_spr`），详见下方「关闭血腥效果」 |
| | `paw` | 爪手感、`steamroller`、`wetness`、体力参数 |
| | `ego` | 开关、增减倍率、`step` |
| | `stain` | 地面血渍数量：`buckets`、`buckets_max` |
| **整体替换**（写了就全量覆盖） | `sound_urls` | `[URL, tag]` 列表；**必须列全想要的音效**，省略该键才用默认 |
| | `stickers` | 61 条爪上贴纸坐标；**切勿设 `[]`——空数组会让游戏崩溃**（见下方「关闭血腥效果」） |
| | `demographics` | 小人分布权重 |
| | `ego_tiers` | 6 档 ego 阈值 |

### 关闭血腥效果（贴纸 / 拉丝 / 血渍 / 血滴）

游戏画面里抬脚时的黑色残留物**不是画在 `custom.png` 里的**，而是游戏运行时叠加的四套独立效果。
它们与生成图和 `validate.py` 无关，全部由 `settings.json` 控制（源码依据：官方游戏 `index.html`
的 `draw_stickers` / `draw_strand` / `draw_stains` / `draw_droplets`）：

| 效果 | 来源字段（在 `bug` 段，浅合并） | 关闭方法 |
|---|---|---|
| 脚上/脚底的残留小人 | `sticker_high_spr` / `sticker_low_spr` | 指向全透明贴图（下方详解） |
| 抬脚拉出的细丝 | `strand_spr` | 设 `null`（源码 `draw_strand()` 有 `if(!spr) return`） |
| 地面血渍 | `stain_spr`（或 `stain.buckets_max:0` 从源头不生成） | 指向全透明贴图 / 设上限 0 |
| 飞溅血滴 | `drop_spr` / `drop_hit_spr`（或 `bug.drop_on:false` 从源头不生成） | 指向全透明贴图 / 设 `false` |

**彻底关闭（视觉全干净）的推荐配置**——复制 `assets/settings.template.json` 加上 `bug` 段：

```json
{
  "giant": { "name": "MY OC" },
  "images": { "giant": "custom.png" },
  "bug": {
    "sticker_high_spr": ["env", 0, 896, 32, 32],
    "sticker_low_spr":  ["env", 0, 896, 32, 32],
    "stain_spr":        ["env", 0, 896, 32, 16],
    "drop_spr":         ["env", 0, 896, 16, 16],
    "drop_hit_spr":     ["env", 0, 896, 16, 16],
    "strand_spr": null
  }
}
```

`["env", 0, 896, ...]` 是官方 env 图上一块**全透明区**（逐像素验证 alpha 全 0），把特效贴图
指向它即可渲染为"看不见"。合成时用 `--settings my.json` 传给 `build_sheet.py` 重新打包。

**三个必须避开的坑**（都是实测踩出来的）：

1. **千万别设 `"stickers": []`**。空数组会让 `init_stickers()` 提前 return，`sticker_planes` 未
   初始化；踩到 sticky 小人时 `get_sticker()` 读 `sticker_planes[i].max` 得到 `undefined`，直接
   抛 `Uncaught TypeError: Cannot read properties of undefined (reading 'max')`，游戏卡死。
   正确做法是**保留贴纸数组**（用默认 61 条），只把贴纸贴图改成透明。
2. **透明贴图必须覆盖该精灵的所有帧**。`sprite()` 用 `s[0]`（贴纸索引 0~9）作水平帧偏移
   `fx*uw`；若只给一格透明，第 1~9 帧会错位采样到相邻的有内容区域，脚上出现圆圈/星星/方块等
   杂图。env 图 `(0,896)` 起是一整条 320×32（=10 帧 × 32px）全透明横条，正好覆盖贴纸的全部帧；
   血渍 3 帧、血滴 ≤6 帧也落在这条透明区内。`strand_spr` 是垂直帧（`s[5]=true`），无法用同一技巧，
   所以用 `null` 直接关闭。
3. **这只是游戏侧效果**，与生成提示词里"污渍随压扁只增不减"是两回事：那是画在贴地帧爪格上的
   静态污渍（脚背朝下时可见），抬起帧 `front_0` 按规范干净无污渍。本节只管游戏运行时叠加的效果。

**只想减弱而非全关**：调小 `stain.buckets_max`（默认 12）、把 `bug.sticky_rand`（默认 0.5）
调低可减少贴纸/拉丝产生量、把 `bug.drop_on` 设 `false` 关血滴、调 `stain.buckets`（默认 32）。
若只想让"抬起最高帧"不显示贴纸而贴地帧保留，设 `paw.show_stickers_on_upper_state: false`
（已是默认）；注意 `paw_state==1`（下落中）仍会画贴纸，这一点没有 settings 开关，只能用透明贴图。

评级 `grades` 每条是 `[stat tag, 操作符, 数值, hint]`（可用 stat 见官方
`generic.zip/stats.txt`，操作符为 `< > <= >= = !=` 六种）；`grades: null` 关闭评级并直接显示
`congrats`；默认 5 条对应 6 个 rank，超过需重定义 `set.grade_spr`；条件按难度**从难到易**排序，
结算显示最后一个未满足条件的 hint。名字/描述/台词由 canvas 的 `VT323` 等宽像素字体绘制，
**建议短英文**：中文会字体回退，且宽度按 6px/字符估算容易溢出。

### 其它常用可配置项（安全）

除血腥效果外，游戏默认配置里这些字段可调（浅合并，只写要改的键）。完整字段以官方游戏
`index.html` 的 `const set/paw/ego/bug` 为准；改前确认不与 26 格坐标契约冲突。

- **HUD 开关（`set`，布尔）**：`show_pressure` / `show_time` / `show_kills` / `show_leaves`
  （默认均 true）、`small_score`（false）、`day_night_cycle`（true）、`foreground_shadow`（false）。
- **画面/文案（`set`）**：`bg_color`（默认 `#dae5d6`）、`tiny_name` / `tiny_name_plural` /
  `floor_name` / `special_name`（小人称呼）、`phrase_changes`（文案替换字典）、`seconds_in_day`（600）。
- **玩法数值（`set`）**：`starter_bugs`（100）、`spawn_rng` / `spawn_ego_base`（0.08）、
  `closed_walls`（null）、`combo_duration`（1.5）、`floor_pos` / `floor_depth`（12 / 8）。
- **爪子手感（`paw`）**：`strength`、`speed`、`friction`、`steamroller`、`wetness`，
  以及体力系统 `stam_on` / `stam_*`。⚠️ `width` / `stomp_masks` / `front_spr` 是坐标契约，**勿改**。
- **ego（`ego`）**：`on` / `numbers_on`（开关）、`gain_mul` / `loss_mul`、`step`（1000）、
  `passive_loss`、`phase_boost`。⚠️ `levels` 勿改（表情帧数绑定）。
- **整体替换字段**：`sound_urls`（必须列全想要的音效，省略才用默认）、`demographics`（小人称谓权重）、
  `ego_tiers`（6 档阈值）。`stickers` 切勿设 `[]`（见上方血腥效果章节）。

**不要改的字段**：任何 `*_spr` 坐标（`front_spr` / `normal_spr` / `end_spr` / `grade_spr` 等）、
`ego.levels`、`paw.width`、`paw.stomp_masks`、`ego_tiers` 的长度——它们与 1024×1024 的
26 格切片契约绑定，改了会让整套图错位或表情帧数不匹配。脚本对这类字段、`grades` 结构、
未知顶层 key、`sound_urls` 全量替换都会打印 WARN，交付前逐条确认。

## 备选路线 B：免上传直达链接（可选，非默认）

- `?giant=<图片URL>`：只换图，`custom=false`，打开即可玩。
- `?json=<URL 编码的 JSON 或 base64>`：可同时设置 `images.giant`、`giant.name/description/grades` 等。
- `?extra=<settings.json 的 URL>`：加载完整配置。

限制与坑：

- **不要**在直达链接里带 `character=custom`：该模式会隐藏爪与头像且跳过开场，等于不能玩。
- 远程图片服务器必须允许跨域（实测 `raw.githubusercontent.com` 返回 `Access-Control-Allow-Origin: *`，
  站点 CSP 也允许跨源 fetch），但**国内网络能否访问该托管源不可控**，所以默认仍用本地上传。
- 直达链接只换 `giant` 纹理，不换 ZIP 里的音效/背景/贴纸等资源。
- 不要把图片塞进 `data:` URL：体积过大，URL 长度不可靠。

## 故障排查

| 症状 | 原因 | 处理 |
|---|---|---|
| 打开页面看不到爪和头像 | 用了 `?character=custom` 但未上传 | 完成上传后再看，或改用 `?giant=` 直达链接 |
| 上传 ZIP 后名字/评级没生效 | `settings.json` 不在 ZIP 根，或 `images.giant` 指向了别的文件名 | 用 `build_sheet.py` 重新打包（脚本自动处理），或 `python -m zipfile -l custom.zip` 检查 |
| 白色方块盖住画面 | 生成图未去背 | 保持默认 `--bg auto` 重新合成（必要时显式 `--bg white`）；`validate.py` 的 `plate:*` 会判 FAIL |
| 头像框里是错位的图 | 表情格坐标/尺寸不对 | 核对 `layout.md`，重新 `build_sheet.py` |
| 爪影消失 / 变成实色块 | 装饰区被 AI 重画 | `validate.py` 会 FAIL；从官方底板重取装饰区 |
| 上传后游戏没反应 | 文件类型不是 `.png`/`.zip`，或 input 未等到 | 确认扩展名与 `wait_for_selector("#upload")` |
| 脚还悬在空中，小人却已被踩死 | 爪格脚底离格子底边留了透明空隙（游戏按格底边对齐 `paw_y`，不看图片内容） | 重跑 `build_sheet.py`：爪格会自动裁剪透明边并底对齐；`validate.py` 的 `ground:*` 会拦截 >6px 的留白 |
| ZIP 上传后没声音 | `sound_urls` 是整体替换，只写了部分标签 | 补全想要的标签，或整个删掉该键使用默认音效 |
| 爪上看不到默认残留小人 | skill 模板默认 `"stickers": []`（默认贴纸被清空） | 想保留官方贴纸就加 `--keep-default-stickers` 重新打包；⚠️ 但在游戏侧自定义时切勿写 `"stickers": []`（会崩，见「关闭血腥效果」） |
| 抬脚/地面出现黑色污渍/拉丝/血滴，想关掉 | 游戏运行时叠加的 stickers/strand/stain/drop 效果（不是画在角色图里） | 按上方「关闭血腥效果」用透明贴图 + `strand_spr:null`；切勿只设 `stain.buckets_max:0`（那只关地面血渍，脚上残留小人和拉丝仍在） |
| 角色名/评级台词显示不全 | 文本用 `VT323` 等宽字体按 6px/字符排版 | 改用短英文，缩短 `name` / `description` / `congrats` / hint |
| `settings.json` 有 WARN | 改了坐标类字段或评级结构 | 按 `custom.report.json` 的 warnings 逐条修，详见上文「不要改的字段」 |
| 无法自动上传 | agent 无浏览器能力 | 把桌面两份路径告诉用户，让用户手动拖入 `?character=custom` 页面 |
